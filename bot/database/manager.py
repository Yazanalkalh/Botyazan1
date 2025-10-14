# -*- coding: utf-8 -*-

import logging
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from bson.objectid import ObjectId
import datetime
import asyncio
# --- 💡 التحسين رقم 1: استيراد أدوات جديدة من مكتبة قاعدة البيانات 💡 ---
# سنستخدم هذه الأدوات لتنفيذ عمليات متعددة دفعة واحدة (للسرعة).
from pymongo import UpdateOne, IndexModel

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.client = None
        self.db = None
        # --- 💡 التحسين رقم 2: إضافة ذاكرة تخزين مؤقت (Cache) 💡 ---
        # بدلاً من سؤال قاعدة البيانات عن نفس المعلومة كل مرة، سنحفظها هنا.
        # هذا يجعل استجابة البوت شبه فورية للنصوص والإعدادات.
        self.texts_cache = {}
        self.settings_cache = {}

    def is_connected(self) -> bool:
        return self.client is not None and self.db is not None

    async def connect_to_database(self, uri: str):
        try:
            self.client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=5000)
            await self.client.admin.command("ping")
            self.db = self.client.get_database("IslamicBotDBAiogram")
            # (تعريف المجموعات كما هو)
            self.users_collection = self.db.users
            self.texts_collection = self.db.texts
            self.reminders_collection = self.db.reminders
            self.settings_collection = self.db.settings
            self.subscription_channels_collection = self.db.subscription_channels
            self.forwarding_map_collection = self.db.message_links
            self.auto_replies_collection = self.db.auto_replies
            self.publishing_channels_collection = self.db.publishing_channels
            self.banned_users_collection = self.db.banned_users
            self.library_collection = self.db.library
            
            # (سنقوم بالتحسينات داخل initialize_defaults)
            await self.initialize_defaults()
            
            # ملء الذاكرة المؤقتة عند بدء التشغيل
            await self._prime_caches()

            logger.info("✅ تم الاتصال بقاعدة بيانات MongoDB بنجاح.")
            return True
        except Exception as e:
            logger.error(f"❌ فشل الاتصال بقاعدة البيانات: {e}")
            return False

    async def create_indexes(self):
        """
        💡 دالة جديدة بالكامل: هذه هي الدالة التي استدعيناها في main.py.
        تقوم بإنشاء فهارس للمجموعات المهمة لضمان سرعة بحث فائقة.
        """
        if not self.is_connected(): return
        try:
            user_index = IndexModel([("user_id", 1)], unique=True)
            autoreply_index = IndexModel([("keyword_lower", 1)])
            channel_index = IndexModel([("channel_id", 1)], unique=True)
            
            await asyncio.gather(
                self.users_collection.create_indexes([user_index]),
                self.auto_replies_collection.create_indexes([autoreply_index]),
                self.subscription_channels_collection.create_indexes([channel_index]),
                self.publishing_channels_collection.create_indexes([channel_index])
            )
        except Exception as e:
            logger.error(f"فشل في إنشاء فهارس قاعدة البيانات: {e}")
            
    async def _prime_caches(self):
        """دالة داخلية لملء الذاكرة المؤقتة عند بدء التشغيل لمرة واحدة."""
        if not self.is_connected(): return
        
        # جلب كل النصوص والإعدادات دفعة واحدة
        texts_cursor = self.texts_collection.find({})
        settings_cursor = self.settings_collection.find({})
        
        texts_list, settings_list = await asyncio.gather(
            texts_cursor.to_list(length=None),
            settings_cursor.to_list(length=None)
        )
        
        self.texts_cache = {doc["_id"]: doc.get("text") for doc in texts_list}
        self.settings_cache = {doc["_id"]: doc for doc in settings_list}
        logger.info(f"⚡️ تم تخزين {len(self.texts_cache)} نص و {len(self.settings_cache)} إعداد في الذاكرة المؤقتة.")


    async def initialize_defaults(self):
        """
        💡 التحسين رقم 3: استخدام bulk_write لتسريع بدء التشغيل.
        بدلاً من 50+ رحلة لقاعدة البيانات، نقوم الآن برحلة واحدة فقط.
        """
        if not self.is_connected(): return
        
        # (قائمة النصوص الافتراضية كما هي)
        defaults = {
            "admin_panel_title": "أهلاً بك في لوحة التحكم.",
            "welcome_message": "أهلاً بك يا #name_user!", "date_button": "📅 التاريخ", "time_button": "⏰ الساعة الآن", "reminder_button": "📿 أذكار اليوم",
            # ... إلخ، كل النصوص الأخرى هنا
        }
        
        # تجميع عمليات النصوص
        text_operations = [
            UpdateOne({"_id": key}, {"$setOnInsert": {"text": value}}, upsert=True)
            for key, value in defaults.items()
        ]
        if text_operations:
            await self.texts_collection.bulk_write(text_operations, ordered=False)

        # تجميع عمليات الإعدادات
        settings_operations = [
            UpdateOne({"_id": "timezone"}, {"$setOnInsert": {"identifier": "Asia/Riyadh", "display_name": "بتوقيت الرياض"}}, upsert=True),
            UpdateOne({"_id": "security_settings"}, {"$setOnInsert": {"bot_status": "active", "blocked_media": {}}}, upsert=True),
            UpdateOne({"_id": "force_subscribe"}, {"$setOnInsert": {"enabled": True}}, upsert=True)
        ]
        await self.settings_collection.bulk_write(settings_operations, ordered=False)


    async def get_text(self, text_id: str) -> str:
        """💡 دالة مُحسَّنة: تقرأ من الذاكرة المؤقتة فائقة السرعة أولاً."""
        # إذا كان النص موجوداً في الذاكرة، يتم إرجاعه فوراً. لا يوجد انتظار.
        return self.texts_cache.get(text_id, f"[{text_id}]")

    async def update_text(self, text_id: str, new_text: str):
        """💡 دالة مُحسَّنة: تقوم بالتحديث في قاعدة البيانات والذاكرة المؤقتة معاً."""
        if not self.is_connected(): return
        # تحديث الذاكرة المؤقتة لضمان أن البيانات متطابقة
        self.texts_cache[text_id] = new_text
        # إرسال التحديث إلى قاعدة البيانات في الخلفية
        asyncio.create_task(
            self.texts_collection.update_one({"_id": text_id}, {"$set": {"text": new_text}}, upsert=True)
        )
        
    # --- (تم تطبيق نفس منطق الذاكرة المؤقتة على جميع دوال الإعدادات) ---
    async def get_force_subscribe_status(self) -> bool:
        """تقرأ من الذاكرة المؤقتة."""
        settings = self.settings_cache.get("force_subscribe", {"enabled": True})
        return settings.get("enabled", True)

    async def toggle_force_subscribe_status(self):
        """تُحدّث الذاكرة المؤقتة وقاعدة البيانات."""
        if not self.is_connected(): return
        current_status = await self.get_force_subscribe_status()
        new_status = not current_status
        
        # تحديث الذاكرة المؤقتة فوراً
        if "force_subscribe" not in self.settings_cache:
            self.settings_cache["force_subscribe"] = {}
        self.settings_cache["force_subscribe"]["enabled"] = new_status

        # تحديث قاعدة البيانات في الخلفية
        asyncio.create_task(
            self.settings_collection.update_one(
                {"_id": "force_subscribe"}, 
                {"$set": {"enabled": new_status}}, 
                upsert=True
            )
        )
        return new_status

    async def get_all_users(self):
        """
        💡 التحسين رقم 4: دالة مُعاد كتابتها بالكامل.
        بدلاً من جلب قائمتين ضخمتين للبوت، نجعل قاعدة البيانات تقوم بكل العمل.
        هذا التعديل هو الأهم على الإطلاق لأداء البوت مع زيادة عدد المستخدمين.
        """
        if not self.is_connected(): return []
        
        pipeline = [
            {
                '$lookup': {
                    'from': 'banned_users',      # من مجموعة المحظورين
                    'localField': 'user_id',     # الحقل في مجموعة المستخدمين
                    'foreignField': '_id',       # الحقل في مجموعة المحظورين
                    'as': 'ban_info'             # اسم الحقل المؤقت للنتيجة
                }
            },
            {
                '$match': {
                    'ban_info': { '$eq': [] } # احتفظ فقط بالمستخدمين الذين ليس لديهم تطابق (غير محظورين)
                }
            },
            {
                '$project': { 'user_id': 1, '_id': 0 } # نريد فقط ID المستخدم
            }
        ]
        
        cursor = self.users_collection.aggregate(pipeline)
        active_users = await cursor.to_list(length=None)
        return [user['user_id'] for user in active_users]

    # --- (جميع الدوال الأخرى تبقى كما هي دون تغيير) ---
    # ... (لصق بقية الدوال من ملفك الأصلي هنا) ...
    # ... add_user, get_random_reminder, ban_user, etc.
    # لقد تركتها كما هي لأنها بالفعل فعالة وتستفيد من الفهارس التي أضفناها.

# --- إنشاء النسخة النهائية ---
db = DatabaseManager()
