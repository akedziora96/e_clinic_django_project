import datetime

from django.http import HttpResponse, Http404
from . import forms
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView, DetailView, CreateView
from e_clinic_app.models import Specialization, Doctor, Procedure, Term, Visit

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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        spec_doctors = self.object.doctor_set.all()

        start = datetime.datetime.strptime("27-06-2022", "%d-%m-%Y")
        end = datetime.datetime.strptime("03-07-2022", "%d-%m-%Y")
        date_generated = [start + datetime.timedelta(days=n) for n in range(0, (end-start).days)]

        weekdays = {WEEKDAYS[date.weekday()+1]: date.strftime("%d.%m") for date in date_generated}
        context['weekdays'] = weekdays

        # week_schedule = {spec_doctor: [spec_doctor.schedule.filter(date=date).first() for date in date_generated]
        #                  for spec_doctor in spec_doctors}
        # context['doctor_week_schedule'] = week_schedule

        week_terms = {}
        for spec_doctor in spec_doctors:
            temp = []
            for date in date_generated:
                temp.append(spec_doctor.terms.filter(date=date))
            week_terms[spec_doctor] = temp

        for key, value in week_terms.items():
            for set in value:
                for term in set:
                    print(term.hour_from, datetime.datetime.now().time())

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
        form = forms.AddVisitForm()

        doctor_qs = Doctor.objects.filter(id=doc_id)
        form.fields['doctor'].choices = [(doctor.id, doctor) for doctor in doctor_qs]
        date_qs = Term.objects.filter(date=date, hour_from=hour)
        # form.fields['date'].choices = [(date.id, date) for date in date_qs]
        procedures = doctor_qs.first().procedures.all()
        form.fields['procedure'].choices = [(procedure.id, procedure) for procedure in procedures]

        if not (date_qs and procedures):
            raise Http404

        return render(request, 'visit_add.html', {'form': form})

    def post(self, request, doc_id, date, hour):
        doctor = get_object_or_404(Doctor, id=doc_id)
        date = get_object_or_404(Term, date=date, hour_from=hour)
        form = forms.AddVisitForm(request.POST)

        if form.is_valid():
            data = form.cleaned_data
            patient = data.get('patient')
            procedure = data.get('procedure')

            Visit.objects.create(patient=patient, doctor=doctor, date=date, procedure=procedure)

            return redirect('main-page')

        return HttpResponse('Śwignij jakimś błędem')