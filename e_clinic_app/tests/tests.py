import random

from django.contrib.auth.models import User
import pytest
from faker import Faker

from e_clinic_app.models import Specialization, Procedure, Doctor, Visit, Term, Patient, Office
from e_clinic_app.tests.utilities import fake_term

fake = Faker("pl_PL")


@pytest.mark.django_db
def test_user_num(client, set_up):
    num_of_specializations = Specialization.objects.all().count()
    assert num_of_specializations > 0


@pytest.mark.django_db
def test_landing_page_view(client):
    response = client.get('')
    assert response.status_code == 200


@pytest.mark.django_db
def test_specialization_list_view(client, set_up):
    response = client.get('/specializations/')
    assert response.status_code == 200
    assert response.context.get('specialization_list').count() == 10


@pytest.mark.django_db
def test_specialization_detail_view(client, set_up):
    specialization = Specialization.objects.all().first()
    response = client.get(f'/specialization/{specialization.id}/')
    assert response.status_code == 200
    assert response.context.get('specialization') == specialization


@pytest.mark.django_db
def test_specialization_detail_view_with_offset(client, set_up):
    specialization = Specialization.objects.first()
    response = client.get(f'/specialization/{specialization.id}/?week={random.randint(0,1000)}')
    assert response.status_code == 200
    assert response.context.get('specialization') == specialization


@pytest.mark.django_db
def test_procedures_list_view(client, set_up):
    response = client.get('/procedures/')
    assert response.status_code == 200
    assert response.context.get('procedure_list').count() == 10


@pytest.mark.django_db
def test_procedure_detail_view(client, set_up):
    procedure = Procedure.objects.first()
    response = client.get(f'/procedure/{procedure.id}/')
    assert response.status_code == 200
    assert response.context.get('procedure') == procedure


@pytest.mark.django_db
def test_doctor_detail_view(client, set_up):
    doctor = Doctor.objects.first()
    response = client.get(f'/doctor/{doctor.id}/')
    assert response.status_code == 200
    assert response.context.get('doctor') == doctor


@pytest.mark.django_db
def test_cancel_visit_view(client, set_up):
    """Tests if only doctors and patients have permission to cancel their visits."""
    before_cancel_visit_counter = Visit.objects.count()

    user = User.objects.order_by('?').first()
    client.force_login(user=user)
    visit = None

    if getattr(user, 'doctor', False):
        visit = user.doctor.visit_set.first()
    elif getattr(user, 'patient', False):
        visit = user.patient.visit_set.first()

    response = client.get(f'/visit/{visit.id}/cancel/')
    assert response.status_code == 200

    post_response = client.post(f'/visit/{visit.id}/cancel/')
    assert post_response.status_code == 302
    assert post_response.url == '/yourvisits/'

    after_cancel_visit_counter = Visit.objects.count()
    assert before_cancel_visit_counter - after_cancel_visit_counter == 1

    client.logout()
    assert post_response.status_code == 302


@pytest.mark.django_db
def test_user_visits_view(client, set_up):
    """Tests if only doctors and patients have permission to see their visits and the display of visits is valid."""
    patient = Patient.objects.first()
    doctor = Doctor.objects.first()

    response = client.get(f'/yourvisits/')
    assert response.status_code == 302
    assert response.url == f'/login/?next=/yourvisits/'

    user = patient.user
    client.force_login(user=user)
    response = client.get(f'/yourvisits/')
    assert response.status_code == 200
    assert response.context.get('visit_list').count() == 1

    client.logout()

    response = client.get(f'/yourvisits/')
    assert response.status_code == 302
    assert response.url == f'/login/?next=/yourvisits/'

    user = doctor.user
    client.force_login(user=user)
    response = client.get(f'/yourvisits/')
    assert response.status_code == 200
    assert response.context.get('visit_list').count() == 1


