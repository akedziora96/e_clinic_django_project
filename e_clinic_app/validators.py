import re

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


default_error_messages = {
    'invalid': 'National Identification Number consists of 11 digits.',
    'checksum': 'Wrong checksum for the National Identification Number.',
    'birthdate': 'The National Identification Number contains an invalid birth date.'
}


def has_valid_checksum(number):
    """Calculates a checksum with the provided algorithm."""
    multiple_table = (1, 3, 7, 9, 1, 3, 7, 9, 1, 3, 1)
    result = 0
    for i, digit in enumerate(number):
        result += int(digit) * multiple_table[i]
    return result % 10 == 0


def pesel_validator(number):
    try:
        number = str(number)
    except TypeError:
        raise ValidationError(default_error_messages['invalid'], code='invalid')
    if not re.match(r'^\d{11}$', number):
        print('123')
        raise ValidationError(default_error_messages['invalid'], code='invalid')
    if not has_valid_checksum(str(number)):
        raise ValidationError(default_error_messages['checksum'], code='checksum')
    return int(number)


if __name__ == '__main__':
    # print(pwz_validator(5425741))
    print(pesel_validator(73100677372))
    print(has_valid_checksum(str(73100677372)))