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

    def is_connected(self) -> bool:
        """فحص سريع للاتصال."""
        return self.client is not None and self.db is not None

    async def connect_to_database(self, uri: str):
        """الاتصال بقاعدة البيانات واختبار الاتصال."""
        try:
            self.client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=5000)
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
    async def add_user(self, user) -> bool:
        """
        إضافة مستخدم جديد أو تحديث بياناته.
        ترجع True إذا كان المستخدم جديداً, و False إذا كان موجوداً مسبقاً.
        """
        if not self.is_connected(): return False
        
        user_data = {
            'first_name': user.first_name or "",
            'last_name': getattr(user, 'last_name', "") or "",
            'username': user.username or ""
        }

        # التحقق مما إذا كان المستخدم موجوداً
        result = await self.users_collection.update_one(
            {'user_id': user.id},
            {'$set': user_data, '$setOnInsert': {'user_id': user.id}},
            upsert=True
        )

        # upserted_id يكون له قيمة فقط إذا تم إنشاء مستند جديد
        if result.upserted_id is not None:
            return True # مستخدم جديد
        else:
            return False # مستخدم موجود مسبقاً

    # --- وظائف النصوص ---
    async def get_text(self, text_id: str) -> str:
        if not self.is_connected(): return "..."
        doc = await self.texts_collection.find_one({"_id": text_id})
        return doc.get("text", "نص غير متوفر") if doc else "نص غير متوفر"

    # --- وظائف التذكيرات ---
    async def get_random_reminder(self) -> str:
        if not self.is_connected(): return "لا توجد أذكار حالياً."
        pipeline = [{"$sample": {"size": 1}}]
        async for doc in self.reminders_collection.aggregate(pipeline): return doc.get("text", "لا توجد أذكار حالياً.")
        return "لا توجد أذكار حالياً."

    # --- وظائف الإعدادات ---
    async def get_timezone(self) -> str:
        if not self.is_connected(): return "Asia/Riyadh"
        doc = await self.settings_collection.find_one({"_id": "timezone"})
        return doc.get("value", "Asia/Riyadh") if doc else "Asia/Riyadh"
        
    # --- وظائف الاشتراك الإجباري ---
    async def get_subscription_channels(self) -> list[str]:
        if not self.is_connected(): return []
        channels_cursor = self.subscription_channels_collection.find({}, {"_id": 0, "username": 1})
        channels_list = await channels_cursor.to_list(length=None)
        return [ch["username"] for ch in channels_list]

db = DatabaseManager()
