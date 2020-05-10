from django import forms
from django.contrib.auth.models import User
from fifth_app.models import Userprofileinfoform

class UserForm(forms.ModelForm):

    password = forms.CharField(widget=forms.PasswordInput())

    class Meta():
        model = User
        fields = ('username','email','password')

class Userprofileinfo(forms.ModelForm):
    class Meta():
        model = Userprofileinfoform
        fields = ('portfolio_site','profile_pic')
