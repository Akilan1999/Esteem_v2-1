from django.urls import path
from .views import AddUser

urlpatterns = [
    path('add_user', AddUser.as_view(), name='add_user'),
]
