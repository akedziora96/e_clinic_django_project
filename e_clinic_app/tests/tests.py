import random
from django.contrib.auth.models import User
from django.test import TestCase, Client
import pytest

from e_clinic_app.models import Specialization, Procedure, Doctor, Visit


@pytest.mark.django_db
def test_user_num(client, set_up):
    num_of_specializations = Specialization.objects.all().count()
    assert num_of_specializations > 0


@pytest.mark.django_db
def test_landing_page_view(client, set_up):
    response = client.get('')
    assert response.status_code == 200


@pytest.mark.django_db
def test_specialization_list_view(client, set_up):
    response = client.get('/specializations/')
    assert response.status_code == 200


@pytest.mark.django_db
def test_specialization_detail_view(client, set_up):
    specialization = Specialization.objects.all().first()
    response = client.get(f'/specialization/{specialization.id}/')
    assert response.status_code == 200


@pytest.mark.django_db
def test_specialization_detail_view_with_offset(client, set_up):
    specialization = Specialization.objects.all().first()
    response = client.get(f'/specialization/{specialization.id}/?week={random.randint(0,1000)}')
    assert response.status_code == 200


@pytest.mark.django_db
def test_procedures_list_view(client, set_up):
    response = client.get('/procedures/')
    assert response.status_code == 200


@pytest.mark.django_db
def test_procedure_detail_view(client, set_up):
    procedure = Procedure.objects.first()
    response = client.get(f'/procedure/{procedure.id}/')
    assert response.status_code == 200


@pytest.mark.django_db
def test_doctor_detail_view(client, set_up):
    doctor = Doctor.objects.first()
    response = client.get(f'/doctor/{doctor.id}/')
    assert response.status_code == 200


@pytest.mark.django_db
def test_user_visits_view_without_loging_in(client, set_up):
    response = client.get(f'/yourvisits/')
    assert response.status_code == 302
    assert response.url == '/login/?next=/yourvisits/'


@pytest.mark.django_db
def test_user_visits_view_with_loging_in(client, set_up):
    user = User.objects.order_by('?').first()
    client.force_login(user=user)
    response = client.get(f'/yourvisits/')
    assert response.status_code == 200


@pytest.mark.django_db
def test_user_visits_view_without_loging_in(client, set_up):
    visit = Visit.objects.order_by('?').first()
    response = client.get(f'/visit/{visit.id}/')
    assert response.status_code == 302
    assert response.url == f'/login/?next=/visit/{visit.id}/'