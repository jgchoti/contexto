from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
import os
from dotenv import load_dotenv
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from pymongo.server_api import ServerApi

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")
DB_NAME = os.getenv("MONGO_DB_NAME", "contexto_game")

if not MONGO_URL:
    raise ValueError("MONGO_URL not found in environment variables!")

connection_params = {
    "tls": True,
    "tlsAllowInvalidCertificates": True,
    "serverSelectionTimeoutMS": 10000,
    "connectTimeoutMS": 10000,
    "socketTimeoutMS": 20000,
    "server_api": ServerApi('1')
}

async_client = AsyncIOMotorClient(MONGO_URL, **connection_params)
async_db = async_client[DB_NAME]

sync_client = MongoClient(MONGO_URL, **connection_params)
sync_db = sync_client[DB_NAME]

def get_words_collection():
    return sync_db["words"]

def get_sessions_collection():
    return sync_db["game_sessions"]

async def get_sessions_collection_async():
    return async_db["game_sessions"]

# Game session 
async def save_game_session(session_data: Dict):
    collection = await get_sessions_collection_async()
    result = await collection.insert_one(session_data)
    return str(result.inserted_id)

async def update_game_session(game_id: str, update_data: Dict):
    collection = await get_sessions_collection_async()
    result = await collection.update_one(
        {"game_id": game_id},
        {"$set": update_data}
    )
    return result.modified_count > 0

async def add_guess_to_session(game_id: str, guess_data: Dict):
    collection = await get_sessions_collection_async()
    result = await collection.update_one(
        {"game_id": game_id},
        {
            "$push": {"guesses": guess_data},
            "$set": {"updated_at": datetime.now().isoformat()}
        }
    )
    return result.modified_count > 0

async def get_game_session(game_id: str) -> Optional[Dict]:
    collection = await get_sessions_collection_async()
    session = await collection.find_one({"game_id": game_id})
    if session:
        session.pop('_id', None) 
    return session

async def get_daily_stats(date_str: str) -> Dict:
    collection = await get_sessions_collection_async()
    
    pipeline = [
        {"$match": {"mode": "daily", "date": date_str}},
        {"$group": {
            "_id": None,
            "total_games": {"$sum": 1},
            "completed_games": {
                "$sum": {"$cond": [{"$eq": ["$won", True]}, 1, 0]}
            },
            "avg_guesses": {
                "$avg": {"$size": "$guesses"}
            }
        }}
    ]
    
    result = await collection.aggregate(pipeline).to_list(1)
    return result[0] if result else {}

def load_reference_words() -> Tuple[List[str], None]:
    collection = get_words_collection()
    collection.create_index([("frequency_rank", 1)])

    pipeline = [
        {"$sort": {"frequency_rank": 1}},
        {"$project": {"_id": 0, "word": 1}}
    ]
    
    try:
        cursor = collection.aggregate(pipeline, allowDiskUse=True)
        words = [doc['word'] for doc in cursor]
        return words, None
    except Exception as e:
        print(f"Error loading reference words: {e}")
        return [], None

def initialize_word_list(words: List[str]):
    collection = get_words_collection()

    existing_count = collection.count_documents({})
    if existing_count > 0:
        print(f"⚠️  {existing_count} words already exist in database")
        return

    documents = [
        {"word": word, "frequency_rank": i + 1}
        for i, word in enumerate(words)
    ]
    
    collection.insert_many(documents)
    print(f"✅ Loaded {len(documents)} words into MongoDB")