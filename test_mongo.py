from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise ValueError("MONGO_URI is not set in .env file")

try:
    print(f"Attempting to connect to: {MONGO_URI}")
    client = MongoClient(MONGO_URI)
    db = client.get_database()
    print("Connection successful!")
except Exception as e:
    print(f"Connection failed: {e}")