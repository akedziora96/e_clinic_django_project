import datetime

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.http import Http404
from django.urls import reverse_lazy

from . import forms
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView, DetailView, DeleteView

from .functions.specializations_list_display_functions import prepare_table_rows
from .models import Specialization, Doctor, Procedure, Visit, Patient, Term
from .functions.datetime_functions import get_week_start_and_end, get_weekdays_names
from .forms import RegisterFormUser, RegisterFormPatient, TermAddForm


class LandingPage(View):
    def get(self, request):
        return render(request, 'index.html')


class SpecializationList(ListView):
    model = Specialization
    template_name = 'specialization_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['specializations_matrix'] = prepare_table_rows(self.object_list, col=4)
        return context


class SpecializationDetails(DetailView):
    model = Specialization
    template_name = 'specialization_detail.html'

    def generate_terms(self, offset):
        start, end = get_week_start_and_end(offset)
        return [start + datetime.timedelta(days=n) for n in range(0, (end - start).days + 1)]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        spec_doctors = self.object.doctor_set.all().order_by('user__last_name').order_by('user__first_name')

        week_offset = 0 if self.request.GET.get('week') is None else int(self.request.GET.get('week'))
        context['offset'] = 0 if week_offset <= 0 else week_offset
        context['is_offset'] = context.get('offset') > 0

        dates_in_offset_week = self.generate_terms(context.get('offset'))
        week_terms = {}
        for spec_doctor in spec_doctors:
            temp = []
            for date in dates_in_offset_week:
                temp.append(spec_doctor.term_set.filter(date=date).order_by('date'))
            week_terms[spec_doctor] = temp

        context['doctor_week_terms'] = week_terms
        context['weekdays'] = get_weekdays_names(dates_in_offset_week)

        return context


class ProcedureList(ListView):
    model = Procedure
    template_name = 'procedure_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['procedures_matrix'] = prepare_table_rows(self.object_list, col=4)
        return context


class ProcedureDetails(DetailView):
    model = Procedure
    template_name = 'procedure_detail.html'


class DoctorDetails(DetailView):
    model = Doctor
    template_name = 'doctor_detail.html'


class VisitAdd(UserPassesTestMixin, View):
    login_url = reverse_lazy('login-page')

    def test_func(self):
        user = self.request.user
        return getattr(user, 'patient', False)

    def get(self, request, doc_id, date, hour):
        patient = get_object_or_404(Patient, user=request.user)
        doctor = get_object_or_404(Doctor, id=doc_id)
        date = get_object_or_404(Term, date=date, hour_from=hour)
        form = forms.AddVisitForm(initial={'doctor': doctor, 'date': date})

        procedures = doctor.procedures.all()
        if not procedures:
            raise Http404
        form.fields['procedure'].choices = [(procedure.id, procedure) for procedure in procedures]

        return render(request, 'visit_add.html', {'form': form, 'doctor': doctor, 'date': date, 'patient': patient})

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

            return redirect('user-visits')

        return render(request, 'visit_add.html', {'form': form})


class SignUpView(UserPassesTestMixin, View):

    def test_func(self):
        return not self.request.user.is_authenticated

    def handle_no_permission(self):
        return redirect('main-page')

    def get(self, request):
        form_user = RegisterFormUser
        form_patient = RegisterFormPatient
        return render(request, "registration/signup.html", {'form_user': form_user, 'form_patient': form_patient})

    def post(self, request):
        form_user = forms.RegisterFormUser(request.POST)
        form_patient = forms.RegisterFormPatient(request.POST)

        if form_user.is_valid():
            data = form_user.cleaned_data
            username = data.get('username')
            first_name = data.get('first_name')
            last_name = data.get('last_name')
            email = data.get('email')
            password = data.get('password1')

            if form_patient.is_valid():
                data = form_patient.cleaned_data
                pesel = data.get('pesel')
                identification_type = data.get('identification_type')
                phone_number = data.get('phone_number')

                user = User.objects.create(
                    is_superuser=0, username=username, email=email,
                    last_name=last_name, first_name=first_name
                )
                user.set_password(password)
                user.save()

                Patient.objects.create(
                                user=user, pesel=pesel,
                                identification_type=identification_type,
                                phone_number=phone_number
                )

                return redirect('login-page')

        return render(request, "registration/signup.html", {'form_user': form_user, 'form_patient': form_patient})


class UserVisits(LoginRequiredMixin, ListView):
    model = Visit
    template_name = 'patient_visits.html'
    login_url = reverse_lazy('login-page')

    def get_queryset(self):
        user = self.request.user

        if getattr(user, 'patient', False):
            patient = get_object_or_404(Patient, user=self.request.user)
            visits = Visit.objects.filter(patient=patient)
            return visits

        elif getattr(user, 'doctor', False):
            doctor = get_object_or_404(Doctor, user=self.request.user)
            visits = Visit.objects.filter(doctor=doctor)
            return visits


class VisitDetails(LoginRequiredMixin, DetailView):
    model = Visit
    template_name = 'visit_detail.html'
    login_url = reverse_lazy('login-page')


class VisitCancel(LoginRequiredMixin, DeleteView):
    model = Visit
    template_name = 'visit_delete.html'
    success_url = reverse_lazy('user-visits')
    login_url = reverse_lazy('login-page')


class TermAdd(UserPassesTestMixin, View):
    login_url = reverse_lazy('login-page')

    def test_func(self):
        user = self.request.user
        return getattr(user, 'doctor', False)

    def get(self, request):
        form = TermAddForm(user=request.user)
        return render(request, 'term_add.html', {'form': form})

    def post(self, request):
        doctor = get_object_or_404(Doctor, user=request.user)
        form = TermAddForm(request.POST, user=request.user)

        if form.is_valid():
            data = form.cleaned_data
            date = data.get('date')
            hour_from = data.get('hour_from')
            hour_to = data.get('hour_to')
            office = data.get('office')

            Term.objects.create(date=date, hour_from=hour_from, hour_to=hour_to, office=office, doctor=doctor)
            return redirect('specialization-detail', pk=doctor.specializations.all().first().id)

        return render(request, 'term_add.html', {'form': form})


class TermCancel(UserPassesTestMixin, DeleteView):
    model = Term
    template_name = 'term_delete.html'
    login_url = reverse_lazy('login-page')

    def test_func(self):
        user = self.request.user
        return getattr(user, 'doctor', False)

    def get_success_url(self):
        return reverse_lazy('specialization-detail', kwargs={'pk': self.object.doctor.specializations.all().first().id})