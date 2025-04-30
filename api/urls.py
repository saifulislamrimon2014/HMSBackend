from django.urls import path
from .views import SaveUserData, GetUserData
from .views import get_dashboard_data


urlpatterns = [
    path('save-user/', SaveUserData.as_view(), name='save-user'),
    path('user/<str:firebase_uid>/', GetUserData.as_view(), name='get-user'),
    path('api/dashboard/', get_dashboard_data),

]
