from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from e_clinic_app.models import Visit, Patient


class AddVisitForm(forms.ModelForm):

    class Meta:
        model = Visit
        fields = ('procedure',)


class RegisterFormUser(UserCreationForm):
    # email = forms.EmailField(label="Email")
    # first_name = forms.CharField(label="Imię")
    # last_name = forms.CharField(label="Nazwisko")

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')


class RegisterFormPatient(forms.ModelForm):

    class Meta:
        model = Patient
        fields = '__all__'
        exclude = ('user', 'email',)