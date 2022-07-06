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


def pwz_validator(pwz_number):
    pwz_number = str(pwz_number)
    if not len(pwz_number):
        raise ValidationError("PWZ number must contain 7 digits!")
    if pwz_number.startswith("0"):
        raise ValidationError("PWZ number must contain 7 digits!")
    if sum(ratio * int(digit) for ratio, digit in zip(range(1, 7), pwz_number[1:])) % 11 != int(pwz_number[0]):
        raise ValidationError("Invalid number!")
    return int(pwz_number)


phone_regex_validator = RegexValidator(
        regex=r'^\+?1?\d{9,11}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 11 digits allowed."
)


if __name__ == '__main__':
    print(pwz_validator(5425741))