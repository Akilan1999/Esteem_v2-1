from django.contrib import messages
from django.contrib.sites import requests
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from Home.models import room, plugs, plug_electricity_consumption, energy_generation, energy_mode, battery, \
    power_transaction, power_generation, leaderboard, user_ranking
from django.contrib.auth.models import User
import requests
import datetime
import pytz


def get_api_results(request=None):
    try:
        results = requests.get("http://127.0.0.1:5000/api/alldevicesconsumption/").json()
    except requests.exceptions.ConnectionError:
        if request:
            messages.error(request, "API is offline")
        results = []

    return results


## To add leaderboard information
def leaderboard_info(stat, plug_id, user_id, request=None):
    if stat == True:
        leaderboard.objects.create(plug_no=plugs.objects.get(plug_name=plug_id),
                                   user_id=User.objects.get(username=str(user_id)))
    else:
        # Init UTC
        utc = pytz.UTC

        try:
            l = leaderboard.objects.get(plug_no=plugs.objects.get(plug_name=plug_id), end_time_stamp=None)
            l.end_time_stamp = datetime.datetime.now()
            l.save()
            # Get the total Kw used
            try:
                results = requests.get("http://127.0.0.1:5000/api/alldevicesconsumption/").json()
                Watt = 0
                for i in results:
                    if i["DeviceName"] == plug_id:
                        Watt = i["CurConsp"]
                        break
                # time diffrences
                diff = datetime.datetime.now() - l.start_time_stamp.replace(tzinfo=None)
                duration_in_s = diff.total_seconds()
                minutes = divmod(duration_in_s, 60)[0]  # Seconds in a minute = 60
                print(datetime.datetime.now())
                print(l.start_time_stamp.replace(tzinfo=None))
                seconds = duration_in_s - 14400

                Total_pow_used = (0.04 * seconds) / 60

                try:
                    u = user_ranking.objects.get(user_id=l.user_id)
                    u.total_KwH = float(u.total_KwH) + Total_pow_used
                    u.save()
                except user_ranking.DoesNotExist:
                    user_ranking.objects.create(user_id=l.user_id, total_KwH=Total_pow_used)

            except requests.exceptions.ConnectionError:
                if request:
                    messages.error(request, "Sample server api off")

        except leaderboard.DoesNotExist:
            if request:
                messages.error(request, "This device is turned on before this update")


def user_rankings():
    return_arr = []
    user = list(user_ranking.objects.all().order_by('total_KwH'))
    for i in range(len(user)):
        return_arr.append({"rank": (i + 1), "username": str(user[i].user_id.username), "Kw": str(user[i].total_KwH), "first": str(user[i].user_id.first_name), "last": str(user[i].user_id.last_name)
                           ,"active": str(user[i].user_id.is_active)})

    return return_arr


