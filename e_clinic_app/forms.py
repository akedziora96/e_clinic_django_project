from datetime import datetime

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from localflavor.pl.forms import PLPESELField
from e_clinic_app.models import Visit, Patient, Term
from e_clinic_app.validators import phone_regex_validator, person_name_validator


class AddVisitForm(forms.ModelForm):

    class Meta:
        model = Visit
        fields = ('procedure',)


class RegisterFormUser(UserCreationForm):

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        return person_name_validator(first_name)

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        return person_name_validator(last_name)


class RegisterFormPatient(forms.ModelForm):
    pesel = PLPESELField(required=True)
    phone_number = forms.CharField(validators=[phone_regex_validator], max_length=17, required=True)

    class Meta:
        model = Patient
        fields = '__all__'
        exclude = ('user', 'email',)


class TermAddForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(TermAddForm, self).__init__(*args, **kwargs)
        self.fields['date'].initial = datetime.today()
        self.fields['hour_from'].initial = "08:00"
        self.fields['hour_to'].initial = "16:00"

    def clean(self):
        data = super().clean()

        date = data.get('date')
        hour_from = data.get('hour_from')
        hour_to = data.get('hour_to')
        office = data.get('office')

        possible_term = Term.objects.filter(date=date)
        pt = possible_term.filter(hour_from__lte=hour_from, hour_to__gte=hour_to)
        pt |= possible_term.filter(hour_from__lte=hour_from, hour_to__gt=hour_from, hour_to__lte=hour_to)
        pt |= possible_term.filter(hour_from__gte=hour_from, hour_from__lte=hour_to, hour_to__gte=hour_to)
        pt |= possible_term.filter(hour_from__gte=hour_from, hour_to__lte=hour_to)
        pt2 = pt.filter(office=office)
        pt2 |= pt.filter(doctor=self.user.doctor)

        if pt2.exists():
            raise ValidationError(f"Office is already occupied!")

    class Meta:
        model = Term
        fields = '__all__'
        exclude = ('doctor',)
        widgets = {
            'date': forms.SelectDateWidget(),
            'hour_from': forms.TimeInput(format='%H:%M'),
            'hour_to': forms.TimeInput(format='%H:%M')
        }

