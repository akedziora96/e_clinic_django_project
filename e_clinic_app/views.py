import datetime

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.http import HttpResponse, Http404
from django.urls import reverse_lazy

from . import forms
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, DeleteView
from e_clinic_app.models import Specialization, Doctor, Procedure, Term, Visit, Patient
from .datetime_functions import get_monday, get_saturday
from .forms import RegisterFormUser, RegisterFormPatient

WEEKDAYS = {
    1: "Poniedziałek",
    2: "Wtorek",
    3: "Środa",
    4: "Czwartek",
    5: "Piątek",
    6: "Sobota"
}


class LandingPage(View):

    def get(self, request):
        return render(request, 'index.html')


class SpecializationList(ListView):
    model = Specialization
    template_name = 'specialization_list.html'


class SpecializationDetails(DetailView):
    model = Specialization
    template_name = 'specialization_detail.html'

    def get(self, request, *args, **kwargs):
        data = super().get(request, *args, **kwargs)
        offset = request.GET.get('week', 0)
        offset_session = request.session.get('offset')
        if offset_session is not None:
            request.session['offset'] += int(offset)
        else:
            request.session['offset'] = 0
        print(request.session.get('offset'))
        return data

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        spec_doctors = self.object.doctor_set.all().order_by('user__last_name').order_by('user__first_name')


        offset = kwargs.get('offset', 0)


        start = get_monday(0)
        end = get_saturday(0)
        date_generated = [start + datetime.timedelta(days=n) for n in range(0, (end-start).days+1)]

        weekdays = {WEEKDAYS[date.weekday()+1]: date.strftime("%d.%m") for date in date_generated}
        context['weekdays'] = weekdays

        # week_schedule = {spec_doctor: [spec_doctor.schedule.filter(date=date).first() for date in date_generated]
        #                  for spec_doctor in spec_doctors}
        # context['doctor_week_schedule'] = week_schedule

        week_terms = {}
        for spec_doctor in spec_doctors:
            temp = []
            for date in date_generated:
                temp.append(spec_doctor.terms.filter(date=date).order_by('date'))
            week_terms[spec_doctor] = temp

        context['doctor_week_terms'] = week_terms
        return context


class ProcedureList(ListView):
    model = Procedure
    template_name = 'procedure_list.html'


class ProcedureDetails(DetailView):
    model = Procedure
    template_name = 'procedure_detail.html'


class DoctorDetails(DetailView):
    model = Doctor
    template_name = 'doctor_detail.html'


class VisitAdd(View):

    def get(self, request, doc_id, date, hour):

        if request.user.is_authenticated:
            user_id = request.user.id

            patient = get_object_or_404(Patient, user_id=user_id)
            doctor = get_object_or_404(Doctor, id=doc_id)
            date = get_object_or_404(Term, date=date, hour_from=hour)
            form = forms.AddVisitForm(initial={'doctor': doctor, 'date': date})

            procedures = doctor.procedures.all()
            if not procedures:
                raise Http404
            form.fields['procedure'].choices = [(procedure.id, procedure) for procedure in procedures]

            return render(request, 'visit_add.html', {'form': form, 'doctor': doctor, 'date': date, 'patient': patient})

        return redirect('login-page')

    def post(self, request, doc_id, date, hour):

        user = request.user
        patient = get_object_or_404(Patient, user=user)
        doctor = get_object_or_404(Doctor, id=doc_id)
        date = get_object_or_404(Term, date=date, hour_from=hour)
        form = forms.AddVisitForm(request.POST)

        if form.is_valid():
            data = form.cleaned_data
            procedure = data.get('procedure')

            Visit.objects.create(patient=patient, doctor=doctor, date=date, procedure=procedure)

            return redirect('main-page')

        return HttpResponse('Śwignij jakimś błędem')


class SignUpView(View):

    def get(self, request):
        form_user = RegisterFormUser
        form_patient = RegisterFormPatient
        return render(request, "registration/signup.html", {'form_user': form_user, 'form_patient': form_patient})

    def post(self, request):
        form_user = forms.RegisterFormUser(request.POST)

        if form_user.is_valid():
            data = form_user.cleaned_data
            username = data.get('username')
            first_name = data.get('first_name')
            last_name = data.get('last_name')
            email = data.get('email')
            password = data.get('password1')

            user = User.objects.create(
                                is_superuser=0, username=username, email=email,
                                last_name=last_name, first_name=first_name
            )
            user.set_password(password)
            user.save()

            patient_user = forms.RegisterFormPatient(request.POST)

            if patient_user.is_valid():
                data = patient_user.cleaned_data
                pesel = data.get('pesel')
                identification_type = data.get('identification_type')
                phone_number = data.get('phone_number')

                Patient.objects.create(
                                user=user, pesel=pesel,
                                identification_type=identification_type,
                                phone_number=phone_number
                )


class PatientVisits(ListView):
    model = Visit
    template_name = 'patient_visits.html'

    def get_queryset(self):
        patient = get_object_or_404(Patient, user=self.request.user)
        visits = Visit.objects.filter(patient=patient)
        return visits


class VisitDetails(DetailView):
    model = Visit
    template_name = 'visit_detail.html'


class VisitCancel(DeleteView):
    model = Visit
    template_name = 'visit_delete.html'
    success_url = reverse_lazy('patient-visits')