class BackgroundClass:

    @staticmethod
    def power_allot_func():
        api_list = requests.get("http://127.0.0.1:5000/api/alldevicesconsumption/").json()
        r = room.objects.all()
        l = []

        for i in r:
            room_number = room.objects.get(room_no=i.room_no)
            plug = plugs.objects.filter(room_no=room_number)
            sum = 0
            for j in plug:

                for k in api_list:
                    if k['DeviceName'] == j.plug_name:
                        sum += k['CurConsp']
            l.append({'room_name': i.room_name, 'CurConsp': sum})

        current_power = 0
        for i in l:
            current_power += i['CurConsp']

        # battery wire capacity
        battery_wire_capacity = 0.45
        energy_modes = energy_mode.objects.all()

        # list of all energy devices
        energy_devices = requests.get("http://127.0.0.1:12345/api").json()
        energy_taken = current_power

        # ----------------------------- Back up mode -----------------------------------

        if energy_modes[0].mode_id == "e1":
            for j in energy_devices:
                try:
                    e_name = energy_generation.objects.get(name=j["SourceName"])
                except energy_generation.DoesNotExist:
                    # If the devce does exist add it to the databases
                    energy_generation.objects.create(name=j["SourceName"])
                    e_name = energy_generation.objects.get(name=j["SourceName"])

                if j["type"] == "Battery":
                    if j["BatteryPercentage"] != 100:
                        power_transaction.objects.create(e_id=e_name, transfer=-abs(battery_wire_capacity))
                        # Battery Pulled from energy sources
                        requests.get(
                            "http://127.0.0.1:12345/api/batterycharge/" + str(float(battery_wire_capacity))).json()
                        energy_taken += battery_wire_capacity

                if j["type"] == "EnergyGenerator":
                    if j['CurrentGenerated'] <= energy_taken:
                        power_transaction.objects.create(e_id=e_name, transfer=j['CurrentGenerated'])
                        requests.get("http://127.0.0.1:12345/api/givepower/" + j["SourceName"] + "/" + str(
                            float(j['CurrentGenerated']))).json()
                        energy_taken -= j['CurrentGenerated']
                    else:
                        power_transaction.objects.create(e_id=e_name, transfer=energy_taken)
                        requests.get("http://127.0.0.1:12345/api/givepower/" + j["SourceName"] + "/" + str(
                            float(energy_taken))).json()
                        energy_taken = 0
                if j["type"] == "Grid":
                    print(j["PowerCut"])
                    if energy_taken != 0 and j["PowerCut"] == False and j["CurrentSupplied"] >= energy_taken:
                        power_transaction.objects.create(e_id=e_name, transfer=energy_taken)
                        requests.get("http://127.0.0.1:12345/api/givepower/" + j["SourceName"] + "/" + str(
                            float(energy_taken))).json()
                        energy_taken = 0

                    elif j["PowerCut"]:
                        for k in energy_devices:
                            if k["type"] == "EnergyGenerator":
                                e_name_level_1 = energy_generation.objects.get(name=k["SourceName"])

                                if k['CurrentGenerated'] <= energy_taken:
                                    power_transaction.objects.create(e_id=e_name_level_1,
                                                                     transfer=k['CurrentGenerated'])
                                    requests.get("http://127.0.0.1:12345/api/givepower/" + k["SourceName"] + "/" + str(
                                        float(k['CurrentGenerated']))).json()
                                    energy_taken -= k['CurrentGenerated']
                                else:
                                    power_transaction.objects.create(e_id=e_name, transfer=energy_taken)
                                    requests.get("http://127.0.0.1:12345/api/givepower/" + j["SourceName"] + "/" + str(
                                        float(energy_taken))).json()
                                    energy_taken = 0
                            elif k["type"] == "Battery":

                                if k["RemainingCapacity"] <= battery_wire_capacity and k[
                                    "RemainingCapacity"] <= energy_taken:
                                    power_transaction.objects.create(e_id=e_name_level_1,
                                                                     transfer=battery_wire_capacity)
                                    requests.get("http://127.0.0.1:12345/api/batterydischarge/" + str(
                                        float(battery_wire_capacity))).json()
                                    energy_taken -= battery_wire_capacity

                                elif k["RemainingCapacity"] <= energy_taken:
                                    power_transaction.objects.create(e_id=e_name_level_1,
                                                                     transfer=k["RemainingCapacity"])
                                    requests.get("http://127.0.0.1:12345/api/batterydischarge/" + str(
                                        float(k["RemainingCapacity"]))).json()
                                    energy_taken -= k["RemainingCapacity"]

                                elif k["RemainingCapacity"] <= battery_wire_capacity and k[
                                    "RemainingCapacity"] > energy_taken:
                                    power_transaction.objects.create(e_id=e_name_level_1, transfer=energy_taken)
                                    requests.get("http://127.0.0.1:12345/api/batterydischarge/" + str(
                                        float(energy_taken))).json()
                                    energy_taken -= energy_taken

        ## ----------------------------- Self Powered mode -----------------------------------

        elif energy_modes[0].mode_id == "e2":

            # Running for all renewables
            for j in energy_devices:
                try:
                    e_name = energy_generation.objects.get(name=j["SourceName"])
                except energy_generation.DoesNotExist:
                    # If the devce does exist add it to the databases
                    energy_generation.objects.create(name=j["SourceName"])
                    e_name = energy_generation.objects.get(name=j["SourceName"])

                if j["type"] == "EnergyGenerator":
                    if j['CurrentGenerated'] <= energy_taken:
                        power_transaction.objects.create(e_id=e_name, transfer=j['CurrentGenerated'])
                        requests.get("http://127.0.0.1:12345/api/givepower/" + j["SourceName"] + "/" + str(
                            float(j['CurrentGenerated']))).json()
                        energy_taken -= j['CurrentGenerated']
                    else:
                        power_transaction.objects.create(e_id=e_name, transfer=energy_taken)
                        requests.get("http://127.0.0.1:12345/api/givepower/" + j["SourceName"] + "/" + str(
                            float(energy_taken))).json()
                        energy_taken = 0

            # Running for all battery Set Precentage to not pull from 30
            for j in energy_devices:
                if j["type"] == "Battery":
                    if j["BatteryPercentage"] > 30 and j[
                        'RemainingCapacity'] >= energy_taken and energy_taken >= battery_wire_capacity:
                        power_transaction.objects.create(e_id=energy_generation.objects.get(name=j["SourceName"]),
                                                         transfer=battery_wire_capacity)
                        # Battery Pulled from energy sources
                        requests.get(
                            "http://127.0.0.1:12345/api/batterydischarge/" + str(float(battery_wire_capacity))).json()
                        energy_taken -= battery_wire_capacity
                        print(energy_taken)
                    elif j["BatteryPercentage"] > 30 and j[
                        'RemainingCapacity'] >= energy_taken and energy_taken <= battery_wire_capacity:
                        power_transaction.objects.create(e_id=energy_generation.objects.get(name=j["SourceName"]),
                                                         transfer=energy_taken)
                        # Battery Pulled from energy sources
                        requests.get("http://127.0.0.1:12345/api/batterydischarge/" + str(float(energy_taken))).json()
                        energy_taken -= energy_taken
                        print(energy_taken)
                    else:
                        power_transaction.objects.create(e_id=energy_generation.objects.get(name=j["SourceName"]),
                                                         transfer=-abs(battery_wire_capacity))
                        # Battery Pulled from energy sources
                        requests.get("http://127.0.0.1:12345/api/batterycharge/" + str(float(energy_taken))).json()
                        energy_taken += energy_taken
                        print(energy_taken)

            for j in energy_devices:

                if j["type"] == "Grid":
                    if energy_taken != 0 and j["PowerCut"] == False and j["CurrentSupplied"] >= energy_taken:
                        power_transaction.objects.create(e_id=e_name, transfer=energy_taken)
                        requests.get("http://127.0.0.1:12345/api/givepower/" + j["SourceName"] + "/" + str(
                            float(energy_taken))).json()
                        energy_taken = 0

                    elif j["PowerCut"] == True:
                        print("here1")
                        for k in energy_devices:

                            if k["type"] == "EnergyGenerator":
                                e_name_level_1 = energy_generation.objects.get(name=k["SourceName"])

                                if k['CurrentGenerated'] <= energy_taken:
                                    power_transaction.objects.create(e_id=e_name_level_1,
                                                                     transfer=k['CurrentGenerated'])
                                    requests.get("http://127.0.0.1:12345/api/givepower/" + k["SourceName"] + "/" + str(
                                        float(k['CurrentGenerated']))).json()
                                    energy_taken -= k['CurrentGenerated']
                                else:
                                    power_transaction.objects.create(e_id=e_name, transfer=energy_taken)
                                    requests.get("http://127.0.0.1:12345/api/givepower/" + j["SourceName"] + "/" + str(
                                        float(energy_taken))).json()
                                    energy_taken = 0

                            elif k["type"] == "Battery":
                                if k["RemainingCapacity"] <= battery_wire_capacity and k[
                                    "RemainingCapacity"] <= energy_taken:
                                    power_transaction.objects.create(e_id=e_name_level_1,
                                                                     transfer=battery_wire_capacity)
                                    requests.get(
                                        "http://127.0.0.1:12345/api/batterydischarge/" + battery_wire_capacity).json()
                                    energy_taken -= battery_wire_capacity
                                elif k["RemainingCapacity"] <= energy_taken:
                                    power_transaction.objects.create(e_id=e_name_level_1,
                                                                     transfer=k["RemainingCapacity"])
                                    requests.get(
                                        "http://127.0.0.1:12345/api/batterydischarge/" + k["RemainingCapacity"]).json()
                                    energy_taken -= k["RemainingCapacity"]
                                elif k["RemainingCapacity"] <= battery_wire_capacity and k[
                                    "RemainingCapacity"] > energy_taken:
                                    power_transaction.objects.create(e_id=e_name_level_1, transfer=energy_taken)
                                    requests.get("http://127.0.0.1:12345/api/batterydischarge/" + energy_taken).json()
                                    energy_taken -= energy_taken

            ## ----------------------------- Only Grid mode -----------------------------------

        elif energy_modes[0].mode_id == "e3":

            for j in energy_devices:
                try:
                    e_name = energy_generation.objects.get(name=j["SourceName"])
                except energy_generation.DoesNotExist:
                    # If the devce does exist add it to the databases
                    energy_generation.objects.create(name=j["SourceName"])
                    e_name = energy_generation.objects.get(name=j["SourceName"])

                if j["type"] == "Grid":
                    if energy_taken != 0 and j["PowerCut"] == False and j["CurrentSupplied"] >= energy_taken:
                        power_transaction.objects.create(e_id=e_name, transfer=energy_taken)
                        requests.get("http://127.0.0.1:12345/api/givepower/" + j["SourceName"] + "/" + str(
                            float(energy_taken))).json()
                        energy_taken = 0

                    elif j["PowerCut"] == True:
                        print("here1")
                        for k in energy_devices:
                            if k["type"] == "EnergyGenerator":
                                e_name_level_1 = energy_generation.objects.get(name=k["SourceName"])

                                if k['CurrentGenerated'] <= energy_taken:
                                    power_transaction.objects.create(e_id=e_name_level_1,
                                                                     transfer=k['CurrentGenerated'])
                                    requests.get("http://127.0.0.1:12345/api/givepower/" + k["SourceName"] + "/" + str(
                                        float(k['CurrentGenerated']))).json()
                                    energy_taken -= k['CurrentGenerated']
                                else:
                                    power_transaction.objects.create(e_id=e_name, transfer=energy_taken)
                                    requests.get("http://127.0.0.1:12345/api/givepower/" + j["SourceName"] + "/" + str(
                                        float(energy_taken))).json()
                                    energy_taken = 0

                            elif k["type"] == "Battery":
                                if k["RemainingCapacity"] <= battery_wire_capacity and k[
                                    "RemainingCapacity"] <= energy_taken:
                                    power_transaction.objects.create(e_id=e_name_level_1,
                                                                     transfer=battery_wire_capacity)
                                    requests.get(
                                        "http://127.0.0.1:12345/api/batterydischarge/" + battery_wire_capacity).json()
                                    energy_taken -= battery_wire_capacity
                                elif k["RemainingCapacity"] <= energy_taken:
                                    power_transaction.objects.create(e_id=e_name_level_1,
                                                                     transfer=k["RemainingCapacity"])
                                    requests.get(
                                        "http://127.0.0.1:12345/api/batterydischarge/" + k["RemainingCapacity"]).json()
                                    energy_taken -= k["RemainingCapacity"]
                                elif k["RemainingCapacity"] <= battery_wire_capacity and k[
                                    "RemainingCapacity"] > energy_taken:
                                    power_transaction.objects.create(e_id=e_name_level_1, transfer=energy_taken)
                                    requests.get("http://127.0.0.1:12345/api/batterydischarge/" + energy_taken).json()
                                    energy_taken -= energy_taken

        ##-------------------------------------- Delete hourly data at the end of the day -----------------------------------------

        # ------------ First we need to to get sum of all energy devices ---------------

        now = datetime.datetime.now()
        time = now.time()
        day = now.day
        month = now.month
        year = now.year
        hour = time.hour
        minute = time.minute

        print(minute)

        if hour == 23 and minute == 59:

            energy = energy_generation.objects.all()

            for i in energy:
                transactions = power_transaction.objects.filter(e_id=i, timestamp__day=day, timestamp__month=month,
                                                                timestamp__year=year)
                sum = 0
                for k in transactions:
                    sum += k.transfer

                # Deletes all data of that plug
                power_transaction.objects.filter(e_id=i, timestamp__day=day, timestamp__month=month,
                                                 timestamp__year=year).delete()

                # Adds the total power back
                power_transaction.objects.create(e_id=i, transfer=sum)

                print("data deleted")

    @staticmethod
    def device_consumption():
        api_devices_list = get_api_results()
        for device in api_devices_list:

            if device['status'] == 'on':
                try:
                    plug_no = plugs.objects.get(plug_name=device['DeviceName'])
                    print("here")
                    plug_electricity_consumption.objects.create(plug_no=plug_no, Watt=device['ElecConsp'])
                except plugs.DoesNotExist:
                    plug_no = None

        now = datetime.datetime.now()
        time = now.time()
        day = now.day
        month = now.month
        year = now.year
        hour = time.hour
        minute = time.minute

        if hour == 23 and minute == 59:

            plug = plugs.objects.all()

            for i in plug:
                consumption = plug_electricity_consumption.objects.filter(plug_no=i, timestamp__day=day,
                                                                          timestamp__month=month, timestamp__year=year)
                sum = 0

                for j in consumption:
                    sum += j.Watt

                plug_electricity_consumption.objects.filter(plug_no=i, timestamp__day=day, timestamp__month=month,
                                                            timestamp__year=year).delete()

                plug_electricity_consumption.objects.create(plug_no=i, Watt=sum)


