import random
import datetime
from faker import Faker

from e_clinic_app.models import Term, Office

fake = Faker("pl_PL")


def fake_phone_number():
    return fake.phone_number().replace(' ', '')


def fake_term(doctor, multiple=False):

    """
    Creates valid dataset needed to create object term and pass form validation
    :param doctor: Doctor object.
    :param multiple: True when we want to add multiple terms, False if we want to add just single term.
    :return: If multiple = True it returns just dictionary with Term atributes values.
    If multiple=True it returns tuple with mentioned dictionary, cumuled term's length in minutes and visit length.
    """

    while True:
        hour_from = fake.time()
        hour_to = fake.time()
        office = Office.objects.order_by('?').first()
        date = fake.date_between(datetime.datetime.now())

        hour_from_f = datetime.datetime.strptime(hour_from, '%H:%M:%S')
        hour_to_f = datetime.datetime.strptime(hour_to, '%H:%M:%S')

        if hour_from_f > hour_to_f:
            continue
        if Term.objects.filter(date=date, hour_from=hour_from, hour_to=hour_to, office=office, doctor=doctor).exists():
            continue
        break

    fake_term_data = {
        'date': date,
        'hour_from': hour_from,
        'hour_to': hour_to,
        'office': office.id
        }

    if multiple:

        fake_term_data['visit_time'] = 60
        hour_from_f = datetime.datetime.strptime(hour_from, '%H:%M:%S')
        hour_to_f = datetime.datetime.strptime(hour_to, '%H:%M:%S')
        day_hour_to = datetime.datetime.combine(date.today(), hour_to_f.time())
        day_hour_from = datetime.datetime.combine(date.today(), hour_from_f.time())
        minutes = (day_hour_to - day_hour_from).total_seconds() / 60.0

        return fake_term_data, minutes, fake_term_data.get('visit_time')

    return fake_term_data


if __name__ == '__main__':
    print(fake_phone_number())