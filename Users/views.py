from django.contrib import messages
from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from .forms import AddUserForm
from django.contrib.auth.models import Group

class AddUser(TemplateView):
    template_name = 'users/add_user.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {'form': AddUserForm()})

    def post(self, request, *args, **kwargs):
        form = AddUserForm(request.POST)

        if form.is_valid():
            group_id = form['user_group'].value()
            user = form.save()
            user.groups.add(Group.objects.get(id=group_id))
            messages.success(request, "User created successfully!")
        else:
            messages.error(request, form.errors)

        return redirect("add_user")