class HomePage(TemplateView):
    template_name = 'home/index.html'

    def get(self, request, *args, **kwargs):
        api_list = get_api_results(request)
        r = room.objects.all()
        l = []

        for i in r:
            room_number = room.objects.get(room_no=i.room_no)
            plug = plugs.objects.filter(room_no=room_number)
            sum = 0
            for j in plug:

                for k in api_list:
                    if k['DeviceName'] == j.plug_name:
                        sum += k['CurConsp']
            l.append({'room_name': i.room_name, 'CurConsp': sum})

        room_names, room_consumptions = [], []

        for i in range(len(l)):
            room_names.append(l[i]['room_name'])
            room_consumptions.append(l[i]['CurConsp'])

        room_names = str(room_names)

        for i in range(len(room_consumptions)):
            room_consumptions[i] = round(room_consumptions[i], 3)

        powerData = requests.get("http://127.0.0.1:12345/api").json()
        batteries, solarpanels, grids = [], [], []

        for i in range(len(powerData)):

            powerData[i]['SupplyingPower'] = int(powerData[i]['SupplyingPower'])
            powerData[i]['CurrentSupplied'] = round(powerData[i]['CurrentSupplied'], 2)
            if powerData[i]['type'] == 'Battery':
                powerData[i]['ChargingState'] = int(powerData[i]['ChargingState'])
                batteries.append(powerData[i])

            elif powerData[i]['type'] == 'EnergyGenerator':
                solarpanels.append(powerData[i])
                powerData[i]['ChargingState'] = int(powerData[i]['ChargingState'])

            elif powerData[i]['type'] == 'Grid':
                grids.append(powerData[i])
                powerData[i]['PowerCut'] = int(powerData[i]['PowerCut'])

            else:
                print("No power source connected")

        return render(request, self.template_name,
                      {"Room": room.objects.all(), "name_rooms": room_names, "consumption_rooms": room_consumptions,
                       "Battery": batteries, "Solarpanel": solarpanels, "Grid": grids,
                       "User_ranking": user_rankings()}, )

    def post(self, request, *args, **kwargs):
        if 'remove_room' in request.POST:
            room.objects.filter(room_no=request.POST.get('room_no')).delete()
        else:
            room.objects.create(room_name=request.POST.get('room_name'))

        return redirect('homepage')


