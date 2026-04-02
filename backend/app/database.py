import os

from motor.motor_asyncio import AsyncIOMotorClient

# ── Client ────────────────────────────────────────────────────────
# Motor is async — one client shared across the whole app
# Never create a new client per request (expensive)
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "roastmycode")

client: AsyncIOMotorClient = None


async def connect_db():
    """Called on app startup — creates the MongoDB connection."""
    global client
    client = AsyncIOMotorClient(MONGODB_URL)
    print(f"Connected to MongoDB: {DB_NAME}")


async def close_db():
    """Called on app shutdown — cleanly closes the connection."""
    global client
    if client:
        client.close()
        print("MongoDB connection closed")


def get_db():
    """Returns the database — use this in route dependencies."""
    return client[DB_NAME]
