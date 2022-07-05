import datetime

from django.contrib.auth.models import User, AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

IDENTIFICATION = [
    (1, "ID card"),
    (2, "Passport"),
]

TITLES = [
    (1, "lek."),
    (2, "lek. dent"),
    (3, "dr n. med."),
    (4, "dr hab. n. med."),
    (5, "prof. dr hab. n. med.")
]


class Person(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    pesel = models.IntegerField(unique=True, verbose_name="PESEL (polish ID number)")

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"

    @property
    def name(self):
        return f"{self.user.first_name} {self.user.last_name}"

    # @property
    # def date_of_birth(self):
    #     pesel = str(self.pesel)
    #     time_data = f"{pesel[2:4]}-{pesel[4:6]}-{pesel[0:2]}"
    #     format_data = "%d-%m-%y"
    #     return datetime.datetime.strptime(time_data, format_data)


class Patient(Person):
    identification_type = models.IntegerField(choices=IDENTIFICATION, verbose_name="identification type")
    phone_number = models.CharField(max_length=11, unique=True, verbose_name="phone number")


class Specialization(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="specialization name")

    def __str__(self):
        return self.name


class Procedure(models.Model):
    name = models.CharField(max_length=60, unique=True, verbose_name="treatment name")
    price = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="treatment price")

    def __str__(self):
        return f"{self.name} ({self.price} PLN)"


class Doctor(Person):
    pwz = models.IntegerField(unique=True, verbose_name="PWZ (doctor's license")
    specializations = models.ManyToManyField(Specialization, verbose_name="Specialization")
    title_or_degree = models.IntegerField(
        choices=TITLES, verbose_name="Scientific degree"
    )
    procedures = models.ManyToManyField(Procedure, verbose_name="Treatments performed by doctor")


class Office(models.Model):
    number = models.IntegerField(unique=True, validators=[MinValueValidator(0)], verbose_name="Office Number")

    def is_free(self, date):
        return not Term.objects.filter(office=self, date=date).exists()

    def __str__(self):
        return f"{self.number}"


class Term(models.Model):
    date = models.DateField(verbose_name="Day's date")
    hour_from = models.TimeField(verbose_name="From hour")
    hour_to = models.TimeField(verbose_name="To hour")
    doctor = models.ForeignKey(Doctor, verbose_name="Doctor", on_delete=models.CASCADE)
    office = models.ForeignKey(Office, on_delete=models.CASCADE, verbose_name="Office")

    class Meta:
        unique_together = ['date', 'hour_from', 'hour_to', 'office']

    @property
    def visit_hour(self):
        return f"{self.hour_from.strftime('%H:%M')}"

    def is_from_past(self):
        if self.date < datetime.date.today():
            return True
        elif self.date == datetime.date.today() and self.hour_from < datetime.datetime.now().time():
            return True
        else:
            return False

    def is_available(self):
        return not self.visit_set.exists() and not self.is_from_past()

    def __str__(self):
        return f"{self.date}, {self.hour_from}, {self.hour_to}"

    def find_visit(self):
        return self.visit_set.all().first().id


class Visit(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, verbose_name="Patient")
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, verbose_name="Doctor")
    date = models.ForeignKey(Term, on_delete=models.CASCADE, verbose_name="Visit term")
    procedure = models.ForeignKey(Procedure, on_delete=models.CASCADE, verbose_name="Chosen treatment")

    def __str__(self):
        return f"{self.date} {self.patient} u {self.doctor.get_title_or_degree_display()} {self.doctor}"