class EnergyGeneration(TemplateView):
    template_name = 'home/energy.html'

    def get(self, request, *args, **kwargs):

        powerSources_data = requests.get('http://127.0.0.1:12345/api').json()

        sources, currentSupplied = [], []
        for s in powerSources_data:
            sources.append(s['SourceName'])
            currentSupplied.append(round(s['CurrentSupplied'], 2))

        # Not secure but working solution
        # EDIT: I have no idea what this is but you can use **kwargs to get url parameters
        type_data = request.GET.get('type_data')

        if type_data is not None:
            energy_mode.objects.all().delete()
            energy_mode.objects.create(mode_id=type_data)
        # Sending current mode active
        return render(request, self.template_name, {"Energy_mode": energy_mode.objects.all(),
                                                    "Room": room.objects.all(),
                                                    "Power_sources": sources,
                                                    "Current_supplied": currentSupplied})


class RoomPage(TemplateView):
    template_name = 'home/room.html'

    def get(self, request, *args, **kwargs):

        # Try and except for smart plugs in the room
        try:
            plugs_in_room = plugs.objects.filter(room_no=kwargs["room_no"]).order_by("plug_no")
        except plugs.DoesNotExist:
            plugs_in_room = []

        # Forces it to an array if their is only 1 result
        if not hasattr(plugs_in_room, '__iter__'):
            plugs_in_room = [plugs_in_room]

        consumption = []
        available_devices = []

        api_devices_list = get_api_results()

        for device in api_devices_list:
            # If the device exist in current room, pass on its reading to the graph in front end.
            if plugs.objects.filter(room_no=kwargs['room_no'], plug_name=device['DeviceName']).exists():
                consumption.append(device['CurConsp'])
            # If the device is not in the database (we use IP address as unique identifier),
            # that means it is a new device and we show it as a list in front end to be added.
            if not plugs.objects.filter(ip_address=device['ip_address']).exists():
                available_devices.append([device['DeviceName'], device['ip_address']])

        return render(request, self.template_name, {"Room": room.objects.all(),
                                                    "Room_in": room.objects.get(room_no=kwargs["room_no"]),
                                                    "Plugs": plugs_in_room, "Consumption": consumption,
                                                    "available_devices": available_devices},
                      )

    def post(self, request, *args, **kwargs):

        user = request.user

        if 'new_device' in request.POST:
            api_devices_list = get_api_results()
            # Using generator, get the item from the list that matches the IP provided from front-end.
            device_data = next(item for item in api_devices_list
                               if item["ip_address"] == request.POST[request.POST['new_device'] + '_ip_address'])
            plugs.objects.create(plug_name=device_data['DeviceName'],
                                 plug_model_name=device_data['DeviceModel'],
                                 ip_address=device_data['ip_address'],
                                 room_no=room.objects.get(room_no=kwargs['room_no']),
                                 # curr_consumption=device_data['CurConsp'],
                                 status=False if device_data['status'] == "off" else True)

        if 'change_status' in request.POST:
            values = request.POST['change_status'].split(',')

            requests.get("http://127.0.0.1:5000/api/changestatus/" + values[1])
            plug_obj = plugs.objects.get(ip_address=values[0], plug_name=values[1])

            if plug_obj.status:
                plug_obj.status = False
            else:
                plug_obj.status = True
            # plug_obj.status = True if plug_obj.status else False
            # Adding to the leaderboard
            leaderboard_info(plug_obj.status, values[1], request.user)
            plug_obj.save()

        if 'add_device' in request.POST:
            plugs.objects.create(plug_name=request.POST['plug_name'],
                                 plug_model_name=request.POST['plug_model_name'],
                                 ip_address=request.POST['ip_address'],
                                 room_no=room.objects.get(room_no=kwargs['room_no']))
        if 'remove_device' in request.POST:
            plugs.objects.filter(plug_no=request.POST.get('plug_no')).delete()

        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


