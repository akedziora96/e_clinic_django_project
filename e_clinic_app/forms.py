from datetime import datetime

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

from localflavor.pl.forms import PLPESELField
from e_clinic_app.models import Visit, Patient, Term, Doctor


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
        if len(first_name.strip()) == 0:
            raise ValidationError("Pole 'imię' nie może być puste!")
        for char in first_name:
            if not char.isalpha():
                raise ValidationError("Imię powinno składać się wyłącznie z liter alfabetu łacińskiego!")
            if char.isspace():
                raise ValidationError("Imię nie może zawierać białych znaków!")
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        if len(last_name.strip()) == 0:
            raise ValidationError("Pole 'nazwisko' nie może być puste!")
        for char in last_name:
            if not char.isalpha():
                raise ValidationError("Imię powinno składać się wyłącznie z liter alfabetu łacińskiego!")
            if char.isspace():
                raise ValidationError("Imię nie może zawierać białych znaków!")
        return last_name


class RegisterFormPatient(forms.ModelForm):
    pesel = PLPESELField(required=True)
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    phone_number = forms.CharField(validators=[phone_regex], max_length=17, required=True)

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
            raise ValidationError(f"Gabinet zajęty")

    class Meta:
        model = Term
        fields = '__all__'
        exclude = ('doctor',)
        widgets = {
            'date': forms.SelectDateWidget(),
            'hour_from': forms.TimeInput(format='%H:%M'),
            'hour_to': forms.TimeInput(format='%H:%M')
        }

# class TermAddFormExpansion(forms.Form):
#     visit_time = forms.ChoiceField(choices=MINUTES, label="ustaw automatycznie czas wizyty", initial=30)
