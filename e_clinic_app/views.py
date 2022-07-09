import datetime

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.contrib.auth.views import PasswordChangeView
from django.contrib.messages.views import SuccessMessageMixin
from django.http import Http404
from django.urls import reverse_lazy

from . import forms
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView, DetailView, DeleteView

from .functions.specializations_list_display_functions import prepare_table_rows
from .models import Specialization, Doctor, Procedure, Visit, Patient, Term
from .functions.datetime_functions import get_week_start_and_end, get_weekdays_names
from .forms import RegisterFormUser, RegisterFormPatient, TermAddForm, MultipleTermAddForm, EditFormUser


class LandingPage(View):
    """Main page of web_app with access through navbar to other views."""

    def get(self, request):
        return render(request, 'index.html')


class SpecializationList(ListView):
    """List (in form of matrix) of specialization with urls which leads to views which contain details about itself."""
    model = Specialization
    template_name = 'specialization_list.html'

    def get_context_data(self, **kwargs):
        """Method transform queryset into list of lists (matrix)"""
        context = super().get_context_data(**kwargs)
        context['specializations_matrix'] = prepare_table_rows(self.object_list, col=4)
        return context


class SpecializationDetails(DetailView):
    """
    This view displays urls with terms grouped by doctors with this specialization. Depending on user status
    (doctor or patient) urls leads to AddVisitView or TermCancelView. View allows to paginate to next weeks and back to
    current week.
    """
    model = Specialization
    template_name = 'specialization_detail.html'

    def generate_terms(self, offset):
        """Method generate weekdays dates based on week offset (for example next week => 1, 2 weeks after => 2 etc.)"""
        start, end = get_week_start_and_end(offset)
        return [start + datetime.timedelta(days=n) for n in range(0, (end - start).days + 1)]

    def get_context_data(self, **kwargs):
        """
        Method take week offset as integer argument to get terms of specialization's doctors for the selected week.
        """
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
    """List (in form of matrix) of procedures with urls which leads to views which contain details about itself."""
    model = Procedure
    template_name = 'procedure_list.html'

    def get_context_data(self, **kwargs):
        """Method transform queryset into list of lists (matrix)."""
        context = super().get_context_data(**kwargs)
        context['procedures_matrix'] = prepare_table_rows(self.object_list, col=4)
        return context


class ProcedureDetails(DetailView):
    """List of procedure's details f.e. price, performed by doctors..."""
    model = Procedure
    template_name = 'procedure_detail.html'


class DoctorDetails(DetailView):
    """List of doctor's details f.e. specializations, pwz number..."""
    model = Doctor
    template_name = 'doctor_detail.html'


class VisitAdd(UserPassesTestMixin, View):
    """
    View allows to make an appointment by a logged-in patient, based on term she/he selected (displayed as url)
    in SpecializationDetailView.
    """
    login_url = reverse_lazy('login-page')

    def test_func(self):
        """Method checks if logged-in user is patient."""
        user = self.request.user
        return getattr(user, 'patient', False)

    def get(self, request, doc_id, date, hour):
        """Method gets data from url parameters. Rendered form ask only for procedure choice."""
        patient = get_object_or_404(Patient, user=request.user)
        doctor = get_object_or_404(Doctor, id=doc_id)
        date = get_object_or_404(Term, doctor=doctor, date=date, hour_from=hour)
        form = forms.AddVisitForm(initial={'doctor': doctor, 'date': date})

        procedures = doctor.procedures.all()
        if not procedures:
            raise Http404
        form.fields['procedure'].choices = [(procedure.id, procedure) for procedure in procedures]

        return render(request, 'visit_add.html', {'form': form, 'doctor': doctor, 'date': date, 'patient': patient})

    def post(self, request, doc_id, date, hour):
        """Method creates Visit object."""
        user = request.user
        patient = get_object_or_404(Patient, user=user)
        doctor = get_object_or_404(Doctor, id=doc_id)
        date = get_object_or_404(Term, doctor=doctor, date=date, hour_from=hour)
        form = forms.AddVisitForm(request.POST)

        if form.is_valid():
            data = form.cleaned_data
            procedure = data.get('procedure')

            Visit.objects.create(patient=patient, doctor=doctor, date=date, procedure=procedure)

            messages.success(request, "Appointment was made successfully.")
            return redirect('user-visits')

        return render(request, 'visit_add.html', {'form': form})