# JSON for nessary data for hourly data
class Plugs(TemplateView):
    def get(self, request, *args, **kwargs):
        # Line graph for plugs hourly data
        plug_id = request.GET.get('plug_id')

        # We start with default hourly data
        if plug_id is not None:
            now = datetime.datetime.now()
            time = now.time()
            day = now.day
            month = now.month
            year = now.year
            hour = time.hour
            hourly_data = []
            plug = plugs.objects.get(plug_name=plug_id)

            # sum for every hour
            for i in range(hour + 1):
                sum = 0
                l = (list(plug_electricity_consumption.objects.filter(plug_no=plug, timestamp__day=day,
                                                                      timestamp__month=month, timestamp__year=year,
                                                                      timestamp__hour=i)))
                for j in l:
                    sum += j.Watt
                hourly_data.append({'hour': i, 'Watts': sum})
            return JsonResponse(hourly_data, safe=False)

        return JsonResponse("{'error':'This plug does not exist in the database'}", safe=False)


# Sum Data for every Room for now every hour
class Rooms(TemplateView):
    def get(self, request, *args, **kwargs):

        room_id = request.GET.get('room_id')

        now = datetime.datetime.now()
        time = now.time()
        day = now.day
        month = now.month
        year = now.year
        hour = time.hour
        # Storing response data
        hourly_data = []
        # Storing all data for the plug
        hourly_data_tot_plug = []

        try:
            plugs_in_room = plugs.objects.filter(room_no=room_id).order_by("plug_no")
        except plugs.DoesNotExist:
            plugs_in_room = []

            for i in range(hour):
                hourly_data.append({'hour': i, 'Watts': 0})
            return JsonResponse(hourly_data, safe=False)

        # Forces it to an array if their is only 1 result
        if not hasattr(plugs_in_room, '__iter__'):
            plugs_in_room = [plugs_in_room]

        # Not a effective way but there is duplicate code but for the current time it's a working solution
        # sum for every hour
        for i in plugs_in_room:
            plug_no = plugs.objects.get(plug_name=i.plug_name)
            hourly_data_plug = []

            for k in range(hour):
                sum = 0
                l = (list(plug_electricity_consumption.objects.filter(plug_no=plug_no, timestamp__day=day,
                                                                      timestamp__month=month, timestamp__year=year,
                                                                      timestamp__hour=k)))
                for j in l:
                    sum += j.Watt
                hourly_data_plug.append({'hour': k, 'Watts': sum})
            hourly_data_tot_plug.append(hourly_data_plug)

        for i in range(hour):
            sum = 0
            for j in hourly_data_tot_plug:
                sum += j[i]['Watts']
            hourly_data.append({'hour': i, 'Watts': sum})

        return JsonResponse(hourly_data, safe=False)


