from django.contrib.sites import requests
from django.http import HttpResponseRedirect,JsonResponse
from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from Home.models import room, plugs, plug_electricity_consumption, energy_generation, energy_mode, battery, \
    power_transaction, power_generation
import requests
import datetime


class BackgroundClass:
    @staticmethod
    def test_func():
        print("HIIIIIIIIIIII")

    @staticmethod
    def power_allot_func():
        api_list = requests.get("http://127.0.0.1:5000/api/alldevicesconsumption/").json()        # print("rooms + " ,room.objects.)
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
            l.append({'room_name':i.room_name,'CurConsp':sum})

        sum = 0
        for i in l:
            sum += i['CurConsp']

        print(sum)

            #power_req += i[CurConsp]
        # print(power_req)
        # check power mode
        # Total power consumption by house
        # Do according transaction


    @staticmethod
    def device_consumption():
        api_devices_list = requests.get("http://127.0.0.1:5000/api/alldevicesconsumption/").json()
        for device in api_devices_list:
            print(device['status'])
            if device['status'] == 'on':
                try:
                    plug_no=plugs.objects.get(plug_name=device['DeviceName'])
                    plug_electricity_consumption.objects.create(plug_no=plug_no,Watt=device['ElecConsp'])
                except plugs.DoesNotExist:
                    plug_no = None



class HomePage(TemplateView):
    template_name = 'home/index.html'

    def get(self, request, *args, **kwargs):
        api_list = requests.get("http://127.0.0.1:5000/api/alldevicesconsumption/").json()        # print("rooms + " ,room.objects.)
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
            l.append({'room_name':i.room_name,'CurConsp':sum})
            #room_data[r[i].room_no] = 0
        room_names, room_consumptions = [],[]

        for i in range(len(l)):
            room_names.append(l[i]['room_name'])
            room_consumptions.append(l[i]['CurConsp'])

        room_names = str(room_names)
        print(room_names, room_consumptions)
        # return JsonResponse(l, safe= False)

        return render(request, self.template_name, {"Room": room.objects.all(), "name_rooms": room_names, "consumption_rooms": room_consumptions},)

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
        return render(request, self.template_name, {"Energy_mode": energy_mode.objects.all()})


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
        dev = []

        api_devices_list = requests.get("http://127.0.0.1:5000/api/alldevicesconsumption/").json()

        for device in api_devices_list:
            # If the device exist in current room, pass on its reading to the graph in front end.
            if plugs.objects.filter(room_no=kwargs['room_no'], plug_name=device['DeviceName']).exists():
                consumption.append(device['CurConsp'])
            # If the device is not in the database (we use IP address as unique identifier),
            # that means it is a new device and we show it as a list in front end to be added.
            if not plugs.objects.filter(ip_address=device['ip_address']).exists():
                available_devices.append([device['DeviceName'], device['ip_address']])

        print(dev)


        return render(request, self.template_name, {"Room": room.objects.all(),
                                                    "Room_in": room.objects.get(room_no=kwargs["room_no"]),
                                                    "Plugs": plugs_in_room, "Consumption": consumption,
                                                    "available_devices": available_devices},
                      )

    def post(self, request, *args, **kwargs):

        if 'new_device' in request.POST:
            api_devices_list = requests.get("http://127.0.0.1:5000/api/alldevicesconsumption/").json()
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
            print("Old values befor pressing button", values)
            requests.get("http://127.0.0.1:5000/api/changestatus/" + values[1])
            plug_obj = plugs.objects.get(ip_address=values[0], plug_name=values[1])
            print(plug_obj.status)

            if plug_obj.status:
                plug_obj.status = False
            else:
                plug_obj.status = True
            #plug_obj.status = True if plug_obj.status else False
            plug_obj.save()
            print("Button pressed, new values", plug_obj.status)


        if 'add_device' in request.POST:
            plugs.objects.create(plug_name=request.POST['plug_name'],
                                 plug_model_name=request.POST['plug_model_name'],
                                 ip_address=request.POST['ip_address'],
                                 room_no=room.objects.get(room_no=kwargs['room_no']))
        if 'remove_device' in request.POST:
            plugs.objects.filter(plug_no=request.POST.get('plug_no')).delete()

        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