class SignUpView(UserPassesTestMixin, View):
    """View allows to create patient account (Patient object and related with it User object)."""

    def test_func(self):
        return not self.request.user.is_authenticated

    def handle_no_permission(self):
        """Method redirects to main page if user is already logged-in"""
        return redirect('main-page')

    def get(self, request):
        """Method render Sign Up form (combined user register form with patient register form)"""
        form_user = RegisterFormUser
        form_patient = RegisterFormPatient
        return render(request, "registration/signup.html", {'form_user': form_user, 'form_patient': form_patient})

    def post(self, request):
        """Method creates both User and Patient object. Both related to each other."""
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

                messages.success(request, "Thank you for joining. Now you can log in.")
                return redirect('login-page')

        return render(request, "registration/signup.html", {'form_user': form_user, 'form_patient': form_patient})


class EditUserView(UserPassesTestMixin, View):
    """
    View allows patients to edit their details excluding password. Editng doctors their details by themselves
    is forbiden and must be done in Django Admin.
    """

    def test_func(self):
        user = self.request.user
        return getattr(user, 'patient', False)

    def handle_no_permission(self):
        """Method redirects to main page if user is not a patient"""
        return redirect('login-page')

    def get(self, request):
        """Method render Edit User form (combined user register form with patient register form) with initial values."""
        form_user = EditFormUser
        form_patient = RegisterFormPatient
        user = self.request.user
        patient = user.patient

        context = {
            'form_user': form_user(instance=user),
            'form_patient': form_patient(instance=patient)
        }

        return render(request, "registration/edit_user.html", context)

    def post(self, request):
        """
        Method changes both User and Patient objects attributes values for values from submitted form and save them.
        """
        form_user = forms.EditFormUser(request.POST, instance=request.user)
        form_patient = forms.RegisterFormPatient(request.POST, instance=request.user.patient)
        user = request.user

        if form_user.is_valid():
            data = form_user.cleaned_data
            user.username = data.get('username')
            user.first_name = data.get('first_name')
            user.last_name = data.get('last_name')
            user.email = data.get('email')

            if form_patient.is_valid():
                data = form_patient.cleaned_data
                patient = user.patient
                patient.pesel = data.get('pesel')
                patient.identification_type = data.get('identification_type')
                patient.phone_number = data.get('phone_number')

                user.save()
                patient.save()

                login(request, user)

                messages.success(request, "Your account details have been changed successfully.")
                return redirect('main-page')

        return render(request, "registration/edit_user.html", {'form_user': form_user, 'form_patient': form_patient})


class UserVisits(LoginRequiredMixin, ListView):
    """View alows both logged-in patient and doctors to see their planned visit"""
    model = Visit
    template_name = 'patient_visits.html'
    login_url = reverse_lazy('login-page')

    def get_queryset(self):
        """
        Method allows to display appropriate set of views:
        - for patient, their own visits
        -for doctors, their patients visits
        """
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
    """View display details of visit: term, doctor and place of it"""
    model = Visit
    template_name = 'visit_detail.html'
    login_url = reverse_lazy('login-page')


class VisitCancel(LoginRequiredMixin, DeleteView):
    """Views allows both patient and doctors to cancel their visits"""
    model = Visit
    success_url = reverse_lazy('user-visits')
    login_url = reverse_lazy('login-page')
    template_name = 'visit_delete.html'
    success_message = "Visit was canceled successfully."

    def delete(self, request, *args, **kwargs):
        """Method enables to show succes message after deleting object"""
        messages.success(self.request, self.success_message)
        return super(VisitCancel, self).delete(request, *args, **kwargs)