@pytest.mark.django_db
def test_user_visit_view(client, set_up):
    """Tests if only doctors and patients have permission to see their visit and the display of visit is valid."""
    patient = Patient.objects.first()
    doctor = Doctor.objects.first()
    visit = patient.visit_set.first()

    response = client.get(f'/visit/{visit.id}/')
    assert response.status_code == 302
    assert response.url == f'/login/?next=/visit/{visit.id}/'

    user = patient.user
    client.force_login(user=user)
    response = client.get(f'/visit/{visit.id}/')
    assert response.status_code == 200
    assert response.context.get('visit') == visit

    client.logout()

    visit = doctor.visit_set.first()

    response = client.get(f'/visit/{visit.id}/')
    assert response.status_code == 302
    assert response.url == f'/login/?next=/visit/{visit.id}/'

    user = doctor.user
    client.force_login(user=user)
    response = client.get(f'/visit/{visit.id}/')
    assert response.status_code == 200
    assert response.context.get('visit') == visit


@pytest.mark.django_db
def test_cancel_term_view(client, set_up):
    """Tests if only doctors have permission to cancel term and if term was canceled correctly."""
    before_cancel_term_counter = Term.objects.count()

    doctor = Doctor.objects.first()
    patien = Patient.objects.first()
    term = doctor.term_set.order_by('?').first()

    response = client.get(f'/cancel_term/{term.id}/')
    assert response.status_code == 302

    user = patien.user
    client.force_login(user=user)

    response = client.get(f'/cancel_term/{term.id}/')
    assert response.status_code == 403

    user = doctor.user
    client.force_login(user=user)

    response = client.get(f'/cancel_term/{term.id}/')
    assert response.status_code == 200

    post_response = client.post(f'/cancel_term/{term.id}/')
    assert post_response.status_code == 302
    assert post_response.url == f'/specialization/{doctor.specializations.first().id}/'

    after_cancel_term_counter = Term.objects.count()
    assert before_cancel_term_counter - after_cancel_term_counter == 1


@pytest.mark.django_db
def test_login_view(client, set_up):
    username = 'test_user'
    password = 'test_pass'
    User.objects.create_user(username=username, password=password)

    response = client.get('/login/')
    assert response.status_code == 200

    client.login(username=username, password=password)
    response = client.get('/login/')
    assert response.status_code == 302
    assert response.url == '/'

    post_response = client.post('/login/')
    assert post_response.url == f'/'


@pytest.mark.django_db
def test_logout_view(client, set_up):
    username = 'test_user'
    password = 'test_pass'
    User.objects.create_user(username=username, password=password)
    response = client.get('/logout/')
    assert response.status_code == 302
    assert response.url == f'/login/'

    client.login(username=username, password=password)
    response = client.get('/logout/')
    assert response.status_code == 302
    assert response.url == f'/login/'


@pytest.mark.django_db
def test_register_visit_view(client, set_up):
    """Tests if visit through view with form was added correctly."""
    term = Term.objects.first()
    patient = Patient.objects.first()
    doctor = Doctor.objects.first()

    response = client.get(f'/register_visit/{doctor.id}/{term.date}/{term.hour_from}/')
    assert response.status_code == 302

    user = doctor.user
    client.force_login(user=user)
    response = client.get(f'/register_visit/{doctor.id}/{term.date}/{term.hour_from}/')
    assert response.status_code == 403

    user = patient.user
    client.force_login(user=user)
    response = client.get(f'/register_visit/{doctor.id}/{term.date}/{term.hour_from}/')
    assert response.status_code == 200
    count_before_create = Visit.objects.count()

    post_response = client.post(f'/register_visit/{doctor.id}/{term.date}/{term.hour_from}/', {
            'procedure': random.choices(doctor.procedures.values_list('id', flat=True))})

    assert post_response.status_code == 302
    assert post_response.url == f'/yourvisits/'
    count_after_create = Visit.objects.count()
    assert count_after_create == count_before_create + 1


@pytest.mark.django_db
def test_signup_view(client, set_up):
    user_count_before_create = User.objects.count()
    patient_count_before_create = Patient.objects.count()

    response = client.get(f'/signup/')
    assert response.status_code == 200

    fake_patient = {
        'username': fake.user_name(),
        'first_name': fake.first_name(),
        'last_name': fake.last_name(),
        'email': fake.email(),
        'password1': 'superstrongpassword12345',
        'password2': 'superstrongpassword12345',
        'pesel': fake.pesel(),
        'identification_type': random.randint(1, 2),
        'phone_number': '48505958860'
    }

    post_response = client.post(f'/signup/', fake_patient)

    assert post_response.status_code == 302
    assert post_response.url == '/login/'
    user_count_after_create = User.objects.count()
    patient_count_after_create = Patient.objects.count()

    assert user_count_after_create == user_count_before_create + 1
    assert patient_count_after_create == patient_count_before_create + 1


