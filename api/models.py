from django.db import models

class User(models.Model):
    firebase_uid = models.CharField(max_length=128, unique=True)  # Store Firebase UID
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    contact_number = models.CharField(max_length=15)
    date_of_birth = models.DateField()
    address = models.TextField()
    blood_group = models.CharField(max_length=5)
    email_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email
    


class DoctorAvailability(models.Model):
    DocID = models.IntegerField()
    DocWeekday = models.CharField(max_length=20)
    DocAvailabilityID = models.IntegerField()
    Timeslot1 = models.CharField(max_length=50)
    Timeslot2 = models.CharField(max_length=50)
    Timeslot3 = models.CharField(max_length=50)

    def __str__(self):
        return f"Doctor {self.DocID} - {self.DocWeekday}"
    
class Appointment(models.Model):
    patient_name = models.CharField(max_length=100)
    doctor_id = models.IntegerField()
    date = models.DateField()
    time_slot = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.patient_name} - {self.date} - {self.time_slot}"