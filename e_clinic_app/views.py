import datetime

from django.contrib.auth.models import User
from django.http import HttpResponse, Http404
from django.urls import reverse_lazy

from . import forms
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, DeleteView
from e_clinic_app.models import Specialization, Doctor, Procedure, Visit, Patient, Term
from .datetime_functions import get_week_start_and_end, get_weekdays_names
from .forms import RegisterFormUser, RegisterFormPatient, TermAddForm


class LandingPage(View):
    def get(self, request):
        return render(request, 'index.html')


class SpecializationList(ListView):
    model = Specialization
    template_name = 'specialization_list.html'


class SpecializationDetails(DetailView):
    model = Specialization
    template_name = 'specialization_detail.html'

    def generate_terms(self, offset):
        start, end = get_week_start_and_end(offset)
        return [start + datetime.timedelta(days=n) for n in range(0, (end - start).days + 1)]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        spec_doctors = self.object.doctor_set.all().order_by('user__last_name').order_by('user__first_name')

        week_offset = self.request.GET.get('week')
        week_offset_session = self.request.session.get('week_offset')
        if week_offset is not None and week_offset_session is not None:
            if week_offset == 'next':
                self.request.session['week_offset'] += 1
            if week_offset == 'previous' and week_offset_session > 0:
                self.request.session['week_offset'] -= 1
        else:
            self.request.session['week_offset'] = 0

        dates_in_offset_week = self.generate_terms(self.request.session['week_offset'])

        week_terms = {}
        for spec_doctor in spec_doctors:
            temp = []
            for date in dates_in_offset_week:
                temp.append(spec_doctor.term_set.filter(date=date).order_by('date'))
            week_terms[spec_doctor] = temp

        context['doctor_week_terms'] = week_terms
        context['weekdays'] = get_weekdays_names(dates_in_offset_week)
        context['is_offset'] = self.request.session.get('week_offset') > 0

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
    pass

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

            patient_user = forms.RegisterFormPatient(request.POST)

            if patient_user.is_valid():
                data = patient_user.cleaned_data
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


class UserVisits(ListView):
    model = Visit
    template_name = 'patient_visits.html'

    def get_queryset(self):
        user = self.request.user
        print(getattr(user, 'doctor', None))
        if getattr(user, 'patient', None):
            patient = get_object_or_404(Patient, user=self.request.user)
            visits = Visit.objects.filter(patient=patient)
            return visits

        elif getattr(user, 'doctor', None):
            doctor = get_object_or_404(Doctor, user=self.request.user)
            visits = Visit.objects.filter(doctor=doctor)
            return visits


class VisitDetails(DetailView):
    model = Visit
    template_name = 'visit_detail.html'


class VisitCancel(DeleteView):
    model = Visit
    template_name = 'visit_delete.html'
    success_url = reverse_lazy('user-visits')


class TermAdd(View):
    pass

    def get(self, request):
        form = TermAddForm()
        # form_expansion = TermAddFormExpansion()
        return render(request, 'term_add.html', {'form': form})

    def post(self, request):
        doctor = get_object_or_404(Doctor, user=self.request.user)

        form = TermAddForm(request.POST)
        # form_expansion = TermAddFormExpansion(request.POST)

        add_option = request.POST.get('add_option')

        if form.is_valid():
            data = form.cleaned_data
            date = data.get('date')
            hour_from = data.get('hour_from')
            hour_to = data.get('hour_to')
            office = data.get('office')

            # if form_expansion.is_valid():
            #     data = form_expansion.cleaned_data
            #     visit_time = data.get('visit_time')

            possible_term = Term.objects.filter(date=date)
            pt = possible_term.filter(hour_from__lte=hour_from, hour_to__gte=hour_to)
            pt |= possible_term.filter(hour_from__lte=hour_from, hour_to__gt=hour_from,  hour_to__lte=hour_to)
            pt |= possible_term.filter(hour_from__gte=hour_from, hour_from__lte=hour_to, hour_to__gte=hour_to)
            pt |= possible_term.filter(hour_from__gte=hour_from, hour_to__lte=hour_to)
            pt2 = pt.filter(office=office)
            pt2 |= pt.filter(doctor=doctor)

            if not pt2.exists():
                Term.objects.create(date=date, hour_from=hour_from, hour_to=hour_to, office=office, doctor=doctor)
                return redirect('main-page')

        message = "gabinet zajęty"
        return render(request, 'term_add.html', {'form': form, "message": message})


