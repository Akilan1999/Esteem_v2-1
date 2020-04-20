from django.contrib import messages
from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from .forms import AddUserForm
from django.contrib.auth.models import Group, User
from Home.models import room


class AddUser(TemplateView):
    template_name = 'users/add_user.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {'form': AddUserForm(), 'Room': room.objects.all()})

    def post(self, request, *args, **kwargs):
        form = AddUserForm(request.POST)

        if form.is_valid():
            group_id = form['user_group'].value()
            user = form.save()
            user.groups.add(Group.objects.get(id=group_id))
            messages.success(request, "User created successfully!")
        else:
            return render(request, self.template_name, {'form': form})

        return redirect("add_user")


class ModifyUser(TemplateView):
    template_name = 'users/user_settings.html'

    def get(self, request, *args, **kwargs):

        return render(request, self.template_name, {'Users': User.objects.all(), 'Room': room.objects.all()})

    def post(self, request, *args, **kwargs):

        if request.POST['remove_user']:
            user = User.objects.get(id=request.POST['user_id'])
            messages.success(request, user.username + '\'s account deleted successfully!')
            user.delete()

        return redirect("user_settings")
