import datetime

from django.contrib.auth.models import User, AbstractUser
from django.core.validators import MinValueValidator
from django.db import models

IDENTIFICATION = [
    (1, "Dowód tożsamości"),
    (2, "Paszport"),
    (3, "Akt urodzenia*")
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
    pesel = models.IntegerField(unique=True, verbose_name="PESEL")

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"

    @property
    def name(self):
        return f"{self.user.first_name} {self.user.last_name}"

    @property
    def date_of_birth(self):
        pesel = str(self.pesel)
        time_data = f"{pesel[2:4]}-{pesel[4:6]}-{pesel[0:2]}"
        format_data = "%d-%m-%y"
        return datetime.datetime.strptime(time_data, format_data)


class Patient(Person):
    identification_type = models.IntegerField(choices=IDENTIFICATION, verbose_name="dowód tożsamości")
    phone_number = models.IntegerField(unique=True, verbose_name="Telefon komórkowy")


class Specialization(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Specjalizacja")

    @property
    def clinic(self):
        return f"{self.name[:-1]}czna"

    def __str__(self):
        return self.name


class Procedure(models.Model):
    name = models.CharField(max_length=60, unique=True, verbose_name="Nazwa Zabiegu")
    price = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="Koszt zabiegu")

    def __str__(self):
        return f"{self.name} ({self.price} zł)"


class Doctor(Person):
    pwz = models.IntegerField(unique=True, verbose_name="PWZ")
    specializations = models.ManyToManyField(Specialization, verbose_name="Specjalizacja")
    title_or_degree = models.IntegerField(
        choices=TITLES, verbose_name="Tytuł zawodowy, stopień naukowy bądź tytuł naukowy"
    )
    procedures = models.ManyToManyField(Procedure, verbose_name="Zabiegi wykonywane przez lekarza")


class Office(models.Model):
    number = models.IntegerField(unique=True, validators=[MinValueValidator(0)], verbose_name="Nr gabinetu")

    def is_free(self, date):
        return not Term.objects.filter(office=self, date=date).exists()

    def __str__(self):
        return f"{self.number}"


class Term(models.Model):
    date = models.DateField(verbose_name="Dzień")
    hour_from = models.TimeField(verbose_name="Od godziny")
    hour_to = models.TimeField(verbose_name="Do godziny")
    doctor = models.ForeignKey(Doctor, verbose_name="Lekarz", on_delete=models.CASCADE)
    office = models.ForeignKey(Office, on_delete=models.CASCADE, verbose_name="Gabinet")

    class Meta:
        unique_together = ['date', 'hour_from', 'hour_to', 'office']

    @property
    def visit_hour(self):
        return f"{self.hour_from.strftime('%H:%M')}"

    def is_available(self):
        if self.visit_set.all().exists():
            return False

        if self.date > datetime.date.today():
            return True
        elif self.date == datetime.date.today():
            if self.hour_from >= datetime.datetime.now().time():
                return True

        return False

    def __str__(self):
        return f"{self.date}, {self.hour_from}, {self.hour_to}"


class Visit(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, verbose_name="Pacjent")
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, verbose_name="Lekarz")
    date = models.ForeignKey(Term, on_delete=models.CASCADE, verbose_name="Termin wizyty")
    procedure = models.ForeignKey(Procedure, on_delete=models.CASCADE, verbose_name="Wybrany zabieg")

    def __str__(self):
        return f"{self.date} {self.patient} u {self.doctor.get_title_or_degree_display()} {self.doctor}"


