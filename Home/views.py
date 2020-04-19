from django.contrib import messages
from django.contrib.sites import requests
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from Home.models import room, plugs, plug_electricity_consumption, energy_generation, energy_mode, battery, \
    power_transaction, power_generation
import requests
import datetime


def get_api_results(request=None):
    try:
        results = requests.get("http://127.0.0.1:5000/api/alldevicesconsumption/").json()
    except requests.exceptions.ConnectionError:
        if request:
            messages.error(request, "API is offline")
        results = []

    return results


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
                        power_transaction.objects.create(e_id=e_name, transfer=battery_wire_capacity)
                        # Battery Pulled from energy sources
                        requests.get("http://127.0.0.1:12345/api/batterycharge/" + battery_wire_capacity).json()
                        energy_taken += battery_wire_capacity

                if j["type"] == "EnergyGenerator":
                    if j['CurrentGenerated'] <= energy_taken:
                        power_transaction.objects.create(e_id=e_name, transfer=-abs(j['CurrentGenerated']))
                        energy_taken -= j['CurrentGenerated']
                    else:
                        power_transaction.objects.create(e_id=e_name, transfer=-abs(j['CurrentGenerated']))
                        energy_taken = 0
                if j["type"] == "Grid":
                    print(j["PowerCut"])
                    if energy_taken != 0 and j["PowerCut"] is False and j["CurrentSupplied"] >= energy_taken:
                        power_transaction.objects.create(e_id=e_name, transfer=-abs(energy_taken))
                        energy_taken = 0

                    elif j["PowerCut"]:
                        for k in energy_devices:
                            if k["type"] == "EnergyGenerator":
                                e_name_level_1 = energy_generation.objects.get(name=k["SourceName"])

                                if k['CurrentGenerated'] <= energy_taken:
                                    power_transaction.objects.create(e_id=e_name_level_1,
                                                                     transfer=-abs(k['CurrentGenerated']))
                                    energy_taken -= k['CurrentGenerated']
                                else:
                                    power_transaction.objects.create(e_id=e_name_level_1,
                                                                     transfer=-abs(k['CurrentGenerated']))
                                    energy_taken = 0
                            elif k["type"] == "Battery":
                                if k["RemainingCapacity"] <= battery_wire_capacity and k["RemainingCapacity"] <= energy_taken:
                                    power_transaction.objects.create(e_id=e_name_level_1,
                                                                     transfer=-abs(battery_wire_capacity))
                                    requests.get(
                                        "http://127.0.0.1:12345/api/batterydischarge/" + battery_wire_capacity).json()
                                    energy_taken -= battery_wire_capacity
                                elif k["RemainingCapacity"] <= energy_taken:
                                    power_transaction.objects.create(e_id=e_name_level_1,
                                                                     transfer=-abs(k["RemainingCapacity"]))
                                    requests.get(
                                        "http://127.0.0.1:12345/api/batterydischarge/" + k["RemainingCapacity"]).json()
                                    energy_taken -= k["RemainingCapacity"]
                                elif k["RemainingCapacity"] <= battery_wire_capacity and k[
                                    "RemainingCapacity"] > energy_taken:
                                    power_transaction.objects.create(e_id=e_name_level_1, transfer=-abs(energy_taken))
                                    requests.get("http://127.0.0.1:12345/api/batterydischarge/" + energy_taken).json()
                                    energy_taken -= energy_taken

        ## ----------------------------- Self Powered mode -----------------------------------

        elif i[0].mode_id == "e2":

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
                        power_transaction.objects.create(e_id=e_name, transfer=-abs(j['CurrentGenerated']))
                        energy_taken -= j['CurrentGenerated']
                    else:
                        power_transaction.objects.create(e_id=e_name, transfer=-abs(j['CurrentGenerated']))
                        energy_taken = 0

            # Running for all battery Set Precentage to not pull from 30
            for j in energy_devices:
                if j["type"] == "Battery":
                    if j["BatteryPercentage"] > 30 and j[
                        'RemainingCapacity'] >= energy_taken and energy_taken >= battery_wire_capacity:
                        power_transaction.objects.create(e_id=e_name, transfer=-abs(battery_wire_capacity))
                        # Battery Pulled from energy sources
                        requests.get("http://127.0.0.1:12345/api/batterydischarge/" + battery_wire_capacity).json()
                        energy_taken -= battery_wire_capacity
                        print(energy_taken)
                    elif j["BatteryPercentage"] > 30 and j[
                        'RemainingCapacity'] >= energy_taken and energy_taken <= battery_wire_capacity:
                        power_transaction.objects.create(e_id=e_name, transfer=-abs(energy_taken))
                        # Battery Pulled from energy sources
                        requests.get("http://127.0.0.1:12345/api/batterydischarge/" + energy_taken).json()
                        energy_taken -= energy_taken
                        print(energy_taken)
                    else:
                        power_transaction.objects.create(e_id=e_name, transfer=battery_wire_capacity)
                        # Battery Pulled from energy sources
                        requests.get("http://127.0.0.1:12345/api/batterycharge/" + energy_taken).json()
                        energy_taken += energy_taken
                        print(energy_taken)

            for j in energy_devices:

                if j["type"] == "Grid":
                    if energy_taken != 0 and j["PowerCut"] == False and j["CurrentSupplied"] >= energy_taken:
                        power_transaction.objects.create(e_id=e_name, transfer=-abs(energy_taken))
                        energy_taken = 0

                    elif j["PowerCut"] == True:
                        print("here1")
                        for k in energy_devices:

                            if k["type"] == "EnergyGenerator":
                                e_name_level_1 = energy_generation.objects.get(name=k["SourceName"])

                                if k['CurrentGenerated'] <= energy_taken:
                                    power_transaction.objects.create(e_id=e_name_level_1,
                                                                     transfer=-abs(k['CurrentGenerated']))
                                    energy_taken -= k['CurrentGenerated']
                                else:
                                    power_transaction.objects.create(e_id=e_name_level_1,
                                                                     transfer=-abs(k['CurrentGenerated']))
                                    energy_taken = 0

                            elif k["type"] == "Battery":
                                if k["RemainingCapacity"] <= battery_wire_capacity and k[
                                    "RemainingCapacity"] <= energy_taken:
                                    power_transaction.objects.create(e_id=e_name_level_1,
                                                                     transfer=-abs(battery_wire_capacity))
                                    requests.get(
                                        "http://127.0.0.1:12345/api/batterydischarge/" + battery_wire_capacity).json()
                                    energy_taken -= battery_wire_capacity
                                elif k["RemainingCapacity"] <= energy_taken:
                                    power_transaction.objects.create(e_id=e_name_level_1,
                                                                     transfer=-abs(k["RemainingCapacity"]))
                                    requests.get(
                                        "http://127.0.0.1:12345/api/batterydischarge/" + k["RemainingCapacity"]).json()
                                    energy_taken -= k["RemainingCapacity"]
                                elif k["RemainingCapacity"] <= battery_wire_capacity and k[
                                    "RemainingCapacity"] > energy_taken:
                                    power_transaction.objects.create(e_id=e_name_level_1, transfer=-abs(energy_taken))
                                    requests.get("http://127.0.0.1:12345/api/batterydischarge/" + energy_taken).json()
                                    energy_taken -= energy_taken

            ## ----------------------------- Only Grid mode -----------------------------------

        elif i[0].mode_id == "e3":

            for j in energy_devices:
                try:
                    e_name = energy_generation.objects.get(name=j["SourceName"])
                except energy_generation.DoesNotExist:
                    # If the devce does exist add it to the databases
                    energy_generation.objects.create(name=j["SourceName"])
                    e_name = energy_generation.objects.get(name=j["SourceName"])

                if j["type"] == "Grid":
                    if energy_taken != 0 and j["PowerCut"] == False and j["CurrentSupplied"] >= energy_taken:
                        power_transaction.objects.create(e_id=e_name, transfer=-abs(energy_taken))
                        energy_taken = 0

                    elif j["PowerCut"] == True:
                        print("here1")
                        for k in energy_devices:
                            if k["type"] == "EnergyGenerator":
                                e_name_level_1 = energy_generation.objects.get(name=k["SourceName"])

                                if k['CurrentGenerated'] <= energy_taken:
                                    power_transaction.objects.create(e_id=e_name_level_1,
                                                                     transfer=-abs(k['CurrentGenerated']))
                                    energy_taken -= k['CurrentGenerated']
                                else:
                                    power_transaction.objects.create(e_id=e_name_level_1,
                                                                     transfer=-abs(k['CurrentGenerated']))
                                    energy_taken = 0
                            elif k["type"] == "Battery":
                                if k["RemainingCapacity"] <= battery_wire_capacity and k[
                                    "RemainingCapacity"] <= energy_taken:
                                    power_transaction.objects.create(e_id=e_name_level_1,
                                                                     transfer=-abs(battery_wire_capacity))
                                    requests.get(
                                        "http://127.0.0.1:12345/api/batterydischarge/" + battery_wire_capacity).json()
                                    energy_taken -= battery_wire_capacity
                                elif k["RemainingCapacity"] <= energy_taken:
                                    power_transaction.objects.create(e_id=e_name_level_1,
                                                                     transfer=-abs(k["RemainingCapacity"]))
                                    requests.get(
                                        "http://127.0.0.1:12345/api/batterydischarge/" + k["RemainingCapacity"]).json()
                                    energy_taken -= k["RemainingCapacity"]
                                elif k["RemainingCapacity"] <= battery_wire_capacity and k[
                                    "RemainingCapacity"] > energy_taken:
                                    power_transaction.objects.create(e_id=e_name_level_1, transfer=-abs(energy_taken))
                                    requests.get("http://127.0.0.1:12345/api/batterydischarge/" + energy_taken).json()
                                    energy_taken -= energy_taken

    @staticmethod
    def device_consumption():
        api_devices_list = get_api_results()
        for device in api_devices_list:

            if device['status'] == 'on':
                try:
                    plug_no = plugs.objects.get(plug_name=device['DeviceName'])
                    plug_electricity_consumption.objects.create(plug_no=plug_no, Watt=device['ElecConsp'])
                except plugs.DoesNotExist:
                    plug_no = None


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

        return render(request, self.template_name,
                      {"Room": room.objects.all(), "name_rooms": room_names, "consumption_rooms": room_consumptions}, )

    def post(self, request, *args, **kwargs):
        if 'remove_room' in request.POST:
            room.objects.filter(room_no=request.POST.get('room_no')).delete()
        else:
            room.objects.create(room_name=request.POST.get('room_name'))

        return redirect('homepage')


class EnergyGeneration(TemplateView):
    template_name = 'home/energy.html'

    def get(self, request, *args, **kwargs):
        # Not secure but working solution
        # EDIT: I have no idea what this is but you can use **kwargs to get url parameters
        type_data = request.GET.get('type_data')

        if type_data is not None:
            energy_mode.objects.all().delete()
            energy_mode.objects.create(mode_id=type_data)
        # Sending current mode active
        return render(request, self.template_name, {"Energy_mode": energy_mode.objects.all(),
                                                    "Room": room.objects.all()})


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
            for i in range(hour):
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
