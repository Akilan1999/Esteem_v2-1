from django import forms
from django.contrib.auth.forms import AuthenticationForm


class LoginForm(AuthenticationForm):

    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'penis'}))
    password = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control form-control-lg'}))