# NOTICE : There is a lot of redundancy as doing inner API calls
# within django API server seems to be having some major issues
class total_consumption(TemplateView):
    def get(self, request, *args, **kwargs):

        now = datetime.datetime.now()
        time = now.time()
        day = now.day
        month = now.month
        year = now.year
        hour = time.hour

        # Storing response data
        hourly_data = []

        # Storing all data for rooms and plugs
        hourly_data_tot_room = []

        rooms = room.objects.all()

        for r in rooms:

            # Storing all data for the plug
            hourly_data_tot_plug = []
            hourly_data_room = []

            room_obj = room.objects.filter(room_no=r.room_no)

            # Redundant code
            try:
                plugs_in_room = plugs.objects.filter(room_no=room_obj).order_by("plug_no")
            except plugs.DoesNotExist:
                plugs_in_room = []
                for i in range(hour):
                    hourly_data_room.append({'hour': i, 'Watts': 0})
                hourly_data_tot_plug.append(hourly_data_room)

            # Forces it to an array if their is only 1 result
            if not hasattr(plugs_in_room, '__iter__'):
                plugs_in_room = [plugs_in_room]


# Hourly power distribution
class EnergyDistribution(TemplateView):
    def get(self, request, *args, **kwargs):

        # Hourly data

        now = datetime.datetime.now()
        time = now.time()
        day = now.day
        month = now.month
        year = now.year
        hour = time.hour

        # Storing all data for all renewables , grid , battery
        # Ex: [[solarpanel1,[{'hour':1,'kWh':0.3}]]]
        hourly_data_tot = []

        energy_gen = energy_generation.objects.all()

        for i in energy_gen:
            # Dict for ex: {'hour':1,'kWh':0.3}
            hourly_data = []
            for j in range(hour):
                transactions = power_transaction.objects.filter(e_id=i, timestamp__day=day, timestamp__month=month,
                                                                timestamp__year=year, timestamp__hour=j)
                sum = 0
                for k in transactions:
                    sum += k.transfer
                hourly_data.append({'hour': j, 'Watts': sum})
            hourly_data_tot.append({'name': i.name, 'data': hourly_data})
        print(hourly_data_tot)

        return JsonResponse(hourly_data_tot, safe=False)


