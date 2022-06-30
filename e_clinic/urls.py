"""e_clinic URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from e_clinic_app import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.LandingPage.as_view(), name="main-page"),
    path('specializations/', views.SpecializationList.as_view(), name="specializations"),
    path('specialization/<int:pk>/', views.SpecializationDetails.as_view(), name="specialization-detail"),
    path('procedures/', views.ProcedureList.as_view(), name="procedures"),
    path('procedure/<int:pk>/', views.ProcedureDetails.as_view(), name="procedure-detail"),
    path('doctor/<int:pk>/', views.DoctorDetails.as_view(), name="doctor-detail"),
    path('register_visit/<int:doc_id>/<str:date>/<str:hour>/', views.VisitAdd.as_view(), name="register_visit"),
]
