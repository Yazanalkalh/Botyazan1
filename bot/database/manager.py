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
            self.publishing_channels_collection = self.db.publishing_channels
            
            await self.initialize_defaults()
            logger.info("✅ تم الاتصال بقاعدة بيانات MongoDB بنجاح.")
            return True
        except Exception as e:
            logger.error(f"❌ فشل الاتصال بقاعدة البيانات: {e}")
            return False

    async def initialize_defaults(self):
        if not self.is_connected(): return
        defaults = {
            # ... (النصوص السابقة موجودة هنا)
            "welcome_message": "أهلاً بك يا {user_mention}!", "date_button": "📅 التاريخ", "time_button": "⏰ الساعة الآن", "reminder_button": "📿 أذكار اليوم",
            "ar_menu_title": "⚙️ *إدارة الردود التلقائية*", "ar_add_button": "➕ إضافة رد", "ar_view_button": "📖 عرض الردود", "ar_import_button": "📥 استيراد", "ar_back_button": "⬅️ عودة", "ar_ask_for_keyword": "📝 أرسل *الكلمة المفتاحية*", "ar_ask_for_content": "📝 أرسل *محتوى الرد*", "ar_added_success": "✅ تم الحفظ!", "ar_add_another_button": "➕ إضافة المزيد", "ar_ask_for_file": "📦 أرسل ملف `.txt` بالتنسيق:\n`الكلمة === المحتوى`", "ar_import_success": "✅ اكتمل: `{success_count}` نجح، `{failed_count}` فشل.", "ar_no_replies": "لا توجد ردود.", "ar_deleted_success": "🗑️ تم الحذف.", "ar_page_info": "صفحة {current_page}/{total_pages}", "ar_next_button": "التالي ⬅️", "ar_prev_button": "➡️ السابق", "ar_delete_button": "🗑️ حذف",
            "rem_menu_title": "⏰ *إدارة التذكيرات*", "rem_add_button": "➕ إضافة", "rem_view_button": "📖 عرض", "rem_import_button": "📥 استيراد", "rem_ask_for_content": "📝 أرسل *نص التذكير*.", "rem_added_success": "✅ تم الحفظ!", "rem_add_another_button": "➕ إضافة المزيد", "rem_ask_for_file": "📦 أرسل ملف `.txt` (كل سطر تذكير).", "rem_import_success": "✅ اكتمل: `{success_count}` نجح، `{failed_count}` فشل.", "rem_no_reminders": "لا توجد تذكيرات.", "rem_deleted_success": "🗑️ تم الحذف.", "rem_delete_button": "🗑️ حذف",
            "cp_menu_title": "📰 *إدارة منشورات القناة*", "cp_set_auto_msg_button": "✍️ تعيين الرسالة", "cp_view_auto_msg_button": "👀 عرض الرسالة", "cp_publish_now_button": "🚀 نشر الآن", "cp_ask_for_auto_msg": "📝 أرسل الآن الرسالة التي سيتم نشرها.", "cp_auto_msg_set_success": "✅ تم حفظ الرسالة.", "cp_no_auto_msg": "لم يتم تعيين رسالة.", "cp_auto_msg_deleted_success": "🗑️ تم حذف الرسالة.", "cp_publish_started": "🚀 جاري النشر إلى `{count}` قناة...", "cp_publish_finished": "🏁 اكتمل النشر!\n\n✅ نجح: `{success}`\n❌ فشل: `{failed}`", "cp_error_no_auto_msg_to_publish": "⚠️ لا توجد رسالة للنشر!", "cp_error_no_channels_to_publish": "⚠️ لا توجد قنوات مضافة!",
            
            # --- الإضافة الجديدة: نصوص واجهة إدارة القنوات ---
            "cm_menu_title": "📡 *إدارة القنوات*\n\nهنا يمكنك إضافة القنوات التي سيقوم البوت بالنشر فيها.",
            "cm_add_button": "➕ إضافة قناة",
            "cm_view_button": "📖 عرض القنوات",
            "cm_ask_for_channel_id": "📡 أرسل الآن معرّف القناة (مثال: `@channel_username` أو `-100123456789`).\n\n*تأكد من أن البوت مشرف في القناة ولديه صلاحية إرسال الرسائل.*",
            "cm_add_success": "✅ تم إضافة القناة `{title}` بنجاح!",
            "cm_add_fail_not_admin": "❌ فشل إضافة القناة. البوت ليس مشرفاً فيها أو لا يملك صلاحية إرسال الرسائل.",
            "cm_add_fail_invalid_id": "❌ فشل إضافة القناة. المعرّف غير صحيح أو لا يمكن الوصول للقناة.",
            "cm_add_fail_already_exists": "⚠️ هذه القناة مضافة بالفعل.",
            "cm_no_channels": "لم يتم إضافة أي قنوات بعد.",
            "cm_deleted_success": "🗑️ تم حذف القناة بنجاح.",
            "cm_test_button": "🔬 تجربة",
            "cm_test_success": "✅ تم إرسال رسالة تجريبية بنجاح إلى القناة `{title}`.",
            "cm_test_fail": "❌ فشل إرسال رسالة تجريبية إلى القناة `{title}`.",
        }
        for key, value in defaults.items():
            await self.texts_collection.update_one({"_id": key}, {"$setOnInsert": {"text": value}}, upsert=True)
        await self.settings_collection.update_one({"_id": "timezone"}, {"$setOnInsert": {"value": "Asia/Riyadh"}}, upsert=True)

    # --- (وظائف الردود التلقائية والتذكيرات ومنشورات القناة موجودة هنا دون تغيير) ---
    async def add_auto_reply(self, keyword: str, message: dict): #...
        if not self.is_connected(): return
        keyword_lower = keyword.lower()
        doc = {"keyword": keyword, "keyword_lower": keyword_lower, "message": message}
        await self.auto_replies_collection.update_one({"keyword_lower": keyword_lower}, {"$set": doc}, upsert=True)
    async def find_auto_reply_by_keyword(self, keyword: str): #...
        if not self.is_connected(): return None
        return await self.auto_replies_collection.find_one({"keyword_lower": keyword.lower()})
    async def get_auto_replies(self, page: int = 1, limit: int = 10): #...
        if not self.is_connected(): return []
        return await self.auto_replies_collection.find().skip((page - 1) * limit).limit(limit).to_list(length=limit)
    async def get_auto_replies_count(self): #...
        if not self.is_connected(): return 0
        return await self.auto_replies_collection.count_documents({})
    async def delete_auto_reply(self, reply_id: str): #...
        if not self.is_connected(): return False
        try:
            result = await self.auto_replies_collection.delete_one({"_id": ObjectId(reply_id)})
            return result.deleted_count > 0
        except Exception: return False
    async def add_reminder(self, text: str): #...
        if not self.is_connected(): return
        await self.reminders_collection.insert_one({"text": text})
    async def get_reminders(self, page: int = 1, limit: int = 10): #...
        if not self.is_connected(): return []
        return await self.reminders_collection.find().skip((page - 1) * limit).limit(limit).to_list(length=limit)
    async def get_reminders_count(self): #...
        if not self.is_connected(): return 0
        return await self.reminders_collection.count_documents({})
    async def delete_reminder(self, reminder_id: str): #...
        if not self.is_connected(): return False
        try:
            result = await self.reminders_collection.delete_one({"_id": ObjectId(reminder_id)})
            return result.deleted_count > 0
        except Exception: return False
    async def set_auto_publication_message(self, message_data: dict): #...
        if not self.is_connected(): return
        await self.settings_collection.update_one({"_id": "auto_publication_message"}, {"$set": {"message": message_data}}, upsert=True)
    async def get_auto_publication_message(self): #...
        if not self.is_connected(): return None
        doc = await self.settings_collection.find_one({"_id": "auto_publication_message"})
        return doc.get("message") if doc else None
    async def delete_auto_publication_message(self): #...
        if not self.is_connected(): return False
        result = await self.settings_collection.delete_one({"_id": "auto_publication_message"})
        return result.deleted_count > 0
        
    # --- الإضافة الجديدة: وظائف إدارة قنوات النشر ---
    async def add_publishing_channel(self, channel_id: int, channel_title: str):
        """يضيف قناة جديدة إلى قائمة النشر."""
        if not self.is_connected(): return None
        # upsert=True يمنع إضافة نفس القناة مرتين
        await self.publishing_channels_collection.update_one(
            {"channel_id": channel_id},
            {"$set": {"title": channel_title}},
            upsert=True
        )

    async def get_publishing_channels(self, page: int = 1, limit: int = 10):
        """يجلب قائمة قنوات النشر مع تقسيم الصفحات."""
        if not self.is_connected(): return []
        return await self.publishing_channels_collection.find().skip((page - 1) * limit).limit(limit).to_list(length=limit)

    async def get_publishing_channels_count(self):
        """يحسب العدد الإجمالي لقنوات النشر."""
        if not self.is_connected(): return 0
        return await self.publishing_channels_collection.count_documents({})

    async def delete_publishing_channel(self, db_id: str):
        """يحذف قناة نشر باستخدام المعرف الخاص بها في قاعدة البيانات."""
        if not self.is_connected(): return False
        try:
            result = await self.publishing_channels_collection.delete_one({"_id": ObjectId(db_id)})
            return result.deleted_count > 0
        except Exception: return False
    
    async def get_all_publishing_channels(self):
        """يجلب كل قنوات النشر (بدون تقسيم صفحات)."""
        if not self.is_connected(): return []
        return await self.publishing_channels_collection.find().to_list(length=None)

    # --- (بقية الوظائف موجودة هنا دون تغيير) ---
    async def log_message_link(self, admin_message_id: int, user_id: int, user_message_id: int): #...
        if not self.is_connected(): return
        await self.forwarding_map_collection.insert_one({"_id": admin_message_id, "user_id": user_id, "user_message_id": user_message_id})
    async def get_message_link_info(self, admin_message_id: int): #...
        if not self.is_connected(): return None
        return await self.forwarding_map_collection.find_one({"_id": admin_message_id})
    async def add_user(self, user) -> bool: #...
        if not self.is_connected(): return False
        user_data = {'first_name': user.first_name or "", 'last_name': getattr(user, 'last_name', "") or "", 'username': user.username or ""}
        result = await self.users_collection.update_one({'user_id': user.id}, {'$set': user_data, '$setOnInsert': {'user_id': user.id}}, upsert=True)
        return result.upserted_id is not None
    async def get_text(self, text_id: str) -> str: #...
        if not self.is_connected(): return f"[{text_id}]"
        doc = await self.texts_collection.find_one({"_id": text_id})
        return doc.get("text", f"[{text_id}]") if doc else f"[{text_id}]"
    async def get_random_reminder(self) -> str: #...
        if not self.is_connected(): return "لا توجد أذكار حالياً."
        pipeline = [{"$sample": {"size": 1}}]
        async for doc in self.reminders_collection.aggregate(pipeline): return doc.get("text", "لا توجد أذكار حالياً.")
        return "لا توجد أذكار حالياً."
    async def get_timezone(self) -> str: #...
        if not self.is_connected(): return "Asia/Riyadh"
        doc = await self.settings_collection.find_one({"_id": "timezone"})
        return doc.get("value", "Asia/Riyadh") if doc else "Asia/Riyadh"
    async def get_subscription_channels(self) -> list[str]: #...
        if not self.is_connected(): return []
        channels_cursor = self.subscription_channels_collection.find({}, {"_id": 0, "username": 1})
        channels_list = await channels_cursor.to_list(length=None)
        return [ch["username"] for ch in channels_list]

db = DatabaseManager()
