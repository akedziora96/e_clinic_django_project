import datetime
import re

from django.core.exceptions import ValidationError

default_error_messages = {
    'invalid': 'National Identification Number consists of 11 digits.',
    'checksum': 'Wrong checksum for the National Identification Number.',
}


def person_name_validator(name):
    """Checks if name contains only latin letters and has no whitespaces"""
    if len(name.strip()) == 0:
        raise ValidationError("Field can not be empty!")
    for char in name:
        if not char.isalpha():
            raise ValidationError("Name should contains only latin letters!")
        if char.isspace():
            raise ValidationError("Name can not contain whitespaces!")
    return name


def pwz_validator(pwz_number):
    """Checks if pwz number contains 7 digits and has valid checksum"""
    pwz_number = str(pwz_number)
    if not len(pwz_number):
        raise ValidationError("PWZ number must contain 7 digits!")
    if pwz_number.startswith("0"):
        raise ValidationError("PWZ number must contain 7 digits!")
    if sum(ratio * int(digit) for ratio, digit in zip(range(1, 7), pwz_number[1:])) % 11 != int(pwz_number[0]):
        raise ValidationError("Invalid number!")
    return int(pwz_number)


def phone_regex_validator(phone_number):
    """Checks if phone number is propper formated"""
    if not re.fullmatch(r'^\+?1?\d{9,11}$', phone_number):
        raise ValidationError("Phone number must be entered in the format: '+999999999'. Up to 11 digits allowed.")
    return phone_number


def has_valid_checksum(number):
    """Calculates a checksum with the provided algorithm."""
    multiple_table = (1, 3, 7, 9, 1, 3, 7, 9, 1, 3, 1)
    result = 0
    for i, digit in enumerate(number):
        result += int(digit) * multiple_table[i]
    return result % 10 == 0


def pesel_validator(number):
    """Check if pesell contains 11 digits and has valid checksum"""
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


def date_validator(date):
    """Checks if date of term is not from past."""
    if date < datetime.date.today():
        raise ValidationError("Date is from the past")
    return date


if __name__ == '__main__':
    # print(pwz_validator(5425741))
    # print(pesel_validator(73100677372))
    # print(has_valid_checksum(str(73100677372)))
    print(phone_regex_validator("+4850595860"))