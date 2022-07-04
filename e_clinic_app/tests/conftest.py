import os
import sys
import random

from django.contrib.auth.models import User
from faker import Faker
from django.test import Client
import pytest

from e_clinic_app.models import Specialization, Procedure, Doctor, Visit, Term, Patient, Office

fake = Faker("pl_PL")


@pytest.fixture
def client():
    client = Client()
    return client


@pytest.fixture
def set_up(db):
    for _ in range(10):
        Specialization.objects.create(name=fake.name())
        Procedure.objects.create(name=fake.name(), price=random.uniform(-1000.00, 1000.00))

    for _ in range(1):
        user = User.objects.create(is_superuser=0, username=fake.user_name(), email=fake.email(),
                                   last_name=fake.last_name(), first_name=fake.first_name())
        user.set_password(fake.password())

        specializations = list(Specialization.objects.all().order_by('?'))[:3]
        doctor = Doctor.objects.create(user=user, pesel=fake.pesel(),
                                       pwz=fake.pwz_doctor(), title_or_degree=random.randint(1, 5))
        doctor.specializations.set(specializations)

        user = User.objects.create(is_superuser=0, username=fake.user_name(), email=fake.email(),
                                   last_name=fake.last_name(), first_name=fake.first_name())
        user.set_password(fake.password())

        patient = Patient.objects.create(user=user, pesel=fake.pesel(),
                                         identification_type=random.randint(1, 2),
                                         phone_number=fake.phone_number())

        office = Office.objects.create(number=random.randint(0, 100))

        term = Term.objects.create(date=fake.date(), hour_from=fake.time(), hour_to=fake.time(),
                                   office=office, doctor=doctor)

        procedure = list(Procedure.objects.all().order_by('?'))[1]
        Visit.objects.create(patient=patient, doctor=doctor, date=term, procedure=procedure)