from django.contrib.sites import requests
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from Home.models import Rooms, Plugs, PlugElectricityConsumption, EnergyGeneration, EnergyMode, Battery, \
    PowerTransaction, PowerGeneration
import requests
import datetime


class BackgroundClass:
    @staticmethod
    def test_func():
        print("HIIIIIIIIIIII")

    @staticmethod
    def power_allot_func():
        # check power mode
        # Total power consumption by house
        # Do according transaction
        print("lol")

    @staticmethod
    def device_consumption():
        api_devices_list = requests.get("http://127.0.0.1:5000/api/alldevicesconsumption/").json()
        for device in api_devices_list:
            print(device['status'])
            if device['status'] == 'on':
                try:
                    plug_no = Plugs.objects.get(plug_name=device['DeviceName'])
                    PlugElectricityConsumption.objects.create(plug_no=plug_no, Watt=device['ElecConsp'])
                except Plugs.DoesNotExist:
                    plug_no = None


class HomePage(TemplateView):
    template_name = 'home/index.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {"Room": Rooms.objects.all()})

    def post(self, request, *args, **kwargs):
        if 'remove_room' in request.POST:
            Rooms.objects.filter(room_no=request.POST.get('room_no')).delete()
        else:
            Rooms.objects.create(room_name=request.POST.get('name'))

        return redirect('homepage')


class EnergyGeneration(TemplateView):
    template_name = 'home/energy.html'

    def get(self, request, *args, **kwargs):
        # Not secure but working solution
        # EDIT: I have no idea what this is but you can use **kwargs to get url parameters
        type_data = request.GET.get('type_data')

        if type_data is not None:
            EnergyMode.objects.all().delete()
            EnergyMode.objects.create(mode_id=type_data)

        # Sending current mode active
        return render(request, self.template_name, {"Energy_mode": EnergyMode.objects.all()})


class RoomPage(TemplateView):
    template_name = 'home/room.html'

    def get(self, request, *args, **kwargs):
        # Try and except for smart plugs in the room
        try:
            plugs_in_room = Plugs.objects.filter(room_no=kwargs["room_no"]).order_by("plug_no")
        except Plugs.DoesNotExist:
            plugs_in_room = []

        # Forces it to an array if their is only 1 result
        if not hasattr(plugs_in_room, '__iter__'):
            plugs_in_room = [plugs_in_room]

        consumption = []
        available_devices = []

        api_devices_list = requests.get("http://127.0.0.1:5000/api/alldevicesconsumption/").json()

        for device in api_devices_list:
            # If the device exist in current room, pass on its reading to the graph in front end.
            if Plugs.objects.filter(room_no=kwargs['room_no'], plug_name=device['DeviceName']).exists():
                consumption.append(device['CurConsp'])
            # If the device is not in the database (we use IP address as unique identifier),
            # that means it is a new device and we show it as a list in front end to be added.
            if not Plugs.objects.filter(ip_address=device['ip_address']).exists():
                available_devices.append([device['DeviceName'], device['ip_address']])

        return render(request, self.template_name, {"Room": Rooms.objects.all(),
                                                    "Room_in": Rooms.objects.get(room_no=kwargs["room_no"]),
                                                    "Plugs": plugs_in_room, "Consumption": consumption,
                                                    "available_devices": available_devices},
                      )

    def post(self, request, *args, **kwargs):

        if 'new_device' in request.POST:
            api_devices_list = requests.get("http://127.0.0.1:5000/api/alldevicesconsumption/").json()
            # Using generator, get the item from the list that matches the IP provided from front-end.
            device_data = next(item for item in api_devices_list
                               if item["ip_address"] == request.POST[request.POST['new_device'] + '_ip_address'])
            Plugs.objects.create(plug_name=device_data['DeviceName'],
                                 plug_model_name=device_data['DeviceModel'],
                                 ip_address=device_data['ip_address'],
                                 room_no=Rooms.objects.get(room_no=kwargs['room_no']),
                                 status=False if device_data['status'] == "off" else True)

        if 'change_status' in request.POST:
            values = request.POST['change_status'].split(',')
            print("Old values before pressing button", values)
            requests.get("http://127.0.0.1:5000/api/changestatus/" + values[1])
            plug_obj = Plugs.objects.get(ip_address=values[0], plug_name=values[1])
            print(plug_obj.status)

            if plug_obj.status:
                plug_obj.status = False
            else:
                plug_obj.status = True
            # plug_obj.status = True if plug_obj.status else False
            plug_obj.save()
            print("Button pressed, new values", plug_obj.status)

        if 'add_device' in request.POST:
            Plugs.objects.create(plug_name=request.POST['plug_name'],
                                 plug_model_name=request.POST['plug_model_name'],
                                 ip_address=request.POST['ip_address'],
                                 room_no=Rooms.objects.get(room_no=kwargs['room_no']))
        if 'remove_device' in request.POST:
            Plugs.objects.filter(plug_no=request.POST.get('plug_no')).delete()

        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


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
            plug = Plugs.objects.get(plug_name=plug_id)

            # sum for every hour
            for i in range(hour + 1):
                sum = 0
                l = (list(PlugElectricityConsumption.objects.filter(plug_no=plug, timestamp__day=day,
                                                                    timestamp__month=month, timestamp__year=year,
                                                                    timestamp__hour=i)))
                for j in l:
                    sum += j.Watt
                hourly_data.append({'hour': i, 'Watts': sum})
            return JsonResponse(hourly_data, safe=False)

        return JsonResponse("{'error':'This plug does not exist in the database'}", safe=False)
