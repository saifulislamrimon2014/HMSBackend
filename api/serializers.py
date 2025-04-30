from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['firebase_uid', 'first_name', 'last_name', 'email', 'contact_number', 'date_of_birth', 'address', 'blood_group', 'email_verified']