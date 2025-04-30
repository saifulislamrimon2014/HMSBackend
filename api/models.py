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