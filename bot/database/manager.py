# -*- coding: utf-8 -*-

import logging
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure
from bson.objectid import ObjectId

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.client = None
        self.db = None
        # ... سيتم تهيئة المجموعات في connect_to_database

    async def connect_to_database(self, uri: str):
        """الاتصال بقاعدة البيانات باستخدام motor."""
        try:
            self.client = AsyncIOMotorClient(uri)
            self.db = self.client.get_database("IslamicBotDBAiogram") # اسم جديد لتجنب التعارض
            
            self.users_collection = self.db.users
            self.approved_channels_collection = self.db.approved_channels
            self.subscription_channels_collection = self.db.subscription_channels
            self.texts_collection = self.db.texts
            self.reminders_collection = self.db.reminders
            self.settings_collection = self.db.settings
            self.temp_posts_collection = self.db.temp_posts
            self.scheduled_posts_collection = self.db.scheduled_posts
            
            await self.initialize_defaults()
            logger.info("تم الاتصال بقاعدة بيانات MongoDB بنجاح (aiogram).")
            return True
        except ConnectionFailure as e:
            logger.error(f"فشل الاتصال بقاعدة البيانات: {e}")
            return False

    async def initialize_defaults(self):
        """إنشاء المستندات الافتراضية إذا لم تكن موجودة."""
        defaults = {
            "welcome_message": "أهلاً بك يا {user_mention}!", "date_button": "📅 التاريخ",
            "time_button": "⏰ الساعة الآن", "reminder_button": "📿 أذكار اليوم",
            "contact_button": "📨 تواصل مع الإدارة"
        }
        for key, value in defaults.items():
            await self.texts_collection.update_one({"_id": key}, {"$setOnInsert": {"text": value}}, upsert=True)
        
        await self.settings_collection.update_one({"_id": "timezone"}, {"$setOnInsert": {"value": "Asia/Riyadh"}}, upsert=True)

    async def add_user(self, user):
        """إضافة مستخدم جديد أو تحديث بياناته."""
        user_data = {
            'user_id': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'username': user.username
        }
        await self.users_collection.update_one({'user_id': user.id}, {'$set': user_data}, upsert=True)

# ... بقية وظائف قاعدة البيانات يمكن إضافتها هنا عند الحاجة ...

db = DatabaseManager()
