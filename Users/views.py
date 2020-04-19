from django.contrib import messages
from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from .forms import AddUserForm
from django.contrib.auth.models import Group
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
