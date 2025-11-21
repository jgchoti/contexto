# backend/test_mongodb.py
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")
DB_NAME = os.getenv("MONGO_DB_NAME", "contexto_game")

if not MONGO_URL:
    raise ValueError("MONGO_URL not found in environment variables!")

try:
    client = MongoClient(MONGO_URL)
    # Test the connection
    client.admin.command('ping')
    print("✅ Connected to MongoDB Atlas!")
    
    # List databases
    db_list = client.list_database_names()
    print(f"Databases: {db_list}")
    
    # Check database for contexto_game
    db = client['contexto_game']
    collections = db.list_collection_names()
    print(f"Collections in 'contexto_game': {collections}")
    
    # Check words collection
    words_count = db['words'].count_documents({})
    print(f"Words in collection: {words_count}")
    
except Exception as e:
    print(f"❌ Connection failed: {e}")