@pytest.mark.django_db
def test_add_term_view(client, set_up):
    """Tests if term through view with form was added correctly."""
    term_count_before_create = Term.objects.count()
    patient = Patient.objects.first()
    doctor = Doctor.objects.first()
    office = Office.objects.first()

    response = client.get(f'/add_term/')
    assert response.status_code == 302

    user = patient.user
    client.force_login(user=user)
    response = client.get(f'/add_term/')
    assert response.status_code == 403

    user = doctor.user
    client.force_login(user=user)
    response = client.get(f'/add_term/')
    assert response.status_code == 200

    data = fake_term(doctor, multiple=False)

    post_response = client.post(f'/add_term/', data)
    term_count_after_create = Term.objects.count()
    assert post_response.status_code == 302
    assert post_response.url == f'/specialization/{doctor.specializations.first().id}/'
    assert term_count_after_create == term_count_before_create + 1


@pytest.mark.django_db
def test_add_multiple_term_view(client, set_up):
    """It's variation of test_add_term_view. It tests if multiple term was added."""
    term_count_before_create = Term.objects.count()
    patient = Patient.objects.first()
    doctor = Doctor.objects.first()

    response = client.get(f'/add_multiple_term/')
    assert response.status_code == 302

    user = patient.user
    client.force_login(user=user)
    response = client.get(f'/add_multiple_term/')
    assert response.status_code == 403

    user = doctor.user
    client.force_login(user=user)
    response = client.get(f'/add_multiple_term/')
    assert response.status_code == 200

    data, minutes_for_visits, time_for_visit = fake_term(doctor, multiple=True)

    post_response = client.post(f'/add_multiple_term/', data)
    term_count_after_create = Term.objects.count()
    assert post_response.status_code == 302
    assert post_response.url == f'/specialization/{doctor.specializations.first().id}/'
    assert term_count_after_create == term_count_before_create + int(minutes_for_visits/time_for_visit)


@pytest.mark.django_db
def test_change_password_view(client, set_up):
    username = 'test_user'
    password = 'test_pass'
    User.objects.create_user(username=username, password=password)
    response = client.get(f'/change_password/')
    assert response.status_code == 302

    client.login(username=username, password=password)
    response = client.get(f'/change_password/')
    assert response.status_code == 200

    data = {
        'old_password': password,
        'new_password1': 'superstrongpassword12345',
        'new_password2': 'superstrongpassword12345'
    }

    post_response = client.post(f'/change_password/', data)
    assert post_response.status_code == 302
    assert post_response.url == '/login/'

    client.login(username=username, password='superstrongpassword12345')
    response = client.get('/login/')
    assert response.status_code == 302
    assert response.url == '/'

    post_response = client.post('/login/')
    assert post_response.url == f'/'


@pytest.mark.django_db
def test_edit_user_view(client, set_up):
    patient = Patient.objects.first()
    doctor = Doctor.objects.first()

    response = client.get(f'/edit_user/')
    assert response.status_code == 302

    user = doctor.user
    client.force_login(user=user)
    response = client.get(f'/edit_user/')
    assert response.status_code == 302

    user = patient.user
    client.force_login(user=user)
    response = client.get(f'/edit_user/')
    assert response.status_code == 200

    new_user_name = fake.user_name()
    new_first_name = fake.first_name()
    new_last_name = fake.last_name()
    new_email = fake.email()
    new_pesel = fake.pesel()
    new_identification_type = random.randint(1, 2)

    data = {
        'username': new_user_name,
        'first_name': new_first_name,
        'last_name': new_last_name,
        'email': new_email,
        'pesel': new_pesel,
        'identification_type': new_identification_type,
        'phone_number': '48505958860'
    }

    post_response = client.post(f'/edit_user/', data)
    assert post_response.status_code == 302
    assert post_response.url == '/'
    patient = Patient.objects.first()
    user = patient.user
    assert user.username == new_user_name
    assert user.first_name == new_first_name
    assert user.last_name == new_last_name
    assert user.email == new_email
    assert patient.identification_type == new_identification_type
    assert patient.phone_number == '48505958860'