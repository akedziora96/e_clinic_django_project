from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


from e_clinic_app.models import Visit, Patient, Term
from e_clinic_app.validators import person_name_validator


class AddVisitForm(forms.ModelForm):
    """Takes procedure."""

    class Meta:
        model = Visit
        fields = ('procedure',)


class RegisterFormUser(UserCreationForm):
    """Takes information needed to create User."""

    def __init__(self, *args, **kwargs):
        super(RegisterFormUser, self).__init__(*args, **kwargs)

        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['email'].required = True

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
    """Takes information needed to create Patient."""

    class Meta:
        model = Patient
        fields = '__all__'
        exclude = ('user', 'email',)


class EditFormUser(RegisterFormUser):
    """
    Takes information needed to edit User. Password fields are disabled.
    To edit patient you can use RegisterFormPatient.
    """

    def __init__(self, *args, **kwargs):
        super(EditFormUser, self).__init__(*args, **kwargs)
        del self.fields['password1']
        del self.fields['password2']

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email',)


class TermAddForm(forms.ModelForm):
    """Takes information needed to create Term."""

    def __init__(self, *args, **kwargs):
        """Enable to use User object in validation"""
        self.user = kwargs.pop('user', None)
        super(TermAddForm, self).__init__(*args, **kwargs)

    def clean(self):
        """
        Validate if there is no intersection between new potential term and terms allready added
        (date, time, doctors and offices). Method also check if term is not set on Sundays and end of term
        is after start.
        """
        data = super().clean()

        date = data.get('date')
        hour_from = data.get('hour_from')
        hour_to = data.get('hour_to')
        office = data.get('office')

        if hour_from > hour_to:
            raise ValidationError(f"End must be after beginning of visit!")

        if date.weekday() + 1 == 7:
            raise ValidationError(f"Clinic is closed on Sundays!")

        possible_term = Term.objects.filter(date=date)
        pt = possible_term.filter(hour_from__lte=hour_from, hour_to__gte=hour_to)
        pt |= possible_term.filter(hour_from__lte=hour_from, hour_to__gt=hour_from, hour_to__lte=hour_to)
        pt |= possible_term.filter(hour_from__gte=hour_from, hour_from__lte=hour_to, hour_to__gte=hour_to)
        pt |= possible_term.filter(hour_from__gte=hour_from, hour_to__lte=hour_to)
        pt2 = pt.filter(office=office)
        pt2 |= pt.filter(doctor=self.user.doctor)

        if pt2.exists():
            raise ValidationError(f"Office is already occupied in this term!")

    class Meta:
        model = Term
        fields = '__all__'
        exclude = ('doctor',)
        widgets = {
            'date': forms.TextInput(attrs={'type': 'date'}),
            'hour_from': forms.TextInput(attrs={'type': 'time'}),
            'hour_to': forms.TextInput(attrs={'type': 'time'}),
        }


class MultipleTermAddForm(TermAddForm):
    """Is extension of TermAddForm. The form is extended by visit_time field needed to auto add  multiple terms."""
    visit_time = forms.ChoiceField(choices={(20, "20 minutes"), (30, "30 minutes"), (60, "1 hour")})



