from django.urls import path
from .views import SaveUserData, GetUserData
from .views import GetDashboardData
from .views import GetAppointmentsData
from .views import GetPatientDashboardData
from .views import DoctorCardListAPIView
from django.conf import settings
from .views import DoctorAvailabilityView
from .views import GetAppointmentCount
from pymongo import MongoClient
from . import views
from .views import DoctorLoginView


urlpatterns = [
    path('save-user/', SaveUserData.as_view(), name='save-user'),
    path('user/<str:firebase_uid>/', GetUserData.as_view(), name='get-user'),
    path('api/dashboard/', GetDashboardData.as_view(), name='dashboard_view'),
    path('appointments/', GetAppointmentsData.as_view(), name='get_appointments'),
    path('api/patient-dashboard/', GetPatientDashboardData.as_view(), name='get_patient_dashboard_data'),
    path('api/doctor-cards/', DoctorCardListAPIView.as_view(), name='doctor_cards'),

    path('availability/<int:doc_id>/<str:weekday>/', DoctorAvailabilityView.as_view(), name='doctor-availability'),
    path('api/appointments/count/<int:doc_id>/<str:date>/', GetAppointmentCount.as_view(), name='get_appointment_count'),
    path('doctor-login/', DoctorLoginView.as_view(), name='doctor-login'),
    
]
    
    



