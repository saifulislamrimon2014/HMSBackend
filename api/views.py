from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from pymongo import MongoClient
from django.conf import settings
import certifi
from rest_framework.decorators import api_view
import os
from django.http import JsonResponse
from rich import _console
from .models import DoctorAvailability
from .models import Appointment
from datetime import datetime




# Connect to MongoDB
client = MongoClient(settings.MONGO_URI, tls=True, tlsCAFile=certifi.where())
db = client[settings.MONGO_DB_NAME]
users_collection = db['api_user']

class SaveUserData(APIView):
    def post(self, request):
        try:
            user_data = request.data
            if 'firebase_uid' not in user_data:
                return Response({"error": "firebase_uid is required"}, status=status.HTTP_400_BAD_REQUEST)
            if users_collection.find_one({"firebase_uid": user_data['firebase_uid']}):
                return Response({"error": "User with this firebase_uid already exists"}, status=status.HTTP_400_BAD_REQUEST)
            result = users_collection.insert_one(user_data)
            return Response({"message": "User data saved successfully", "id": str(result.inserted_id)}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class GetUserData(APIView):
    def get(self, request, firebase_uid):
        try:
            user = users_collection.find_one({"firebase_uid": firebase_uid})
            if user:
                user.pop('_id', None)
                # Transform field names to match frontend expectations
                response_data = {
                    "firstName": user.get("first_name", ""),
                    "lastName": user.get("last_name", ""),
                    "email": user.get("email", ""),
                    "contactNumber": user.get("contact_number", ""),
                    "dateOfBirth": user.get("date_of_birth", ""),
                    "address": user.get("address", ""),
                    "bloodGroup": user.get("blood_group", ""),
                    "email_verified": user.get("email_verified", False),
                    "firebase_uid": user.get("firebase_uid", "")
                }
                return Response(response_data, status=status.HTTP_200_OK)
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, firebase_uid):
        try:
            # Transform incoming camelCase fields to snake_case for MongoDB
            incoming_data = request.data
            user_data = {
                "first_name": incoming_data.get("firstName", ""),
                "last_name": incoming_data.get("lastName", ""),
                "contact_number": incoming_data.get("contactNumber", ""),
                "date_of_birth": incoming_data.get("dateOfBirth", ""),
                "address": incoming_data.get("address", ""),
                "blood_group": incoming_data.get("bloodGroup", ""),
                # Keep these fields unchanged
                "email": incoming_data.get("email", ""),
                "firebase_uid": firebase_uid,
                "email_verified": incoming_data.get("email_verified", False)
            }
            # Remove any empty strings to avoid overwriting with empty values
            user_data = {k: v for k, v in user_data.items() if v}
            result = users_collection.update_one(
                {"firebase_uid": firebase_uid},
                {"$set": user_data},
                upsert=False
            )
            if result.matched_count > 0:
                return Response({"message": "User updated successfully"}, status=status.HTTP_200_OK)
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class GetDashboardData(APIView):
    def get(self, request):
        client = MongoClient(settings.MONGO_URI, tls=True, tlsCAFile=certifi.where())
        db = client[settings.MONGO_DB_NAME]
        collection = db["DoctorDashboard"]
        document = collection.find_one()

        data = {
            "DocID": document.get("DocID", 0) if document else 0,
            "PendingAppointment": document.get("PendingAppointment", 0) if document else 0,
            "RegisteredPatient": document.get("RegisteredPatient", 0) if document else 0,
            "Referral": document.get("Referral", 0) if document else 0,
            "OnlineConsultation": document.get("OnlineConsultation", 0) if document else 0,
        }
        return Response(data)

class GetAppointmentsData(APIView):
    def get(self, request):
        client = MongoClient(settings.MONGO_URI, tls=True, tlsCAFile=certifi.where())
        db = client[settings.MONGO_DB_NAME]
        collection = db["Appointments"]

        appointments = list(collection.find())

        data = []
        for doc in appointments:
            data.append({
                "AppointmentID": doc.get("AppointmentID", ""),
                "PatientID": doc.get("PatientID", ""),
                "DoctorID": doc.get("DoctorID", ""),
                "SelectSpeciality": doc.get("SelectSpeciality", ""),
                "SelectDoctor": doc.get("SelectDoctor", ""),
                "AppointmentDate": doc.get("AppointmentDate", ""),
                "Time_Slot": str(doc.get("Time_Slot", "")),
                "AppointmentStatus": doc.get("AppointmentStatus", ""),
                "Accepted": doc.get("Accepted", False),
                "Phone": doc.get("Phone", "")
            })

        return Response(data)
    
class GetPatientDashboardData(APIView):
    def get(self, request):
        client = MongoClient(settings.MONGO_URI, tls=True, tlsCAFile=certifi.where())
        db = client["hsm_db"]
        collection = db["PatientDashboard"]

        data = collection.find_one()
        if data:
            response = {
                "PatID": data.get("PatID", 0),
                "PatPendingAppointment": data.get("PatPendingAppointment", 0),
                "PatDoctorCount": data.get("PatDoctorCount", 0),
                "PatDue": data.get("PatDue", 0)
            }
            return JsonResponse(response)
        else:
            return JsonResponse({"error": "Dashboard data not found"}, status=404)

class DoctorCardListAPIView(APIView):
    def get(self, request):
        client = MongoClient(settings.MONGO_URI, tls=True, tlsCAFile=certifi.where())
        db = client["hsm_db"]
        collection = db["DoctorInfo"]

        doctor_list = list(collection.find({}, {"_id": 0}))  # exclude Mongo _id
        return Response(doctor_list)
    
class DoctorAvailabilityView(APIView):
    def get(self, request, doc_id, weekday):
        try:
            client = MongoClient(settings.MONGO_URI, tls=True, tlsCAFile=certifi.where())
            db = client["hsm_db"]
            collection = db["DoctorAvailability"]

            #  Use raw Mongo query instead of Django ORM
            availability = collection.find_one({
                "DocID": doc_id,
                "DocWeekday": weekday
            })

            if availability:
                return Response({
                    "Timeslot1": availability.get("Timeslot1", "No"),
                    "Timeslot2": availability.get("Timeslot2", "No"),
                    "Timeslot3": availability.get("Timeslot3", "No"),
                }, status=status.HTTP_200_OK)
            else:
                return Response({"error": "No availability found."}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class GetAppointmentCount(APIView):
    def get(self, request, doc_id, date):
        try:
            appointment_date = datetime.strptime(date, "%Y-%m-%d").date()
            count = Appointment.objects.filter(doctor_id=doc_id, appointment_date=appointment_date).count()
            return Response({"count": count}, status=status.HTTP_200_OK)
        except ValueError:
            return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
        


class DoctorLoginView(APIView):
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response({"error": "Email and password are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            client = MongoClient(settings.MONGO_URI, tls=True, tlsCAFile=certifi.where())
            db = client["hsm_db"]
            collection = db["DoctorInfo"]

            doctor = collection.find_one({"DocEmail": email, "DocPassword": password})

            if doctor:
                doctor["_id"] = str(doctor["_id"])  # convert ObjectId to string
                return Response({"success": True, "doctor": doctor}, status=status.HTTP_200_OK)
            else:
                return Response({"success": False, "message": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)