from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group, User


def get_groups():
    print(Group.objects.all())


class AddUserForm(UserCreationForm):

    error_messages = {
        'duplicate_email': "A user with that e-mail already exists.",
        'email_mismatch': "The two e-mail fields didn't match.",
    }
    user_group = forms.ModelChoiceField(queryset=Group.objects.all())

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')

