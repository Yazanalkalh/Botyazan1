# -*- coding: utf-8 -*-

import logging
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from bson.objectid import ObjectId

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.client = None
        self.db = None
        # سيتم تهيئة المجموعات في connect_to_database

    def is_connected(self) -> bool:
        """فحص سريع للاتصال."""
        return self.client is not None and self.db is not None

    async def connect_to_database(self, uri: str):
        """الاتصال بقاعدة البيانات واختبار الاتصال."""
        try:
            self.client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=5000)
            # --- التحسين رقم 3: اختبار الاتصال الفعلي ---
            await self.client.admin.command("ping")
            
            self.db = self.client.get_database("IslamicBotDBAiogram")
            
            self.users_collection = self.db.users
            self.texts_collection = self.db.texts
            self.reminders_collection = self.db.reminders
            self.settings_collection = self.db.settings
            self.subscription_channels_collection = self.db.subscription_channels
            self.approved_channels_collection = self.db.approved_channels
            self.temp_posts_collection = self.db.temp_posts
            self.scheduled_posts_collection = self.db.scheduled_posts
            
            await self.initialize_defaults()
            logger.info("✅ تم الاتصال بقاعدة بيانات MongoDB بنجاح (aiogram).")
            return True
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"فشل الاتصال بقاعدة البيانات: {e}")
            return False
        except Exception as e:
            logger.error(f"حدث خطأ غير متوقع أثناء الاتصال بـ MongoDB: {e}")
            return False

    async def initialize_defaults(self):
        """إنشاء المستندات الافتراضية إذا لم تكن موجودة."""
        if not self.is_connected(): return
        defaults = {
            "welcome_message": "أهلاً بك يا {user_mention}!", "date_button": "📅 التاريخ",
            "time_button": "⏰ الساعة الآن", "reminder_button": "📿 أذكار اليوم",
        }
        for key, value in defaults.items():
            await self.texts_collection.update_one({"_id": key}, {"$setOnInsert": {"text": value}}, upsert=True)
        
        await self.settings_collection.update_one({"_id": "timezone"}, {"$setOnInsert": {"value": "Asia/Riyadh"}}, upsert=True)

    # --- وظائف المستخدمين ---
    async def add_user(self, user):
        """إضافة مستخدم جديد أو تحديث بياناته (مع معالجة القيم الفارغة)."""
        if not self.is_connected(): return
        # --- التحسين رقم 1: معالجة القيم الفارغة ---
        user_data = {
            'user_id': user.id,
            'first_name': user.first_name or "",
            'last_name': getattr(user, 'last_name', "") or "",
            'username': user.username or ""
        }
        await self.users_collection.update_one({'user_id': user.id}, {'$set': user_data}, upsert=True)

    # --- وظائف النصوص ---
    async def get_text(self, text_id: str) -> str:
        """جلب نص معين من قاعدة البيانات."""
        if not self.is_connected(): return "..."
        doc = await self.texts_collection.find_one({"_id": text_id})
        default_text = "نص غير متوفر"
        return doc.get("text", default_text) if doc else default_text

    # --- وظائف التذكيرات ---
    async def get_random_reminder(self) -> str:
        if not self.is_connected(): return "لا توجد أذكار حالياً."
        pipeline = [{"$sample": {"size": 1}}]
        async for doc in self.reminders_collection.aggregate(pipeline):
            return doc.get("text", "لا توجد أذكار حالياً.")
        return "لا توجد أذكار حالياً."

    # --- وظائف الإعدادات ---
    async def get_timezone(self) -> str:
        if not self.is_connected(): return "Asia/Riyadh"
        doc = await self.settings_collection.find_one({"_id": "timezone"})
        return doc.get("value", "Asia/Riyadh") if doc else "Asia/Riyadh"
        
    # --- وظائف الاشتراك الإجباري ---
    async def get_subscription_channels(self) -> list[str]:
        """جلب قائمة بأسماء مستخدمي قنوات الاشتراك الإجباري."""
        if not self.is_connected(): return []
        channels_cursor = self.subscription_channels_collection.find({}, {"_id": 0, "username": 1})
        # --- التحسين رقم 2: إرجاع قائمة نصوص نظيفة ---
        channels_list = await channels_cursor.to_list(length=None)
        return [ch["username"] for ch in channels_list]

    async def add_subscription_channel(self, channel_username: str) -> bool:
        if not self.is_connected(): return False
        if not await self.subscription_channels_collection.find_one({"username": channel_username}):
            await self.subscription_channels_collection.insert_one({"username": channel_username})
            return True
        return False

    async def delete_subscription_channel(self, channel_username: str):
        if not self.is_connected(): return
        await self.subscription_channels_collection.delete_one({"username": channel_username})

db = DatabaseManager()