#JSON for nessary data for hourly data

class Plugs(TemplateView):
   def get(self, request, *args, **kwargs):
       #Line graph for plugs hourly data
       plug_id = request.GET.get('plug_id')

       #We start with default hourly data
       if plug_id != None:
           now = datetime.datetime.now()
           time = now.time()
           day = now.day
           month = now.month
           year = now.year
           hour=time.hour
           hourly_data = []
           plug = plugs.objects.get(plug_name=plug_id)

           #sum for every hour
           for i in range(hour):
              sum = 0
              l = (list(plug_electricity_consumption.objects.filter(plug_no=plug,timestamp__day=day,timestamp__month=month,timestamp__year=year,timestamp__hour=i)))
              for j in l:
                  sum += j.Watt
              hourly_data.append({'hour':i,'Watts':sum})
           return JsonResponse(hourly_data, safe=False)

       return JsonResponse("{'error':'This plug does not exist in the database'}", safe=False)


#Sum Data for every Room for now every hour

class Rooms(TemplateView):
    def get(self, request, *args, **kwargs):
        room_id = request.GET.get('room_id')

        now = datetime.datetime.now()
        time = now.time()
        day = now.day
        month = now.month
        year = now.year
        hour=time.hour
        #Storing response data
        hourly_data = []
        #Storing all data for the plug
        hourly_data_tot_plug = []

        try:
            plugs_in_room = plugs.objects.filter(room_no=room_id).order_by("plug_no")
        except plugs.DoesNotExist:
            plugs_in_room = []
            for i in range(hour):
                hourly_data.append({'hour':i,'Watts':0})
            return JsonResponse(hourly_data, safe=False)

        # Forces it to an array if their is only 1 result
        if not hasattr(plugs_in_room, '__iter__'):
            plugs_in_room = [plugs_in_room]

        #Not a effective way but there is duplicate code but for the current time it's a working solution
        #sum for every hour

        for i in plugs_in_room:

             plug_no = plugs.objects.get(plug_name=i.plug_name)

             hourly_data_plug = []
             for k in range(hour):
                sum = 0
                l = (list(plug_electricity_consumption.objects.filter(plug_no=plug_no,timestamp__day=day,timestamp__month=month,timestamp__year=year,timestamp__hour=k)))
                for j in l:
                   sum += j.Watt
                hourly_data_plug.append({'hour':k,'Watts':sum})
             hourly_data_tot_plug.append(hourly_data_plug)

        for i in range(hour):
            sum = 0
            for j in hourly_data_tot_plug:
                sum += j[i]['Watts']
            hourly_data.append({'hour':i,'Watts':sum})

        return JsonResponse(hourly_data, safe=False)


# NOTICE : There is a lot of redudancy as doing inner API calls within django API server seems to be having some major issues
class total_consumption(TemplateView):
    def get(self, request, *args, **kwargs):

        now = datetime.datetime.now()
        time = now.time()
        day = now.day
        month = now.month
        year = now.year
        hour=time.hour

        #Storing response data
        hourly_data = []

        #Storing all data for rooms and plugs
        hourly_data_tot_room = []

        rooms = room.objects.all()

        for r in rooms:

            #Storing all data for the plug
            hourly_data_tot_plug = []
            hourly_data_room = []

            room_obj = room.objects.filter(room_no= r.room_no)

            # Redundant code
            try:
                plugs_in_room = plugs.objects.filter(room_no=room_obj).order_by("plug_no")
            except plugs.DoesNotExist:
                plugs_in_room = []
                for i in range(hour):
                    hourly_data_room.append({'hour':i,'Watts':0})
                hourly_data_tot_plug.append(hourly_data_room)

            # Forces it to an array if their is only 1 result
            if not hasattr(plugs_in_room, '__iter__'):
                plugs_in_room = [plugs_in_room]
