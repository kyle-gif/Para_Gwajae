from motor.motor_asyncio import AsyncIOMotorClient
from config import settings

client = AsyncIOMotorClient(settings.MONGODB_URL)
database = client["login_demo"]
user_collection = database.get_collection("users")
