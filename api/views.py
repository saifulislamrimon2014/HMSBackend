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
from bson import ObjectId




# Connect to MongoDB
client = MongoClient(settings.MONGO_URI, tls=True, tlsCAFile=certifi.where())
db = client[settings.MONGO_DB_NAME]
users_collection = db['api_user']
technologist_collection = db['TechnologistInfo']
accountant_collection = db['AccountsInfo']
inventory_collection = db['InventoryInfo']
doctor_collection = db['DoctorInfo']
doctor_availability_collection = db['DoctorAvailability']
admin_collection = db['AdminInfo']
report_list_collection = db['ReportList']
confirmed_report_list_collection = db['ConfirmedReportList']

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

class GetPatientAppointments(APIView):
    def get(self, request, firebase_uid):
        try:
            client = MongoClient(settings.MONGO_URI, tls=True, tlsCAFile=certifi.where())
            db = client[settings.MONGO_DB_NAME]

            # First get the patient ID from the users collection
            users_collection = db["api_user"]
            user = users_collection.find_one({"firebase_uid": firebase_uid})

            if not user:
                return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

            # Get appointments for this patient
            appointments_collection = db["Appointments"]
            appointments = list(appointments_collection.find({"PatientID": user.get("_id")}))

            # If no appointments found with PatientID, try with firebase_uid directly
            if not appointments:
                appointments = list(appointments_collection.find({"PatientID": firebase_uid}))

            data = []
            for doc in appointments:
                # Convert ObjectId to string for JSON serialization
                if "_id" in doc:
                    doc["_id"] = str(doc["_id"])

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

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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


