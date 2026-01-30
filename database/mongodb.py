from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
from core.config import settings

class MongoDB:
    client: Optional[AsyncIOMotorClient] = None
    database = None

    async def connect(self):
        """Connect to MongoDB"""
        self.client = AsyncIOMotorClient(settings.MONGODB_URL)
        self.database = self.client[settings.DATABASE_NAME]
        print(f"Connected to MongoDB: {settings.DATABASE_NAME}")

    async def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            print("Disconnected from MongoDB")

    def get_collection(self, collection_name: str):
        """Get a collection from the database"""
        return self.database[collection_name]

    def get_database(self):
        """Get the database instance"""
        return self.database

# Singleton instance
mongodb = MongoDB()


async def get_database():
    """Dependency for getting database instance"""
    return mongodb.get_database()