class TermAdd(UserPassesTestMixin, View):
    """View allows doctors to add Term objets (single at one time)."""
    login_url = reverse_lazy('login-page')

    def test_func(self):
        """Method checks if logged-in usser is doctor."""
        user = self.request.user
        return getattr(user, 'doctor', False)

    def get(self, request):
        """Method renders Add Term Form."""
        form = TermAddForm(user=request.user)
        return render(request, 'term_add.html', {'form': form})

    def post(self, request):
        """Method creates single Term Object."""
        doctor = get_object_or_404(Doctor, user=request.user)
        form = TermAddForm(request.POST, user=request.user)

        if form.is_valid():
            data = form.cleaned_data
            date = data.get('date')
            hour_from = data.get('hour_from')
            hour_to = data.get('hour_to')
            office = data.get('office')

            Term.objects.create(date=date, hour_from=hour_from, hour_to=hour_to, office=office, doctor=doctor)
            messages.success(request, "Term was added successfully.")
            return redirect('specialization-detail', pk=doctor.specializations.all().first().id)

        return render(request, 'term_add.html', {'form': form})


class TermCancel(SuccessMessageMixin, UserPassesTestMixin, DeleteView):
    """View allows doctors to cancel (delete Term object)."""
    model = Term
    template_name = 'term_delete.html'
    login_url = reverse_lazy('login-page')
    success_message = "Term was canceled successfully."

    def test_func(self):
        """Method checks if logged-in usser is doctor."""
        user = self.request.user
        return getattr(user, 'doctor', False)

    def get_success_url(self):
        """Method redirects to doctor's specialization detail ciew after successfully deleting of term."""
        return reverse_lazy('specialization-detail', kwargs={'pk': self.object.doctor.specializations.first().id})

    def delete(self, request, *args, **kwargs):
        """Method enables to show succes message after deleting object"""
        messages.success(self.request, self.success_message)
        return super(TermCancel, self).delete(request, *args, **kwargs)


class MultipleTermAdd(UserPassesTestMixin, View):
    """
    View is extended version of TermAddView and allows to add multiple terms at one time, basing on interval of time
    (hour when doctor starts the work and hour when doctor ends the work) and time lenght of visit.
    """
    login_url = reverse_lazy('login-page')

    def test_func(self):
        """Method checks if logged-in usser is doctor."""
        user = self.request.user
        return getattr(user, 'doctor', False)

    def get(self, request):
        """Method renders form which is extension of TermAddForm and has an additional field "visit time"."""
        form = MultipleTermAddForm(user=request.user)
        return render(request, 'multiple_term_add.html', {'form': form})

    def post(self, request):
        """Methods create multiple Term object basing on doctor's day work hours and visit time length"""
        doctor = get_object_or_404(Doctor, user=request.user)
        form = MultipleTermAddForm(request.POST, user=request.user)

        if form.is_valid():
            data = form.cleaned_data
            date = data.get('date')
            hour_from = data.get('hour_from')
            hour_to = data.get('hour_to')
            office = data.get('office')
            visit_time = int(data.get('visit_time'))

            day_hour_to = datetime.datetime.combine(date.today(), hour_to)
            day_hour_from = datetime.datetime.combine(date.today(), hour_from)
            minutes = (day_hour_to - day_hour_from).total_seconds() / 60.0

            for _ in range(int(minutes / visit_time)):
                final_time = day_hour_from + datetime.timedelta(minutes=visit_time)
                Term.objects.create(
                    date=date, hour_from=day_hour_from.time(), hour_to=final_time.time(), office=office, doctor=doctor
                )
                day_hour_from = final_time

            messages.success(request, "Terms was added successfully.")
            return redirect('specialization-detail', pk=doctor.specializations.all().first().id)

        return render(request, 'multiple_term_add.html', {'form': form})


class CustomPasswordChangeView(SuccessMessageMixin, LoginRequiredMixin, PasswordChangeView):
    """View allows users to change their passwords"""
    form_class = PasswordChangeForm
    login_url = reverse_lazy('login-page')
    template_name = 'change-password.html'
    success_message = "Password was changed successfully. Now you can log in with your new password."

    def get_success_url(self):
        """Method forces loggin-out users accaouts and redirects to log-in View"""
        logout(self.request)
        return reverse_lazy('login-page')
