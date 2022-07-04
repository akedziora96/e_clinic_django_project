from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator


def person_name_validator(name):
    if len(name.strip()) == 0:
        raise ValidationError("Field can not be empty!")
    for char in name:
        if not char.isalpha():
            raise ValidationError("Name should contains only latin letters!")
        if char.isspace():
            raise ValidationError("Name can not contain whitespaces!")
    return name


phone_regex_validator = RegexValidator(
        regex=r'^\+?1?\d{9,11}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 11 digits allowed."
)