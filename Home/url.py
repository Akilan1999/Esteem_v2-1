from django.urls import path
from .views import HomePage, EnergyGeneration, RoomPage, Plugs, Rooms, EnergyDistribution, RoomsWeekly

urlpatterns = [
    path('', HomePage.as_view(), name='homepage'),
    path('energy', EnergyGeneration.as_view(), name='energygeneration'),
    path('room/<int:room_no>/', RoomPage.as_view(), name='roompage'),
    path('plug', Plugs.as_view(), name='plug'),
    path('room', Rooms.as_view(), name='room'),
    path('energy_data', EnergyDistribution.as_view(), name='energy_dsitribution'),
    path('prev_thisweek', RoomsWeekly.as_view(), name='this_prevweek'),
]
