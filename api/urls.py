from django.urls import path
from .views import SaveUserData, GetUserData
from .views import GetDashboardData
from .views import GetAppointmentsData
from .views import GetPatientDashboardData
from .views import GetPatientAppointments
from .views import DoctorCardListAPIView
from django.conf import settings
from .views import DoctorAvailabilityView
from .views import GetAppointmentCount
from pymongo import MongoClient
from . import views
from .views import DoctorLoginView
from .views import GetTechnologistList, AddTechnologist, UpdateTechnologist, DeleteTechnologist, TechnologistLoginView
from .views import GetAccountantList, AddAccountant, UpdateAccountant, DeleteAccountant, AccountantLoginView
from .views import GetInventoryList, AddInventoryItem, UpdateInventoryItem, DeleteInventoryItem
from .views import GetDoctorList, AddDoctor, UpdateDoctor, DeleteDoctor
from .views import GetDoctorAvailability, AddDoctorAvailability, UpdateDoctorAvailability, DeleteDoctorAvailability
from .views import AdminLoginView
from .views import GetPatientList, UpdatePatient, DeletePatient
from .views import GetReportList, AddReport, UpdateReport, DeleteReport
from .views import GetConfirmedReportList, DeliverReport


urlpatterns = [
    path('save-user/', SaveUserData.as_view(), name='save-user'),
    path('user/<str:firebase_uid>/', GetUserData.as_view(), name='get-user'),
    path('api/dashboard/', GetDashboardData.as_view(), name='dashboard_view'),
    path('appointments/', GetAppointmentsData.as_view(), name='get_appointments'),
    path('patient-appointments/<str:firebase_uid>/', GetPatientAppointments.as_view(), name='get_patient_appointments'),
    path('api/patient-dashboard/', GetPatientDashboardData.as_view(), name='get_patient_dashboard_data'),
    path('api/doctor-cards/', DoctorCardListAPIView.as_view(), name='doctor_cards'),

    path('availability/<int:doc_id>/<str:weekday>/', DoctorAvailabilityView.as_view(), name='doctor-availability'),
    path('api/appointments/count/<int:doc_id>/<str:date>/', GetAppointmentCount.as_view(), name='get_appointment_count'),
    path('doctor-login/', DoctorLoginView.as_view(), name='doctor-login'),

    # Technologist API endpoints
    path('technologists/', GetTechnologistList.as_view(), name='get_technologists'),
    path('technologists/add/', AddTechnologist.as_view(), name='add_technologist'),
    path('technologists/update/<str:tech_id>/', UpdateTechnologist.as_view(), name='update_technologist'),
    path('technologists/delete/<str:tech_id>/', DeleteTechnologist.as_view(), name='delete_technologist'),

    # Accountant API endpoints
    path('accountants/', GetAccountantList.as_view(), name='get_accountants'),
    path('accountants/add/', AddAccountant.as_view(), name='add_accountant'),
    path('accountants/update/<str:acc_id>/', UpdateAccountant.as_view(), name='update_accountant'),
    path('accountants/delete/<str:acc_id>/', DeleteAccountant.as_view(), name='delete_accountant'),

    # Inventory API endpoints
    path('inventory/', GetInventoryList.as_view(), name='get_inventory'),
    path('inventory/add/', AddInventoryItem.as_view(), name='add_inventory_item'),
    path('inventory/update/<str:item_id>/', UpdateInventoryItem.as_view(), name='update_inventory_item'),
    path('inventory/delete/<str:item_id>/', DeleteInventoryItem.as_view(), name='delete_inventory_item'),

    # Doctor API endpoints
    path('doctors/', GetDoctorList.as_view(), name='get_doctors'),
    path('doctors/add/', AddDoctor.as_view(), name='add_doctor'),
    path('doctors/update/<str:doc_id>/', UpdateDoctor.as_view(), name='update_doctor'),
    path('doctors/delete/<str:doc_id>/', DeleteDoctor.as_view(), name='delete_doctor'),

    # Doctor Availability API endpoints
    path('doctor-availability/<int:doc_id>/', GetDoctorAvailability.as_view(), name='get_doctor_availability'),
    path('doctor-availability/add/', AddDoctorAvailability.as_view(), name='add_doctor_availability'),
    path('doctor-availability/update/<str:availability_id>/', UpdateDoctorAvailability.as_view(), name='update_doctor_availability'),
    path('doctor-availability/delete/<str:availability_id>/', DeleteDoctorAvailability.as_view(), name='delete_doctor_availability'),

    # Patient API endpoints
    path('patients/', GetPatientList.as_view(), name='get_patients'),
    path('patients/update/<str:patient_id>/', UpdatePatient.as_view(), name='update_patient'),
    path('patients/delete/<str:patient_id>/', DeletePatient.as_view(), name='delete_patient'),

    # Report API endpoints
    path('reports/', GetReportList.as_view(), name='get_reports'),
    path('reports/add/', AddReport.as_view(), name='add_report'),
    path('reports/update/<str:report_id>/', UpdateReport.as_view(), name='update_report'),
    path('reports/delete/<str:report_id>/', DeleteReport.as_view(), name='delete_report'),

    # Confirmed Report API endpoints
    path('confirmed-reports/', GetConfirmedReportList.as_view(), name='get_confirmed_reports'),
    path('reports/deliver/', DeliverReport.as_view(), name='deliver_report'),

    # Login endpoints
    path('technologist-login/', TechnologistLoginView.as_view(), name='technologist-login'),
    path('accountant-login/', AccountantLoginView.as_view(), name='accountant-login'),
    path('admin-login/', AdminLoginView.as_view(), name='admin-login'),
]





