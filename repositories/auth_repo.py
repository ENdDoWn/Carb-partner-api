from database.mongodb import mongodb
from bson import ObjectId
from datetime import datetime
from zoneinfo import ZoneInfo

class AuthRepository:
    def __init__(self):
        self.collection = mongodb.get_collection("user_profile")

    async def create(self, user_data: dict) -> dict:
        user = await self.collection.insert_one(user_data)
        new_user = await self.collection.find_one({"_id": user.inserted_id})
        if new_user:
            new_user["_id"] = str(new_user["_id"])
        return new_user

    async def find_by_email(self, email: str) -> dict:
        user = await self.collection.find_one({"email": email})
        if user:
            user["_id"] = str(user["_id"])
        return user

    async def find_by_id(self, user_id: str) -> dict:
        try:
            user = await self.collection.find_one({"_id": ObjectId(user_id)})
            if user:
                user["_id"] = str(user["_id"])
            return user
        except Exception:
            return None

    async def find_by_line_id(self, line_user_id: str):
        user = await self.collection.find_one({"auth_providers.line.userId": line_user_id})
        if user:
            user["_id"] = str(user["_id"])
        return user

    async def find_by_google_sub(self, google_sub: str):
        user = await self.collection.find_one({"auth_providers.google.sub": google_sub})
        if user:
            user["_id"] = str(user["_id"])
        return user

    async def find_by_facebook_id(self, fb_id: str):
        user = await self.collection.find_one({"auth_providers.facebook.id": fb_id})
        if user:
            user["_id"] = str(user["_id"])
        return user

    async def create_social_user(self, provider: str, profile_data: dict) -> dict:
        new_user = {
            "full_name": profile_data.get("name"),
            "email": profile_data.get("email"),
            "weight": None,
            "height": None,
            "created_at": datetime.now(ZoneInfo("Asia/Bangkok")),
            "auth_providers": {
                "google": {},
                "line": {},
                "facebook": {}
            }
        }
        if provider == "line":
            new_user["auth_providers"]["line"] = profile_data.get("line")
        elif provider == "google":
            new_user["auth_providers"]["google"] = profile_data.get("google")
        elif provider == "facebook":
            new_user["auth_providers"]["facebook"] = profile_data.get("facebook")

        result = await self.collection.insert_one(new_user)
        
        new_user["_id"] = str(result.inserted_id)
        return new_user

    async def store_verification_code(self, user_id: str, code: str, expires_at: datetime) -> bool:
        """Store verification code and expiry for a user"""
        try:
            result = await self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"verification_code": code, "verification_code_expires_at": expires_at}}
            )
            return result.modified_count > 0
        except Exception:
            return False

    async def verify_email(self, email: str, code: str) -> bool:
        """Verify email with code and mark as verified"""
        try:
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc)
            result = await self.collection.update_one(
                {
                    "email": email,
                    "verification_code": code,
                    "verification_code_expires_at": {"$gte": now}
                },
                {
                    "$set": {"email_verified": True},
                    "$unset": {"verification_code": "", "verification_code_expires_at": ""}
                }
            )
            return result.modified_count > 0
        except Exception:
            return False

    async def is_email_verified(self, email: str) -> bool:
        """Check if email is verified"""
        try:
            user = await self.collection.find_one({"email": email})
            return user and user.get("email_verified", False)
        except Exception:
            return False
