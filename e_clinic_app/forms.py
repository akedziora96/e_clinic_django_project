from datetime import datetime

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from e_clinic_app.models import Visit, Patient, Term

MINUTES = [
    (15, "15 minut"),
    (20, "20 minut"),
    (30, "30 minut"),
    (45, "45 minut"),
    (60, "1 godzina")
]


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


class TermAddForm(forms.ModelForm):
    pass

    class Meta:
        model = Term
        fields = '__all__'
        exclude = ('doctor',)
        widgets = {
            'date': forms.SelectDateWidget(),
            'hour_from': forms.TimeInput(format='%H:%M'),
            'hour_to': forms.TimeInput(format='%H:%M')
        }

    def __init__(self, *args, **kwargs):
        super(TermAddForm, self).__init__(*args, **kwargs)
        self.fields['date'].initial = datetime.today()
        self.fields['hour_from'].initial = "08:00"
        self.fields['hour_to'].initial = "16:00"


# class TermAddFormExpansion(forms.Form):
#     visit_time = forms.ChoiceField(choices=MINUTES, label="ustaw automatycznie czas wizyty", initial=30)
