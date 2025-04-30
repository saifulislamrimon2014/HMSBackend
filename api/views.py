from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from pymongo import MongoClient
from django.conf import settings
import certifi
from rest_framework.decorators import api_view
import os
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


    @api_view(['GET'])
    def get_dashboard_data(request):
        from pymongo import MongoClient
        
        client = MongoClient("mongodb+srv://hmsbd64:<db_password>@cluster0.jof024m.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
        
        db = client["hsm_db"]  # your DB name
        collection = db["DoctorDashboard"]  # your collection name

        document = collection.find_one()  # get the first document

        if document:
            data = {
                "PendingAppointment": document.get("PendingAppointment", 0),
                "RegisteredPatient": document.get("RegisteredPatient", 0),
                "Referral": document.get("Referral", 0),
                "OnlineConsulation": document.get("OnlineConsulation", 0)
            }
        else:
            data = {
                "PendingAppointment": 0,
                "RegisteredPatient": 0,
                "Referral": 0,
                "OnlineConsulation": 0
            }

        return Response(data)