class GetTechnologistList(APIView):
    def get(self, request):
        try:
            # Get all technologists from the collection
            technologists = list(technologist_collection.find())

            # Convert ObjectId to string for JSON serialization and map to frontend field names
            mapped_technologists = []
            for tech in technologists:
                # Map MongoDB fields to frontend field names
                mapped_tech = {
                    'id': str(tech['_id']),
                    'techId': tech.get('TechID', ''),
                    'name': tech.get('TechName', ''),
                    'phoneNumber': tech.get('TechPhone', ''),
                    'email': tech.get('TechEmail', ''),
                    'joinDate': tech.get('TechJoinDate', ''),
                    'address': tech.get('TechAddress', ''),
                    'password': tech.get('TechPassword', '')
                }
                mapped_technologists.append(mapped_tech)

            return Response(mapped_technologists, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AddTechnologist(APIView):
    def post(self, request):
        try:
            tech_data = request.data

            # Validate required fields
            required_fields = ['name', 'phoneNumber', 'email', 'joinDate', 'address', 'password']
            for field in required_fields:
                if field not in tech_data or not tech_data[field]:
                    return Response({"error": f"{field} is required"}, status=status.HTTP_400_BAD_REQUEST)

            # Generate technologist ID (starting from 401)
            last_tech = technologist_collection.find_one(sort=[("TechID", -1)])
            if last_tech and 'TechID' in last_tech:
                try:
                    last_id = int(last_tech['TechID'])
                    new_id = str(last_id + 1)
                except (ValueError, TypeError):
                    new_id = "401"
            else:
                new_id = "401"

            # Map the fields to the preferred case
            mongo_data = {
                'TechID': new_id,
                'TechName': tech_data['name'],
                'TechPhone': tech_data['phoneNumber'],
                'TechEmail': tech_data['email'],
                'TechJoinDate': tech_data['joinDate'],
                'TechAddress': tech_data['address'],
                'TechPassword': tech_data['password'],
                'CreatedAt': datetime.now()
            }

            # Insert into MongoDB
            result = technologist_collection.insert_one(mongo_data)

            # Return success response with the new ID
            return Response({
                "message": "Technologist added successfully",
                "id": str(result.inserted_id),
                "techId": new_id
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UpdateTechnologist(APIView):
    def put(self, request, tech_id):
        try:
            tech_data = request.data

            # Validate required fields
            required_fields = ['name', 'phoneNumber', 'email', 'joinDate', 'address', 'password']
            for field in required_fields:
                if field not in tech_data or not tech_data[field]:
                    return Response({"error": f"{field} is required"}, status=status.HTTP_400_BAD_REQUEST)

            # Map the fields to the preferred case
            mongo_data = {
                'TechName': tech_data['name'],
                'TechPhone': tech_data['phoneNumber'],
                'TechEmail': tech_data['email'],
                'TechJoinDate': tech_data['joinDate'],
                'TechAddress': tech_data['address'],
                'TechPassword': tech_data['password'],
                'UpdatedAt': datetime.now()
            }

            # Update in MongoDB
            result = technologist_collection.update_one(
                {"_id": ObjectId(tech_id)},
                {"$set": mongo_data}
            )

            if result.matched_count == 0:
                return Response({"error": "Technologist not found"}, status=status.HTTP_404_NOT_FOUND)

            # Return success response
            return Response({
                "message": "Technologist updated successfully",
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DeleteTechnologist(APIView):
    def delete(self, request, tech_id):
        try:
            # Delete from MongoDB
            result = technologist_collection.delete_one({"_id": ObjectId(tech_id)})

            if result.deleted_count == 0:
                return Response({"error": "Technologist not found"}, status=status.HTTP_404_NOT_FOUND)

            # Return success response
            return Response({
                "message": "Technologist deleted successfully",
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GetAccountantList(APIView):
    def get(self, request):
        try:
            # Get all accountants from the collection
            accountants = list(accountant_collection.find())

            # Convert ObjectId to string for JSON serialization and map to frontend field names
            mapped_accountants = []
            for acc in accountants:
                # Map MongoDB fields to frontend field names
                mapped_acc = {
                    'id': str(acc['_id']),
                    'accId': acc.get('AccID', ''),
                    'name': acc.get('AccName', ''),
                    'phoneNumber': acc.get('AccPhone', ''),
                    'email': acc.get('AccEmail', ''),
                    'joinDate': acc.get('AccJoinDate', ''),
                    'address': acc.get('AccAddress', ''),
                    'password': acc.get('AccPassword', '')
                }
                mapped_accountants.append(mapped_acc)

            return Response(mapped_accountants, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AddAccountant(APIView):
    def post(self, request):
        try:
            acc_data = request.data

            # Validate required fields
            required_fields = ['name', 'phoneNumber', 'email', 'joinDate', 'address', 'password']
            for field in required_fields:
                if field not in acc_data or not acc_data[field]:
                    return Response({"error": f"{field} is required"}, status=status.HTTP_400_BAD_REQUEST)

            # Generate accountant ID (starting from 301)
            last_acc = accountant_collection.find_one(sort=[("AccID", -1)])
            if last_acc and 'AccID' in last_acc:
                try:
                    last_id = int(last_acc['AccID'])
                    new_id = str(last_id + 1)
                except (ValueError, TypeError):
                    new_id = "301"
            else:
                new_id = "301"

            # Map the fields to the preferred case
            mongo_data = {
                'AccID': new_id,
                'AccName': acc_data['name'],
                'AccPhone': acc_data['phoneNumber'],
                'AccEmail': acc_data['email'],
                'AccJoinDate': acc_data['joinDate'],
                'AccAddress': acc_data['address'],
                'AccPassword': acc_data['password'],
                'CreatedAt': datetime.now()
            }

            # Insert into MongoDB
            result = accountant_collection.insert_one(mongo_data)

            # Return success response with the new ID
            return Response({
                "message": "Accountant added successfully",
                "id": str(result.inserted_id),
                "accId": new_id
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UpdateAccountant(APIView):
    def put(self, request, acc_id):
        try:
            acc_data = request.data

            # Validate required fields
            required_fields = ['name', 'phoneNumber', 'email', 'joinDate', 'address', 'password']
            for field in required_fields:
                if field not in acc_data or not acc_data[field]:
                    return Response({"error": f"{field} is required"}, status=status.HTTP_400_BAD_REQUEST)

            # Map the fields to the preferred case
            mongo_data = {
                'AccName': acc_data['name'],
                'AccPhone': acc_data['phoneNumber'],
                'AccEmail': acc_data['email'],
                'AccJoinDate': acc_data['joinDate'],
                'AccAddress': acc_data['address'],
                'AccPassword': acc_data['password'],
                'UpdatedAt': datetime.now()
            }

            # Update in MongoDB
            result = accountant_collection.update_one(
                {"_id": ObjectId(acc_id)},
                {"$set": mongo_data}
            )

            if result.matched_count == 0:
                return Response({"error": "Accountant not found"}, status=status.HTTP_404_NOT_FOUND)

            # Return success response
            return Response({
                "message": "Accountant updated successfully",
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DeleteAccountant(APIView):
    def delete(self, request, acc_id):
        try:
            # Delete from MongoDB
            result = accountant_collection.delete_one({"_id": ObjectId(acc_id)})

            if result.deleted_count == 0:
                return Response({"error": "Accountant not found"}, status=status.HTTP_404_NOT_FOUND)

            # Return success response
            return Response({
                "message": "Accountant deleted successfully",
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GetInventoryList(APIView):
    def get(self, request):
        try:
            # Get all inventory items from the collection
            inventory_items = list(inventory_collection.find())

            # Convert ObjectId to string for JSON serialization and map to frontend field names
            mapped_items = []
            for item in inventory_items:
                # Map MongoDB fields to frontend field names
                mapped_item = {
                    'id': str(item['_id']),
                    'itemNo': item.get('ItemNo', ''),
                    'itemName': item.get('ItemName', ''),
                    'quantity': item.get('Quantity', 0),
                    'purchaseDate': item.get('PurchaseDate', '')
                }
                mapped_items.append(mapped_item)

            return Response(mapped_items, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AddInventoryItem(APIView):
    def post(self, request):
        try:
            item_data = request.data

            # Validate required fields
            required_fields = ['itemName', 'quantity', 'purchaseDate']
            for field in required_fields:
                if field not in item_data or not item_data[field]:
                    return Response({"error": f"{field} is required"}, status=status.HTTP_400_BAD_REQUEST)

            # Generate item number (auto-increment)
            last_item = inventory_collection.find_one(sort=[("ItemNo", -1)])
            if last_item and 'ItemNo' in last_item:
                try:
                    last_id = int(last_item['ItemNo'])
                    new_id = last_id + 1
                except (ValueError, TypeError):
                    new_id = 1
            else:
                new_id = 1

            # Map the fields to the preferred case
            mongo_data = {
                'ItemNo': new_id,
                'ItemName': item_data['itemName'],
                'Quantity': int(item_data['quantity']),
                'PurchaseDate': item_data['purchaseDate'],
                'CreatedAt': datetime.now()
            }

            # Insert into MongoDB
            result = inventory_collection.insert_one(mongo_data)

            # Return success response with the new ID
            return Response({
                "message": "Inventory item added successfully",
                "id": str(result.inserted_id),
                "itemNo": new_id
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UpdateInventoryItem(APIView):
    def put(self, request, item_id):
        try:
            item_data = request.data

            # Validate required fields
            required_fields = ['itemName', 'quantity', 'purchaseDate']
            for field in required_fields:
                if field not in item_data or not item_data[field]:
                    return Response({"error": f"{field} is required"}, status=status.HTTP_400_BAD_REQUEST)

            # Map the fields to the preferred case
            mongo_data = {
                'ItemName': item_data['itemName'],
                'Quantity': int(item_data['quantity']),
                'PurchaseDate': item_data['purchaseDate'],
                'UpdatedAt': datetime.now()
            }

            # Update in MongoDB
            result = inventory_collection.update_one(
                {"_id": ObjectId(item_id)},
                {"$set": mongo_data}
            )

            if result.matched_count == 0:
                return Response({"error": "Inventory item not found"}, status=status.HTTP_404_NOT_FOUND)

            # Return success response
            return Response({
                "message": "Inventory item updated successfully",
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DeleteInventoryItem(APIView):
    def delete(self, request, item_id):
        try:
            # Delete from MongoDB
            result = inventory_collection.delete_one({"_id": ObjectId(item_id)})

            if result.deleted_count == 0:
                return Response({"error": "Inventory item not found"}, status=status.HTTP_404_NOT_FOUND)

            # Return success response
            return Response({
                "message": "Inventory item deleted successfully",
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GetDoctorList(APIView):
    def get(self, request):
        try:
            # Get all doctors from the collection
            doctors = list(doctor_collection.find())

            # Convert ObjectId to string for JSON serialization and map to frontend field names
            mapped_doctors = []
            for doctor in doctors:
                # Map MongoDB fields to frontend field names
                mapped_doctor = {
                    'id': str(doctor['_id']),
                    'docID': doctor.get('DocID', ''),
                    'docName': doctor.get('DocName', ''),
                    'dob': doctor.get('DocDOB', ''),
                    'department': doctor.get('DocDepartment', ''),
                    'designation': doctor.get('DocDesignation', ''),
                    'email': doctor.get('DocEmail', ''),
                    'phone': doctor.get('DocPhone', ''),
                    'degree': doctor.get('DocDegree', ''),
                    'details': doctor.get('DocDetails', ''),
                    'image': doctor.get('DocImage', '')
                }
                mapped_doctors.append(mapped_doctor)

            return Response(mapped_doctors, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AddDoctor(APIView):
    def post(self, request):
        try:
            doctor_data = request.data

            # Validate required fields
            required_fields = ['name', 'dob', 'department', 'designation', 'email', 'password', 'phone', 'degree', 'details']
            for field in required_fields:
                if field not in doctor_data or not doctor_data[field]:
                    return Response({"error": f"{field} is required"}, status=status.HTTP_400_BAD_REQUEST)

            # Generate doctor ID (starting from 101)
            last_doctor = doctor_collection.find_one(sort=[("DocID", -1)])
            if last_doctor and 'DocID' in last_doctor:
                try:
                    last_id = int(last_doctor['DocID'])
                    new_id = last_id + 1
                except (ValueError, TypeError):
                    new_id = 101
            else:
                new_id = 101

            # Map the fields to the preferred case
            mongo_data = {
                'DocID': new_id,
                'DocName': doctor_data['name'],
                'DocDOB': doctor_data['dob'],
                'DocDepartment': doctor_data['department'],
                'DocDesignation': doctor_data['designation'],
                'DocEmail': doctor_data['email'],
                'DocPassword': doctor_data['password'],
                'DocPhone': doctor_data['phone'],
                'DocDegree': doctor_data['degree'],
                'DocDetails': doctor_data['details'],
                'DocImage': doctor_data.get('image', ''),
                'CreatedAt': datetime.now()
            }

            # Insert into MongoDB
            result = doctor_collection.insert_one(mongo_data)

            # Return success response with the new ID
            return Response({
                "message": "Doctor added successfully",
                "id": str(result.inserted_id),
                "docId": new_id
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UpdateDoctor(APIView):
    def put(self, request, doc_id):
        try:
            doctor_data = request.data

            # Validate required fields
            required_fields = ['name', 'dob', 'department', 'designation', 'email', 'phone', 'degree', 'details']
            for field in required_fields:
                if field not in doctor_data or not doctor_data[field]:
                    return Response({"error": f"{field} is required"}, status=status.HTTP_400_BAD_REQUEST)

            # Map the fields to the preferred case
            mongo_data = {
                'DocName': doctor_data['name'],
                'DocDOB': doctor_data['dob'],
                'DocDepartment': doctor_data['department'],
                'DocDesignation': doctor_data['designation'],
                'DocEmail': doctor_data['email'],
                'DocPhone': doctor_data['phone'],
                'DocDegree': doctor_data['degree'],
                'DocDetails': doctor_data['details'],
                'UpdatedAt': datetime.now()
            }

            # Add password only if provided
            if 'password' in doctor_data and doctor_data['password']:
                mongo_data['DocPassword'] = doctor_data['password']

            # Add image only if provided
            if 'image' in doctor_data and doctor_data['image']:
                mongo_data['DocImage'] = doctor_data['image']

            # Update in MongoDB
            result = doctor_collection.update_one(
                {"_id": ObjectId(doc_id)},
                {"$set": mongo_data}
            )

            if result.matched_count == 0:
                return Response({"error": "Doctor not found"}, status=status.HTTP_404_NOT_FOUND)

            # Return success response
            return Response({
                "message": "Doctor updated successfully",
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DeleteDoctor(APIView):
    def delete(self, request, doc_id):
        try:
            # Get the DocID before deleting
            doctor = doctor_collection.find_one({"_id": ObjectId(doc_id)})
            if not doctor:
                return Response({"error": "Doctor not found"}, status=status.HTTP_404_NOT_FOUND)

            doc_id_value = doctor.get('DocID')

            # Delete from MongoDB
            result = doctor_collection.delete_one({"_id": ObjectId(doc_id)})

            if result.deleted_count == 0:
                return Response({"error": "Doctor not found"}, status=status.HTTP_404_NOT_FOUND)

            # Also delete all availability records for this doctor
            doctor_availability_collection.delete_many({"DocID": doc_id_value})

            # Return success response
            return Response({
                "message": "Doctor and availability records deleted successfully",
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GetDoctorAvailability(APIView):
    def get(self, request, doc_id):
        try:
            # Get all availability records for the doctor
            availability_records = list(doctor_availability_collection.find({"DocID": int(doc_id)}))

            # Convert ObjectId to string for JSON serialization
            for record in availability_records:
                record['_id'] = str(record['_id'])

            return Response(availability_records, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AddDoctorAvailability(APIView):
    def post(self, request):
        try:
            availability_data = request.data

            # Validate required fields
            required_fields = ['docId', 'weekday', 'timeslot1', 'timeslot2', 'timeslot3']
            for field in required_fields:
                if field not in availability_data:
                    return Response({"error": f"{field} is required"}, status=status.HTTP_400_BAD_REQUEST)

            # Generate availability ID (auto-increment)
            last_availability = doctor_availability_collection.find_one(sort=[("DocAvailabilityID", -1)])
            if last_availability and 'DocAvailabilityID' in last_availability:
                try:
                    last_id = int(last_availability['DocAvailabilityID'])
                    new_id = last_id + 1
                except (ValueError, TypeError):
                    new_id = 1
            else:
                new_id = 1

            # Check if availability already exists for this doctor and weekday
            existing = doctor_availability_collection.find_one({
                "DocID": int(availability_data['docId']),
                "DocWeekday": availability_data['weekday']
            })

            if existing:
                return Response({
                    "error": f"Availability already exists for doctor {availability_data['docId']} on {availability_data['weekday']}"
                }, status=status.HTTP_400_BAD_REQUEST)

            # Map the fields to the preferred case
            mongo_data = {
                'DocID': int(availability_data['docId']),
                'DocWeekday': availability_data['weekday'],
                'DocAvailabilityID': new_id,
                'Timeslot1': availability_data['timeslot1'],
                'Timeslot2': availability_data['timeslot2'],
                'Timeslot3': availability_data['timeslot3'],
                'CreatedAt': datetime.now()
            }

            # Insert into MongoDB
            result = doctor_availability_collection.insert_one(mongo_data)

            # Return success response with the new ID
            return Response({
                "message": "Doctor availability added successfully",
                "id": str(result.inserted_id),
                "availabilityId": new_id
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UpdateDoctorAvailability(APIView):
    def put(self, request, availability_id):
        try:
            availability_data = request.data

            # Validate required fields
            required_fields = ['timeslot1', 'timeslot2', 'timeslot3']
            for field in required_fields:
                if field not in availability_data:
                    return Response({"error": f"{field} is required"}, status=status.HTTP_400_BAD_REQUEST)

            # Map the fields to the preferred case
            mongo_data = {
                'Timeslot1': availability_data['timeslot1'],
                'Timeslot2': availability_data['timeslot2'],
                'Timeslot3': availability_data['timeslot3'],
                'UpdatedAt': datetime.now()
            }

            # Update in MongoDB
            result = doctor_availability_collection.update_one(
                {"_id": ObjectId(availability_id)},
                {"$set": mongo_data}
            )

            if result.matched_count == 0:
                return Response({"error": "Availability record not found"}, status=status.HTTP_404_NOT_FOUND)

            # Return success response
            return Response({
                "message": "Doctor availability updated successfully",
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DeleteDoctorAvailability(APIView):
    def delete(self, request, availability_id):
        try:
            # Delete from MongoDB
            result = doctor_availability_collection.delete_one({"_id": ObjectId(availability_id)})

            if result.deleted_count == 0:
                return Response({"error": "Availability record not found"}, status=status.HTTP_404_NOT_FOUND)

            # Return success response
            return Response({
                "message": "Doctor availability deleted successfully",
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class TechnologistLoginView(APIView):
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response({"error": "Email and password are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Find technologist with matching email and password
            technologist = technologist_collection.find_one({"TechEmail": email, "TechPassword": password})

            if technologist:
                # Convert ObjectId to string for JSON serialization
                technologist["_id"] = str(technologist["_id"])

                # Return technologist data
                return Response({
                    "success": True,
                    "technologist": {
                        "id": technologist["_id"],
                        "techId": technologist.get("TechID", ""),
                        "name": technologist.get("TechName", ""),
                        "email": technologist.get("TechEmail", ""),
                        "phoneNumber": technologist.get("TechPhone", ""),
                        "joinDate": technologist.get("TechJoinDate", ""),
                        "address": technologist.get("TechAddress", "")
                    }
                }, status=status.HTTP_200_OK)
            else:
                return Response({"success": False, "message": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AccountantLoginView(APIView):
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response({"error": "Email and password are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Find accountant with matching email and password
            accountant = accountant_collection.find_one({"AccEmail": email, "AccPassword": password})

            if accountant:
                # Convert ObjectId to string for JSON serialization
                accountant["_id"] = str(accountant["_id"])

                # Return accountant data
                return Response({
                    "success": True,
                    "accountant": {
                        "id": accountant["_id"],
                        "accId": accountant.get("AccID", ""),
                        "name": accountant.get("AccName", ""),
                        "email": accountant.get("AccEmail", ""),
                        "phoneNumber": accountant.get("AccPhone", ""),
                        "joinDate": accountant.get("AccJoinDate", ""),
                        "address": accountant.get("AccAddress", "")
                    }
                }, status=status.HTTP_200_OK)
            else:
                return Response({"success": False, "message": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AdminLoginView(APIView):
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response({"error": "Email and password are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Find admin with matching email and password
            admin = admin_collection.find_one({"AdminEmail": email, "AdminPassword": password})

            if admin:
                # Convert ObjectId to string for JSON serialization
                admin["_id"] = str(admin["_id"])

                # Return admin data
                return Response({
                    "success": True,
                    "admin": {
                        "id": admin["_id"],
                        "email": admin.get("AdminEmail", ""),
                        "name": admin.get("AdminName", "")
                    }
                }, status=status.HTTP_200_OK)
            else:
                return Response({"success": False, "message": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GetPatientList(APIView):
    def get(self, request):
        try:
            # Get all patients from the collection
            patients = list(users_collection.find())

            # Convert ObjectId to string for JSON serialization and map to frontend field names
            mapped_patients = []
            for idx, patient in enumerate(patients):
                # Map MongoDB fields to frontend field names
                mapped_patient = {
                    'id': str(patient['_id']),
                    'slNo': idx + 1,
                    'patientId': patient.get('PatID', ''),
                    'patientName': f"{patient.get('first_name', '')} {patient.get('last_name', '')}",
                    'firstName': patient.get('first_name', ''),
                    'lastName': patient.get('last_name', ''),
                    'phoneNumber': patient.get('contact_number', ''),
                    'email': patient.get('email', ''),
                    'dob': patient.get('date_of_birth', ''),
                    'address': patient.get('address', ''),
                    'bloodGroup': patient.get('blood_group', ''),
                    'gender': patient.get('gender', ''),
                    'age': patient.get('age', ''),
                    'password': patient.get('password', ''),
                    'joinDate': patient.get('created_at', '').strftime('%m/%d/%Y') if patient.get('created_at') else '',
                    'firebase_uid': patient.get('firebase_uid', '')
                }
                mapped_patients.append(mapped_patient)

            return Response(mapped_patients)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UpdatePatient(APIView):
    def put(self, request, patient_id):
        try:
            patient_data = request.data

            # Validate required fields
            required_fields = ['firstName', 'lastName', 'phoneNumber', 'email', 'dob', 'address', 'bloodGroup', 'gender', 'age']
            for field in required_fields:
                if field not in patient_data or not patient_data[field]:
                    return Response({"error": f"{field} is required"}, status=status.HTTP_400_BAD_REQUEST)

            # Prepare data for MongoDB update
            mongo_data = {
                "first_name": patient_data['firstName'],
                "last_name": patient_data['lastName'],
                "contact_number": patient_data['phoneNumber'],
                "email": patient_data['email'],
                "date_of_birth": patient_data['dob'],
                "address": patient_data['address'],
                "blood_group": patient_data['bloodGroup'],
                "gender": patient_data['gender'],
                "age": patient_data['age'],
                "password": patient_data.get('password', '')
            }

            # Update in MongoDB
            result = users_collection.update_one(
                {"_id": ObjectId(patient_id)},
                {"$set": mongo_data}
            )

            if result.modified_count == 0:
                return Response({"error": "Patient not found or no changes made"}, status=status.HTTP_404_NOT_FOUND)

            return Response({"message": "Patient updated successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DeletePatient(APIView):
    def delete(self, request, patient_id):
        try:
            # Delete from MongoDB
            result = users_collection.delete_one({"_id": ObjectId(patient_id)})

            if result.deleted_count == 0:
                return Response({"error": "Patient not found"}, status=status.HTTP_404_NOT_FOUND)

            return Response({"message": "Patient deleted successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GetReportList(APIView):
    def get(self, request):
        try:
            # Get all reports from the collection
            reports = list(report_list_collection.find())

            # Convert ObjectId to string for JSON serialization and map to frontend field names
            mapped_reports = []
            for idx, report in enumerate(reports):
                # Map MongoDB fields to frontend field names
                mapped_report = {
                    'id': str(report['_id']),
                    'reportNo': report.get('ReportNo', ''),
                    'dateOfIssue': report.get('DateOfIssue', ''),
                    'sampleCollection': report.get('SampleCollection', ''),
                    'reportedBy': report.get('ReportedBy', ''),
                    'patientName': report.get('PatientName', ''),
                    'patientId': report.get('PatientId', ''),
                    'doctorId': report.get('DoctorId', ''),
                    'doctorName': report.get('DoctorName', ''),
                    'weight': report.get('Weight', ''),
                    'bloodPressure': report.get('BloodPressure', ''),
                    'sugarLevel': report.get('SugarLevel', ''),
                    'heartRate': report.get('HeartRate', ''),
                    'totalCholesterol': report.get('TotalCholesterol', ''),
                    'hdl': report.get('HDL', ''),
                    'ldl': report.get('LDL', ''),
                    'tg': report.get('TG', ''),
                    'hdlRatio': report.get('HDLRatio', ''),
                    'ecg': report.get('ECG', ''),
                    'xRay': report.get('XRay', ''),
                    'ent': report.get('ENT', ''),
                    'tb': report.get('TB', ''),
                    'summary': report.get('Summary', ''),
                    'payment': report.get('Payment', 'Pending')
                }
                mapped_reports.append(mapped_report)

            return Response(mapped_reports)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AddReport(APIView):
    def post(self, request):
        try:
            report_data = request.data

            # Validate required fields
            required_fields = ['reportedBy', 'patientName', 'patientId', 'doctorId', 'doctorName']
            for field in required_fields:
                if field not in report_data or not report_data[field]:
                    return Response({"error": f"{field} is required"}, status=status.HTTP_400_BAD_REQUEST)

            # Generate report number (auto-increment)
            last_report = report_list_collection.find_one(sort=[("ReportNo", -1)])
            if last_report and 'ReportNo' in last_report:
                try:
                    # If the ReportNo is a string like "001", extract the number
                    if isinstance(last_report['ReportNo'], str) and last_report['ReportNo'].isdigit():
                        last_id = int(last_report['ReportNo'])
                    else:
                        last_id = int(last_report['ReportNo'])
                    new_id = last_id + 1
                except (ValueError, TypeError):
                    new_id = 1
            else:
                new_id = 1

            # Format the report number as a string with leading zeros (e.g., "001")
            report_no = f"{new_id:03d}"

            # Prepare data for MongoDB
            mongo_data = {
                "ReportNo": report_no,
                "DateOfIssue": report_data.get('dateOfIssue', datetime.now().strftime('%Y-%m-%d')),
                "SampleCollection": report_data.get('sampleCollection', ''),
                "ReportedBy": report_data['reportedBy'],
                "PatientName": report_data['patientName'],
                "PatientId": report_data['patientId'],
                "DoctorId": report_data['doctorId'],
                "DoctorName": report_data['doctorName'],
                "Weight": report_data.get('weight', ''),
                "BloodPressure": report_data.get('bloodPressure', ''),
                "SugarLevel": report_data.get('sugarLevel', ''),
                "HeartRate": report_data.get('heartRate', ''),
                "TotalCholesterol": report_data.get('totalCholesterol', ''),
                "HDL": report_data.get('hdl', ''),
                "LDL": report_data.get('ldl', ''),
                "TG": report_data.get('tg', ''),
                "HDLRatio": report_data.get('hdlRatio', ''),
                "ECG": report_data.get('ecg', ''),
                "XRay": report_data.get('xRay', ''),
                "ENT": report_data.get('ent', ''),
                "TB": report_data.get('tb', ''),
                "Summary": report_data.get('summary', '')
            }

            # Insert into MongoDB
            result = report_list_collection.insert_one(mongo_data)

            # Return success response with the new ID
            return Response({
                "message": "Report added successfully",
                "id": str(result.inserted_id),
                "reportNo": report_no
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UpdateReport(APIView):
    def put(self, request, report_id):
        try:
            report_data = request.data

            # Check if this is a partial update for payment status only
            if len(report_data) == 1 and 'payment' in report_data:
                # This is a payment status update only
                mongo_data = {
                    "Payment": report_data['payment']
                }
            else:
                # Validate required fields for full update
                required_fields = ['reportedBy', 'patientName', 'patientId']
                for field in required_fields:
                    if field not in report_data or not report_data[field]:
                        return Response({"error": f"{field} is required"}, status=status.HTTP_400_BAD_REQUEST)

            # Prepare data for MongoDB update if not already set (for payment status only)
            if 'mongo_data' not in locals():
                mongo_data = {
                    "DateOfIssue": report_data.get('dateOfIssue', ''),
                    "SampleCollection": report_data.get('sampleCollection', ''),
                    "ReportedBy": report_data.get('reportedBy', ''),
                    "PatientName": report_data.get('patientName', ''),
                    "PatientId": report_data.get('patientId', ''),
                    "DoctorId": report_data.get('doctorId', ''),
                    "DoctorName": report_data.get('doctorName', ''),
                    "Weight": report_data.get('weight', ''),
                    "BloodPressure": report_data.get('bloodPressure', ''),
                    "SugarLevel": report_data.get('sugarLevel', ''),
                    "HeartRate": report_data.get('heartRate', ''),
                    "TotalCholesterol": report_data.get('totalCholesterol', ''),
                    "HDL": report_data.get('hdl', ''),
                    "LDL": report_data.get('ldl', ''),
                    "TG": report_data.get('tg', ''),
                    "HDLRatio": report_data.get('hdlRatio', ''),
                    "ECG": report_data.get('ecg', ''),
                    "XRay": report_data.get('xRay', ''),
                    "ENT": report_data.get('ent', ''),
                    "TB": report_data.get('tb', ''),
                    "Summary": report_data.get('summary', ''),
                    "Payment": report_data.get('payment', '')
                }

            # Update in MongoDB
            result = report_list_collection.update_one(
                {"_id": ObjectId(report_id)},
                {"$set": mongo_data}
            )

            if result.modified_count == 0:
                return Response({"error": "Report not found or no changes made"}, status=status.HTTP_404_NOT_FOUND)

            return Response({"message": "Report updated successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DeleteReport(APIView):
    def delete(self, request, report_id):
        try:
            # Delete from MongoDB
            result = report_list_collection.delete_one({"_id": ObjectId(report_id)})

            if result.deleted_count == 0:
                return Response({"error": "Report not found"}, status=status.HTTP_404_NOT_FOUND)

            return Response({"message": "Report deleted successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GetConfirmedReportList(APIView):
    def get(self, request):
        try:
            # Get all confirmed reports from the collection
            reports = list(confirmed_report_list_collection.find())

            # Convert ObjectId to string for JSON serialization and map to frontend field names
            mapped_reports = []
            for idx, report in enumerate(reports):
                # Map MongoDB fields to frontend field names
                mapped_report = {
                    'id': str(report['_id']),
                    'reportNo': report.get('ReportNo', ''),
                    'dateOfIssue': report.get('DateOfIssue', ''),
                    'sampleCollection': report.get('SampleCollection', ''),
                    'reportedBy': report.get('ReportedBy', ''),
                    'patientName': report.get('PatientName', ''),
                    'patientId': report.get('PatientId', ''),
                    'doctorId': report.get('DoctorId', ''),
                    'doctorName': report.get('DoctorName', ''),
                    'weight': report.get('Weight', ''),
                    'bloodPressure': report.get('BloodPressure', ''),
                    'sugarLevel': report.get('SugarLevel', ''),
                    'heartRate': report.get('HeartRate', ''),
                    'totalCholesterol': report.get('TotalCholesterol', ''),
                    'hdl': report.get('HDL', ''),
                    'ldl': report.get('LDL', ''),
                    'tg': report.get('TG', ''),
                    'hdlRatio': report.get('HDLRatio', ''),
                    'ecg': report.get('ECG', ''),
                    'xRay': report.get('XRay', ''),
                    'ent': report.get('ENT', ''),
                    'tb': report.get('TB', ''),
                    'summary': report.get('Summary', ''),
                    'deliveryDateTime': report.get('DeliveryDateTime', ''),
                    'payment': report.get('Payment', ''),
                    'phone': report.get('Phone', ''),
                    'delivered': report.get('Delivered', False)
                }
                mapped_reports.append(mapped_report)

            return Response(mapped_reports)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DeliverReport(APIView):
    def post(self, request):
        try:
            report_data = request.data
            report_id = report_data.get('reportId')

            if not report_id:
                return Response({"error": "Report ID is required"}, status=status.HTTP_400_BAD_REQUEST)

            # Get the report from ReportList
            report = report_list_collection.find_one({"_id": ObjectId(report_id)})

            if not report:
                return Response({"error": "Report not found"}, status=status.HTTP_404_NOT_FOUND)

            # Add delivery information
            report['DeliveryDateTime'] = report_data.get('deliveryDateTime', datetime.now().strftime('%d-%b-%Y %I:%M %p'))

            # Get payment status from the report or from the request data
            payment_status = report_data.get('payment', report.get('Payment', 'Pending'))
            report['Payment'] = payment_status

            report['Phone'] = report_data.get('phone', '')
            report['Delivered'] = True

            # Remove MongoDB _id field
            report_id = report.pop('_id')

            # Insert into ConfirmedReportList
            result = confirmed_report_list_collection.insert_one(report)

            # Delete from ReportList
            report_list_collection.delete_one({"_id": ObjectId(report_id)})

            return Response({
                "message": "Report delivered successfully",
                "id": str(result.inserted_id)
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)