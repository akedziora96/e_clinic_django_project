from django.contrib import admin
from . import models

admin.site.register(models.Patient)
admin.site.register(models.Doctor)
admin.site.register(models.Specialization)
admin.site.register(models.Office)
admin.site.register(models.Procedure)
admin.site.register(models.Term)
admin.site.register(models.Visit)
