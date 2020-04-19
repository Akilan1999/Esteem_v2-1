from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group, User


def get_groups():
    print(Group.objects.all())


class AddUserForm(UserCreationForm):

    error_messages = {
        'duplicate_email': "A user with that e-mail already exists.",
        'password_mismatch': "The two password fields didn't match.",
    }
    username = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control', 'autocomplete': 'new-password'}))
    email = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control', 'type': 'email', 'autocomplete': 'new-password'}))
    first_name = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control'}))
    last_name = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control'}))
    password1 = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control', 'autocomplete': 'new-password', 'type': 'password'}))
    password2 = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control', 'autocomplete': 'new-password', 'type': 'password'}))
    user_group = forms.ModelChoiceField(queryset=Group.objects.all(), widget=forms.Select(
        attrs={'class': 'custom-select'}), empty_label=None)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')

