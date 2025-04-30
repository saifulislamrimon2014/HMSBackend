from dotenv import load_dotenv
import os

load_dotenv()
MONGO_URI = os.getenv('MONGO_URI')
print(f"MONGO_URI: {MONGO_URI}")