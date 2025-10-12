# -*- coding: utf-8 -*-
import os
import motor.motor_asyncio
from pymongo.errors import ConnectionFailure

class DatabaseManager:
    """
    مدير قاعدة البيانات للتعامل مع كل عمليات MongoDB بشكل غير متزامن.
    """
    def __init__(self):
        self.client = None
        self.db = None
        # ... (بقية تعريفات المجموعات)
        self.reminders_collection = None
        self.settings_collection = None
        self.subscription_channels_collection = None
        self.approved_channels_collection = None
        self.text_configs_collection = None
        self.users_collection = None


    async def connect_to_database(self, uri: str, db_name: str = "IslamicBotDB"):
        """إنشاء اتصال مع قاعدة بيانات MongoDB."""
        try:
            self.client = motor.motor_asyncio.AsyncIOMotorClient(uri)
            await self.client.admin.command('ping')
            self.db = self.client[db_name]
            self.reminders_collection = self.db["reminders"]
            self.settings_collection = self.db["settings"]
            self.subscription_channels_collection = self.db["subscription_channels"]
            self.approved_channels_collection = self.db["approved_channels"]
            self.text_configs_collection = self.db["text_configs"]
            self.users_collection = self.db["users"]
            print("تم الاتصال بقاعدة بيانات MongoDB بنجاح.")
            if self.client is not None:
                print("db_connection is not None")
            else:
                print("db_connection is None")
        except ConnectionFailure as e:
            print(f"فشل الاتصال بقاعدة البيانات: {e}")
        except Exception as e:
            print(f"حدث خطأ غير متوقع عند الاتصال بقاعدة البيانات: {e}")

    # --- وظائف التذكيرات ---
    async def add_reminder(self, text: str):
        if self.reminders_collection is not None:
            await self.reminders_collection.insert_one({"text": text})

    async def get_reminders_by_page(self, page: int = 1, limit: int = 8):
        if self.reminders_collection is not None:
            skip_count = (page - 1) * limit
            cursor = self.reminders_collection.find({}, {"_id": 1, "text": 1}).skip(skip_count).limit(limit)
            return await cursor.to_list(length=limit)
        return []

    async def count_reminders(self) -> int:
        if self.reminders_collection is not None:
            return await self.reminders_collection.count_documents({})
        return 0

    async def delete_reminder(self, reminder_id: str):
        from bson.objectid import ObjectId
        if self.reminders_collection is not None:
            await self.reminders_collection.delete_one({"_id": ObjectId(reminder_id)})

    async def get_random_reminder(self) -> str | None:
        if self.reminders_collection is not None:
            pipeline = [{"$sample": {"size": 1}}]
            async for doc in self.reminders_collection.aggregate(pipeline):
                return doc.get("text")
        return None
    
    # --- وظائف الإعدادات ---
    async def get_timezone(self) -> str:
        if self.settings_collection is not None:
            setting = await self.settings_collection.find_one({"name": "timezone"})
            return setting.get("value", "Asia/Riyadh") if setting else "Asia/Riyadh"
        return "Asia/Riyadh"

    async def set_timezone(self, timezone: str):
        if self.settings_collection is not None:
            await self.settings_collection.update_one(
                {"name": "timezone"}, {"$set": {"value": timezone}}, upsert=True
            )
    
    # --- وظائف قنوات الاشتراك الإجباري (مع دعم تقسيم الصفحات) ---
    async def add_subscription_channel(self, channel_id: int, channel_username: str):
        if self.subscription_channels_collection is not None:
            await self.subscription_channels_collection.update_one(
                {"channel_id": channel_id},
                {"$set": {"channel_username": channel_username}},
                upsert=True
            )

    async def get_subscription_channels_by_page(self, page: int = 1, limit: int = 8):
        """جلب قنوات الاشتراك لصفحة معينة."""
        if self.subscription_channels_collection is not None:
            skip_count = (page - 1) * limit
            cursor = self.subscription_channels_collection.find({}).skip(skip_count).limit(limit)
            return await cursor.to_list(length=limit)
        return []

    async def count_subscription_channels(self) -> int:
        """الحصول على العدد الإجمالي لقنوات الاشتراك."""
        if self.subscription_channels_collection is not None:
            return await self.subscription_channels_collection.count_documents({})
        return 0

    async def get_all_subscription_channels(self):
        """جلب كل القنوات (للاستخدام الداخلي في التحقق من الاشتراك)."""
        if self.subscription_channels_collection is not None:
            cursor = self.subscription_channels_collection.find({})
            return await cursor.to_list(length=100) # يمكن زيادة الحد هنا إذا لزم الأمر
        return []


    async def delete_subscription_channel(self, channel_id: int):
        if self.subscription_channels_collection is not None:
            await self.subscription_channels_collection.delete_one({"channel_id": channel_id})
    
    # --- وظائف القنوات المعتمدة ---
    async def add_approved_channel(self, channel_id: int, channel_title: str):
        if self.approved_channels_collection is not None:
            await self.approved_channels_collection.update_one(
                {"channel_id": channel_id},
                {"$set": {"channel_title": channel_title}},
                upsert=True
            )
    
    # --- وظائف النصوص ---
    async def get_text_configs(self) -> dict:
        if self.text_configs_collection is not None:
            configs = await self.text_configs_collection.find_one({"name": "user_interface_texts"})
            return configs.get("value", {}) if configs else {}
        return {}

    async def update_text_config(self, key: str, value: str):
        if self.text_configs_collection is not None:
            await self.text_configs_collection.update_one(
                {"name": "user_interface_texts"},
                {"$set": {f"value.{key}": value}},
                upsert=True
            )
    
    # --- وظائف المستخدمين ---
    async def add_or_update_user(self, user_id: int, first_name: str, username: str | None):
        if self.users_collection is not None:
            await self.users_collection.update_one(
                {"user_id": user_id},
                {"$set": {"first_name": first_name, "username": username}},
                upsert=True
            )

db = DatabaseManager()
