import datetime

from django.contrib.auth.models import User, AbstractUser
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.db import models

from e_clinic_app.validators import phone_regex_validator, pesel_validator, pwz_validator, date_validator

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
    """Abstract parent model for Doctor and Patient."""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    pesel = models.CharField(
        max_length=11, unique=True, verbose_name="PESEL (polish ID number)", validators=[pesel_validator]
    )

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"

    @property
    def name(self):
        """Method displays Person fullname which contains User model values 'firs_name' and 'last_name'."""
        return f"{self.user.first_name} {self.user.last_name}"


class Patient(Person):
    """Represents patient."""
    identification_type = models.IntegerField(choices=IDENTIFICATION, verbose_name="identification type")
    phone_number = models.CharField(
        max_length=15, unique=True, verbose_name="phone number", validators=[phone_regex_validator]
    )


class Specialization(models.Model):
    """Represents medical specializations which can be hold by a doctor."""
    name = models.CharField(max_length=100, unique=True, verbose_name="specialization name")

    def __str__(self):
        return self.name


class Procedure(models.Model):
    """Represents medical treatment which can be performed by a doctor on a patient."""
    name = models.CharField(max_length=60, unique=True, verbose_name="treatment name")
    price = models.DecimalField(
        max_digits=6, decimal_places=2, verbose_name="treatment price", validators=[MinValueValidator(0)]
    )

    def __str__(self):
        return f"{self.name} ({self.price} PLN)"


class Doctor(Person):
    """Represents doctor."""
    pwz = models.IntegerField(unique=True, verbose_name="PWZ (doctor's license", validators=[pwz_validator])
    specializations = models.ManyToManyField(Specialization, verbose_name="Specialization")
    title_or_degree = models.IntegerField(
        choices=TITLES, verbose_name="Scientific degree"
    )
    procedures = models.ManyToManyField(Procedure, verbose_name="Treatments performed by doctor")


class Office(models.Model):
    """Represents the room where patient's visit takes place."""
    number = models.IntegerField(unique=True, validators=[MinValueValidator(0)], verbose_name="Office Number")

    def is_free(self, date):
        return not Term.objects.filter(office=self, date=date).exists()

    def __str__(self):
        return f"{self.number}"


class Term(models.Model):
    """Represents the complex info: term, doctor and place where and when patient's visit can take place."""
    date = models.DateField(verbose_name="Day's date", validators=[date_validator])
    hour_from = models.TimeField(verbose_name="From hour")
    hour_to = models.TimeField(verbose_name="To hour")
    doctor = models.ForeignKey(Doctor, verbose_name="Doctor", on_delete=models.CASCADE)
    office = models.ForeignKey(Office, on_delete=models.CASCADE, verbose_name="Office")

    class Meta:
        """Meta doesn't allow to create a (possible) term with the same office."""
        unique_together = ['date', 'hour_from', 'hour_to', 'office']

    @property
    def visit_hour(self):
        """Method allows to display time without seconds."""
        return f"{self.hour_from.strftime('%H:%M')}"

    def is_from_past(self):
        """
        Method checks if term is form the past by comparison of actual date and time with the same
        values of Term object.
        """
        if self.date < datetime.date.today():
            return True
        elif self.date == datetime.date.today() and self.hour_from < datetime.datetime.now().time():
            return True
        else:
            return False

    def is_available(self):
        """Method checks if there's no visit on this term and date is from the past."""
        return not self.visit_set.exists() and not self.is_from_past()

    def __str__(self):
        return f"{self.date}, {self.hour_from}, {self.hour_to}"

    def find_visit(self):
        """Method Allows to find a Visit object (by primary key) related to term itself."""
        return self.visit_set.first().id


class Visit(models.Model):
    """Represent information about patient's visit through relations between models"""
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, verbose_name="Patient")
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, verbose_name="Doctor")
    date = models.ForeignKey(Term, on_delete=models.CASCADE, verbose_name="Visit term")
    procedure = models.ForeignKey(Procedure, on_delete=models.CASCADE, verbose_name="Chosen treatment")

    def __str__(self):
        return f"{self.date} {self.patient} u {self.doctor.get_title_or_degree_display()} {self.doctor}"


