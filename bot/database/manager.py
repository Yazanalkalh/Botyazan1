# -*- coding: utf-8 -*-

import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from telegram import Message

# إعداد اللوجر
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
        self.temp_posts_collection = None # <-- إضافة جديدة

    async def connect_to_database(self, uri: str):
        """الاتصال بقاعدة البيانات وإعداد المجموعات."""
        try:
            self.client = MongoClient(uri)
            self.db = self.client.get_database("IslamicBotDB") # اسم قاعدة البيانات
            
            # --- تهيئة المجموعات ---
            self.users_collection = self.db.users
            self.approved_channels_collection = self.db.approved_channels
            self.subscription_channels_collection = self.db.subscription_channels
            self.texts_collection = self.db.texts
            self.reminders_collection = self.db.reminders
            self.settings_collection = self.db.settings
            self.temp_posts_collection = self.db.temp_posts # <-- إضافة جديدة
            
            # التأكد من إنشاء الإعدادات الافتراضية
            await self.initialize_defaults()
            
            logger.info("تم الاتصال بقاعدة بيانات MongoDB بنجاح.")
            return True
        except ConnectionFailure as e:
            logger.error(f"فشل الاتصال بقاعدة البيانات: {e}")
            return False

    async def initialize_defaults(self):
        """إنشاء المستندات الافتراضية إذا لم تكن موجودة."""
        # إعدادات النصوص
        defaults = {
            "welcome_message": "أهلاً بك يا {user_mention} في بوت التقويم الإسلامي!",
            "date_button": "📅 التاريخ",
            "time_button": "⏰ الساعة الآن",
            "reminder_button": "📿 أذكار اليوم",
            "contact_button": "📨 تواصل مع الإدارة"
        }
        for key, value in defaults.items():
            if not await self.texts_collection.find_one({"_id": key}):
                await self.texts_collection.insert_one({"_id": key, "text": value})
        
        # إعدادات المنطقة الزمنية
        if not await self.settings_collection.find_one({"_id": "timezone"}):
            await self.settings_collection.insert_one({"_id": "timezone", "value": "Asia/Riyadh"})

    # --- وظائف المستخدمين ---
    async def add_user(self, user):
        """إضافة مستخدم جديد أو تحديث بياناته."""
        user_data = {
            'user_id': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'username': user.username
        }
        await self.users_collection.update_one(
            {'user_id': user.id},
            {'$set': user_data},
            upsert=True
        )

    # --- وظائف القنوات المعتمدة ---
    async def add_approved_channel(self, channel_id: int, channel_title: str):
        """إضافة قناة جديدة إلى قائمة القنوات المعتمدة."""
        await self.approved_channels_collection.update_one(
            {"channel_id": channel_id},
            {"$set": {"title": channel_title}},
            upsert=True
        )

    async def is_channel_approved(self, channel_id: int) -> bool:
        """التحقق مما إذا كانت القناة معتمدة."""
        return await self.approved_channels_collection.find_one({"channel_id": channel_id}) is not None

    # --- وظائف قنوات الاشتراك الإجباري ---
    async def add_subscription_channel(self, channel_username: str) -> bool:
        """إضافة قناة اشتراك إجباري جديدة."""
        if not await self.subscription_channels_collection.find_one({"username": channel_username}):
            await self.subscription_channels_collection.insert_one({"username": channel_username})
            return True
        return False
        
    async def get_subscription_channels(self, page: int = 1, limit: int = 10):
        """جلب قائمة قنوات الاشتراك الإجباري مع تقسيم الصفحات."""
        skip = (page - 1) * limit
        channels_cursor = self.subscription_channels_collection.find().skip(skip).limit(limit)
        return [doc for doc in await channels_cursor.to_list(length=limit)]

    async def get_subscription_channels_count(self) -> int:
        """الحصول على العدد الإجمالي لقنوات الاشتراك الإجباري."""
        return await self.subscription_channels_collection.count_documents({})
        
    async def delete_subscription_channel(self, channel_username: str):
        """حذف قناة اشتراك إجباري."""
        await self.subscription_channels_collection.delete_one({"username": channel_username})

    # --- وظائف النصوص ---
    async def get_text(self, text_id: str) -> str:
        """جلب نص معين من قاعدة البيانات."""
        doc = await self.texts_collection.find_one({"_id": text_id})
        return doc.get("text", "") if doc else ""

    async def set_text(self, text_id: str, new_text: str):
        """تحديث نص معين في قاعدة البيانات."""
        await self.texts_collection.update_one(
            {"_id": text_id},
            {"$set": {"text": new_text}},
            upsert=True
        )

    # --- وظائف التذكيرات ---
    async def add_reminder(self, text: str):
        """إضافة تذكير جديد."""
        await self.reminders_collection.insert_one({"text": text})

    async def get_random_reminder(self) -> str:
        """جلب تذكير عشوائي."""
        pipeline = [{"$sample": {"size": 1}}]
        async for doc in self.reminders_collection.aggregate(pipeline):
            return doc.get("text", "لا توجد أذكار حالياً.")
        return "لا توجد أذكار حالياً."
        
    async def get_all_reminders(self, page: int = 1, limit: int = 10):
        """جلب كل التذكيرات مع تقسيم الصفحات."""
        skip = (page - 1) * limit
        reminders_cursor = self.reminders_collection.find().skip(skip).limit(limit)
        return [doc for doc in await reminders_cursor.to_list(length=limit)]

    async def get_reminders_count(self) -> int:
        """الحصول على العدد الإجمالي للتذكيرات."""
        return await self.reminders_collection.count_documents({})

    async def delete_reminder(self, reminder_id):
        """حذف تذكير معين."""
        from bson.objectid import ObjectId
        await self.reminders_collection.delete_one({"_id": ObjectId(reminder_id)})

    # --- وظائف الإعدادات ---
    async def get_timezone(self) -> str:
        """جلب المنطقة الزمنية من الإعدادات."""
        doc = await self.settings_collection.find_one({"_id": "timezone"})
        return doc.get("value", "Asia/Riyadh") if doc else "Asia/Riyadh"

    async def set_timezone(self, new_timezone: str):
        """تحديث المنطقة الزمنية."""
        await self.settings_collection.update_one(
            {"_id": "timezone"},
            {"$set": {"value": new_timezone}},
            upsert=True
        )

    # --- وظائف النشر المتقدم (جديدة) ---
    async def save_temp_post(self, admin_id: int, message: Message):
        """حفظ محتوى المنشور المؤقت."""
        post_data = message.to_dict() # تحويل الرسالة بالكامل إلى قاموس
        await self.temp_posts_collection.update_one(
            {"_id": admin_id},
            {"$set": {"post_data": post_data, "buttons": []}}, # إعادة تعيين الأزرار
            upsert=True
        )

    async def update_temp_post_buttons(self, admin_id: int, buttons: list):
        """تحديث أزرار المنشور المؤقت."""
        await self.temp_posts_collection.update_one(
            {"_id": admin_id},
            {"$set": {"buttons": buttons}}
        )

    async def delete_temp_post(self, admin_id: int):
        """حذف المنشور المؤقت بعد الانتهاء أو الإلغاء."""
        await self.temp_posts_collection.delete_one({"_id": admin_id})

# إنشاء نسخة واحدة من مدير قاعدة البيانات لاستخدامها في المشروع بأكمله
db = DatabaseManager()