class RoomsWeekly(TemplateView):
    def get(self, request, *args, **kwargs):
        now = datetime.datetime.now()
        time = now.time()
        day = now.day
        month = now.month
        year = now.year
        hour = time.hour

        # Return_data  [{previous_week:[{date:'',weekday:'',KwH:''}]}]
        return_data = []

        current_date = datetime.date(year, month, day)

        # Previous week range
        start_date = current_date + datetime.timedelta(-current_date.weekday(), weeks=-1)
        end_date = current_date + datetime.timedelta(-current_date.weekday() - 1)
        days_month = current_date.replace(day=28) + datetime.timedelta(days=4)

        i = start_date.day
        m = start_date.month
        y = year

        e_date = end_date.day
        e_month = end_date.month

        return_data.append({'previous_week': []})

        print(end_date.day)
        print(i)

        while i != e_date + 1:

            week_day = datetime.datetime(y, m, i).strftime('%A')

            l = (list(
                plug_electricity_consumption.objects.filter(timestamp__day=i, timestamp__month=m, timestamp__year=y)))

            sum = 0

            for j in l:
                sum += j.Watt

            data = {'date': str(i) + "/" + str(m) + "/" + str(y), 'week_day': week_day, 'Watt': sum}

            return_data[0]['previous_week'].append(data)

            if days_month == i:
                i = 1
                if m == 12:
                    m = 1
                    y += 1
                else:
                    m += 1
            else:
                i += 1

        days = [{"weekday": "Monday", "value": 0}, {"weekday": "Tuesday", "value": 1},
                {"weekday": "Wednesday", "value": 2}, {"weekday": "Thursday", "value": 3},
                {"weekday": "Friday", "value": 4}, {"weekday": "Saturday", "value": 5},
                {"weekday": "Sunday", "value": 6}]

        prev_month = datetime.date(year, (month - 1), day)
        days_month = prev_month.replace(day=28) + datetime.timedelta(days=4)
        m = month

        current_weekday = current_date.strftime('%A')

        value = 0

        for i in days:
            if i["weekday"] == current_weekday:
                value = i["value"]

        i = int(day)
        print(value)

        start_week = i - value
        print(i)
        print(start_week)
        return_data.append({'current_week': []})

        while i >= start_week:
            print("here")

            l = (list(
                plug_electricity_consumption.objects.filter(timestamp__day=i, timestamp__month=m, timestamp__year=y)))
            sum = 0

            for j in l:
                sum += j.Watt

            data = {'date': str(i) + "/" + str(m) + "/" + str(y), 'week_day': current_weekday, 'Watt': sum}

            return_data[1]['current_week'].insert(0, data)

            i -= 1

            if i == 0:
                i = days_month.day
                if m == 0:
                    m = 12
                    y -= 1
                else:
                    m -= 1

        return JsonResponse(return_data, safe=False)

# Code for leaderboard to turn on or off a device
