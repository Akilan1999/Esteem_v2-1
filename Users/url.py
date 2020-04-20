from django.urls import path
from .views import AddUser, ModifyUser

urlpatterns = [
    path('add_user', AddUser.as_view(), name='add_user'),
    path('user_settings', ModifyUser.as_view(), name='user_settings'),
]
