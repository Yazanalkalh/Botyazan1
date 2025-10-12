# -*- coding: utf-8 -*-

import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from telegram import Message

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.client = None
        self.db = None
        self.users_collection = None
        self.approved_channels_collection = None
        self.subscription_channels_collection = None
        self.texts_collection = None
        self.reminders_collection = None
        self.settings_collection = None
        self.temp_posts_collection = None
        self.scheduled_posts_collection = None

    async def connect_to_database(self, uri: str):
        try:
            self.client = MongoClient(uri, appname="islamic_bot")
            self.db = self.client.get_database("IslamicBotDB")
            self.users_collection = self.db.users
            self.approved_channels_collection = self.db.approved_channels
            self.subscription_channels_collection = self.db.subscription_channels
            self.texts_collection = self.db.texts
            self.reminders_collection = self.db.reminders
            self.settings_collection = self.db.settings
            self.temp_posts_collection = self.db.temp_posts
            self.scheduled_posts_collection = self.db.scheduled_posts
            await self.initialize_defaults()
            logger.info("تم الاتصال بقاعدة بيانات MongoDB بنجاح.")
            return True
        except ConnectionFailure as e:
            logger.error(f"فشل الاتصال بقاعدة البيانات: {e}")
            return False

    async def initialize_defaults(self):
        defaults = {
            "welcome_message": "أهلاً بك يا {user_mention}!", "date_button": "📅 التاريخ",
            "time_button": "⏰ الساعة الآن", "reminder_button": "📿 أذكار اليوم",
            "contact_button": "📨 تواصل مع الإدارة"
        }
        for key, value in defaults.items():
            await self.texts_collection.update_one({"_id": key}, {"$setOnInsert": {"text": value}}, upsert=True)
        await self.settings_collection.update_one({"_id": "timezone"}, {"$setOnInsert": {"value": "Asia/Riyadh"}}, upsert=True)

    # --- وظائف المستخدمين ---
    async def add_user(self, user):
        user_data = {
            'user_id': user.id, 'first_name': user.first_name,
            'last_name': user.last_name, 'username': user.username
        }
        await self.users_collection.update_one({'user_id': user.id}, {'$set': user_data}, upsert=True)

    # --- وظائف القنوات ---
    async def add_approved_channel(self, channel_id: int, channel_title: str):
        await self.approved_channels_collection.update_one(
            {"channel_id": channel_id}, {"$set": {"title": channel_title}}, upsert=True
        )

    async def get_all_approved_channels(self):
        """تجلب كل القنوات المعتمدة."""
        channels_cursor = self.approved_channels_collection.find()
        return [doc for doc in await channels_cursor.to_list(length=None)]

    async def is_channel_approved(self, channel_id: int) -> bool:
        return await self.approved_channels_collection.find_one({"channel_id": channel_id}) is not None
    
    # --- وظائف الاشتراك الإجباري ---
    async def add_subscription_channel(self, channel_username: str) -> bool:
        if not await self.subscription_channels_collection.find_one({"username": channel_username}):
            await self.subscription_channels_collection.insert_one({"username": channel_username})
            return True
        return False
        
    async def get_subscription_channels(self, page: int = 1, limit: int = 10):
        skip = (page - 1) * limit
        channels_cursor = self.subscription_channels_collection.find().skip(skip).limit(limit)
        return [doc for doc in await channels_cursor.to_list(length=limit)]

    async def get_subscription_channels_count(self) -> int:
        return await self.subscription_channels_collection.count_documents({})
        
    async def delete_subscription_channel(self, channel_username: str):
        await self.subscription_channels_collection.delete_one({"username": channel_username})

    # --- وظائف النصوص ---
    async def get_text(self, text_id: str) -> str:
        doc = await self.texts_collection.find_one({"_id": text_id})
        return doc.get("text", "") if doc else ""

    async def set_text(self, text_id: str, new_text: str):
        await self.texts_collection.update_one({"_id": text_id}, {"$set": {"text": new_text}}, upsert=True)

    # --- وظائف التذكيرات ---
    async def add_reminder(self, text: str):
        await self.reminders_collection.insert_one({"text": text})

    async def get_random_reminder(self) -> str:
        pipeline = [{"$sample": {"size": 1}}]
        async for doc in self.reminders_collection.aggregate(pipeline):
            return doc.get("text", "لا توجد أذكار حالياً.")
        return "لا توجد أذكار حالياً."
        
    async def get_all_reminders(self, page: int = 1, limit: int = 10):
        skip = (page - 1) * limit
        reminders_cursor = self.reminders_collection.find().skip(skip).limit(limit)
        return [doc for doc in await reminders_cursor.to_list(length=limit)]

    async def get_reminders_count(self) -> int:
        return await self.reminders_collection.count_documents({})

    async def delete_reminder(self, reminder_id):
        from bson.objectid import ObjectId
        await self.reminders_collection.delete_one({"_id": ObjectId(reminder_id)})

    # --- وظائف الإعدادات ---
    async def get_timezone(self) -> str:
        doc = await self.settings_collection.find_one({"_id": "timezone"})
        return doc.get("value", "Asia/Riyadh")
        
    async def set_timezone(self, new_timezone: str):
        await self.settings_collection.update_one({"_id": "timezone"}, {"$set": {"value": new_timezone}}, upsert=True)

    # --- وظائف النشر ---
    async def save_temp_post(self, admin_id: int, message: Message):
        post_data = message.to_dict()
        await self.temp_posts_collection.update_one(
            {"_id": admin_id}, {"$set": {"post_data": post_data, "buttons": []}}, upsert=True
        )

    async def update_temp_post_buttons(self, admin_id: int, buttons: list):
        await self.temp_posts_collection.update_one({"_id": admin_id}, {"$set": {"buttons": buttons}})

    async def get_temp_post(self, admin_id: int):
        return await self.temp_posts_collection.find_one({"_id": admin_id})

    async def delete_temp_post(self, admin_id: int):
        await self.temp_posts_collection.delete_one({"_id": admin_id})

db = DatabaseManager()
