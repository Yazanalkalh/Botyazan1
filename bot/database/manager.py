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
            self.forwarding_map_collection = self.db.message_links
            self.auto_replies_collection = self.db.auto_replies
            
            await self.initialize_defaults()
            logger.info("✅ تم الاتصال بقاعدة بيانات MongoDB بنجاح.")
            return True
        except Exception as e:
            logger.error(f"❌ فشل الاتصال بقاعدة البيانات: {e}")
            return False

    async def initialize_defaults(self):
        if not self.is_connected(): return
        defaults = {
            "welcome_message": "أهلاً بك يا {user_mention}!", "date_button": "📅 التاريخ",
            "time_button": "⏰ الساعة الآن", "reminder_button": "📿 أذكار اليوم",
            "ar_menu_title": "⚙️ *إدارة الردود التلقائية*\n\nاختر الإجراء المطلوب من الأزرار أدناه.",
            "ar_add_button": "➕ إضافة رد جديد",
            "ar_view_button": "📖 عرض كل الردود",
            "ar_import_button": "📥 استيراد من ملف",
            "ar_back_button": "⬅️ عودة",
            "ar_ask_for_keyword": "📝 *الخطوة 1 من 2:*\n\nأرسل الآن *الكلمة المفتاحية*.\nعندما يرسل المستخدم هذه الكلمة، سيقوم البوت بالرد.",
            "ar_ask_for_content": "📝 *الخطوة 2 من 2:*\n\nرائع! الآن أرسل *محتوى الرد*.\nيمكنك استخدام الصور، النصوص، الملصقات، أو أي نوع من الرسائل.",
            "ar_added_success": "✅ تم حفظ الرد بنجاح!",
            "ar_add_another_button": "➕ إضافة رد آخر",
            "ar_ask_for_file": "📦 *استيراد الردود*\n\nأرسل الآن ملف `.txt`.\nيجب أن يكون كل سطر بالصيغة التالية:\n`الكلمة المفتاحية === محتوى الرد`",
            "ar_import_success": "✅ *اكتمل الاستيراد*\n\nتم استيراد `{success_count}` رد بنجاح.\nفشل استيراد `{failed_count}` رد (بسبب تنسيق خاطئ).",
            "ar_no_replies": "لا توجد أي ردود تلقائية مضافة حالياً.",
            "ar_deleted_success": "🗑️ تم حذف الرد بنجاح.",
            "ar_page_info": "صفحة {current_page} من {total_pages}",
            "ar_next_button": "التالي ⬅️",
            "ar_prev_button": "➡️ السابق",
            "ar_delete_button": "🗑️ حذف",
            
            # --- الإضافة الجديدة: جميع نصوص واجهة التذكيرات ---
            "rem_menu_title": "⏰ *إدارة التذكيرات*\n\nاختر الإجراء المطلوب.",
            "rem_add_button": "➕ إضافة تذكير",
            "rem_view_button": "📖 عرض التذكيرات",
            "rem_import_button": "📥 استيراد تذكيرات",
            "rem_ask_for_content": "📝 أرسل الآن *نص التذكير*.",
            "rem_added_success": "✅ تم حفظ التذكير بنجاح!",
            "rem_add_another_button": "➕ إضافة تذكير آخر",
            "rem_ask_for_file": "📦 *استيراد التذكيرات*\n\nأرسل ملف `.txt`.\nيجب أن يحتوي كل سطر على تذكير واحد.",
            "rem_import_success": "✅ اكتمل الاستيراد: `{success_count}` نجح، `{failed_count}` فشل.",
            "rem_no_reminders": "لا توجد أي تذكيرات مضافة حالياً.",
            "rem_deleted_success": "🗑️ تم حذف التذكير بنجاح.",
            "rem_delete_button": "🗑️ حذف",
        }
        for key, value in defaults.items():
            await self.texts_collection.update_one({"_id": key}, {"$setOnInsert": {"text": value}}, upsert=True)
            
        await self.settings_collection.update_one({"_id": "timezone"}, {"$setOnInsert": {"value": "Asia/Riyadh"}}, upsert=True)

    # --- وظائف إدارة الردود التلقائية ---
    async def add_auto_reply(self, keyword: str, message: dict):
        if not self.is_connected(): return
        keyword_lower = keyword.lower()
        doc = {"keyword": keyword, "keyword_lower": keyword_lower, "message": message}
        await self.auto_replies_collection.update_one({"keyword_lower": keyword_lower}, {"$set": doc}, upsert=True)

    async def find_auto_reply_by_keyword(self, keyword: str):
        if not self.is_connected(): return None
        return await self.auto_replies_collection.find_one({"keyword_lower": keyword.lower()})

    async def get_auto_replies(self, page: int = 1, limit: int = 10):
        if not self.is_connected(): return []
        skip = (page - 1) * limit
        cursor = self.auto_replies_collection.find().skip(skip).limit(limit)
        return await cursor.to_list(length=limit)

    async def get_auto_replies_count(self):
        if not self.is_connected(): return 0
        return await self.auto_replies_collection.count_documents({})

    async def delete_auto_reply(self, reply_id: str):
        if not self.is_connected(): return False
        try:
            result = await self.auto_replies_collection.delete_one({"_id": ObjectId(reply_id)})
            return result.deleted_count > 0
        except Exception:
            return False
            
    # --- الإضافة الجديدة: وظائف إدارة التذكيرات ---
    async def add_reminder(self, text: str):
        """يضيف تذكيراً جديداً."""
        if not self.is_connected(): return
        await self.reminders_collection.insert_one({"text": text})

    async def get_reminders(self, page: int = 1, limit: int = 10):
        """يجلب قائمة التذكيرات مع تقسيم الصفحات."""
        if not self.is_connected(): return []
        return await self.reminders_collection.find().skip((page - 1) * limit).limit(limit).to_list(length=limit)

    async def get_reminders_count(self):
        """يحسب العدد الإجمالي للتذكيرات."""
        if not self.is_connected(): return 0
        return await self.reminders_collection.count_documents({})

    async def delete_reminder(self, reminder_id: str):
        """يحذف تذكيراً باستخدام المعرف الخاص به."""
        if not self.is_connected(): return False
        try:
            result = await self.reminders_collection.delete_one({"_id": ObjectId(reminder_id)})
            return result.deleted_count > 0
        except Exception: return False

    # --- وظائف الرد الذكي ---
    async def log_message_link(self, admin_message_id: int, user_id: int, user_message_id: int):
        if not self.is_connected(): return
        await self.forwarding_map_collection.insert_one({"_id": admin_message_id, "user_id": user_id, "user_message_id": user_message_id})

    async def get_message_link_info(self, admin_message_id: int):
        if not self.is_connected(): return None
        return await self.forwarding_map_collection.find_one({"_id": admin_message_id})

    # --- بقية الوظائف ---
    async def add_user(self, user) -> bool:
        if not self.is_connected(): return False
        user_data = {'first_name': user.first_name or "", 'last_name': getattr(user, 'last_name', "") or "", 'username': user.username or ""}
        result = await self.users_collection.update_one({'user_id': user.id}, {'$set': user_data, '$setOnInsert': {'user_id': user.id}}, upsert=True)
        return result.upserted_id is not None
        
    async def get_text(self, text_id: str) -> str:
        if not self.is_connected(): return f"[{text_id}]"
        doc = await self.texts_collection.find_one({"_id": text_id})
        return doc.get("text", f"[{text_id}]") if doc else f"[{text_id}]"
        
    async def get_random_reminder(self) -> str:
        if not self.is_connected(): return "لا توجد أذكار حالياً."
        pipeline = [{"$sample": {"size": 1}}]
        async for doc in self.reminders_collection.aggregate(pipeline): return doc.get("text", "لا توجد أذكار حالياً.")
        return "لا توجد أذكار حالياً."
        
    async def get_timezone(self) -> str:
        if not self.is_connected(): return "Asia/Riyadh"
        doc = await self.settings_collection.find_one({"_id": "timezone"})
        return doc.get("value", "Asia/Riyadh") if doc else "Asia/Riyadh"
        
    async def get_subscription_channels(self) -> list[str]:
        if not self.is_connected(): return []
        channels_cursor = self.subscription_channels_collection.find({}, {"_id": 0, "username": 1})
        channels_list = await channels_cursor.to_list(length=None)
        return [ch["username"] for ch in channels_list]

db = DatabaseManager()
