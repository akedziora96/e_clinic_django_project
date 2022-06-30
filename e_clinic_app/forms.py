from django import forms

from e_clinic_app.models import Visit


class AddVisitForm(forms.ModelForm):

    class Meta:
        model = Visit
        fields = ('patient', 'doctor', 'procedure')
        widgets = {
            'doctor': forms.Select(),
        }
