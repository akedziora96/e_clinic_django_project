from e_clinic_app.models import Specialization


def specializations_ctxp(request):
  context = {
    "specializations_ctxp": Specialization.objects.all()
  }
  return context

