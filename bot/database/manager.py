# -*- coding: utf-8 -*-

import logging
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from bson.objectid import ObjectId
import datetime

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
            self.banned_users_collection = self.db.banned_users
            
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
            "admin_panel_title": "أهلاً بك في لوحة التحكم الخاصة بالبوت. اختر أحد الخيارات أدناه:",
            "welcome_message": "أهلاً بك يا #name_user!", "date_button": "📅 التاريخ", "time_button": "⏰ الساعة الآن", "reminder_button": "📿 أذكار اليوم",
            "ar_menu_title": "⚙️ *إدارة الردود التلقائية*", "ar_add_button": "➕ إضافة رد", "ar_view_button": "📖 عرض الردود", "ar_import_button": "📥 استيراد", "ar_back_button": "⬅️ عودة", "ar_ask_for_keyword": "📝 أرسل *الكلمة المفتاحية*", "ar_ask_for_content": "📝 أرسل *محتوى الرد*", "ar_added_success": "✅ تم الحفظ!", "ar_add_another_button": "➕ إضافة المزيد", "ar_ask_for_file": "📦 أرسل ملف `.txt` بالتنسيق:\n`الكلمة === المحتوى`", "ar_import_success": "✅ اكتمل: `{success_count}` نجح، `{failed_count}` فشل.", "ar_no_replies": "لا توجد ردود.", "ar_deleted_success": "🗑️ تم الحذف.", "ar_page_info": "صفحة {current_page}/{total_pages}", "ar_next_button": "التالي ⬅️", "ar_prev_button": "➡️ السابق", "ar_delete_button": "🗑️ حذف",
            "rem_menu_title": "⏰ *إدارة التذكيرات*", "rem_add_button": "➕ إضافة", "rem_view_button": "📖 عرض", "rem_import_button": "📥 استيراد", "rem_ask_for_content": "📝 أرسل *نص التذكير*.", "rem_added_success": "✅ تم الحفظ!", "rem_add_another_button": "➕ إضافة المزيد", "rem_ask_for_file": "📦 أرسل ملف `.txt` (كل سطر تذكير).", "rem_import_success": "✅ اكتمل: `{success_count}` نجح، `{failed_count}` فشل.", "rem_no_reminders": "لا توجد تذكيرات.", "rem_deleted_success": "🗑️ تم الحذف.", "rem_delete_button": "🗑️ حذف",
            "cp_menu_title": "📰 *إدارة منشورات القناة*", "cp_set_auto_msg_button": "✍️ تعيين الرسالة", "cp_view_auto_msg_button": "👀 عرض الرسالة", "cp_publish_now_button": "🚀 نشر الآن", "cp_ask_for_auto_msg": "📝 أرسل الآن الرسالة التي سيتم نشرها.", "cp_auto_msg_set_success": "✅ تم حفظ الرسالة.", "cp_no_auto_msg": "لم يتم تعيين رسالة.", "cp_auto_msg_deleted_success": "🗑️ تم حذف الرسالة.", "cp_publish_started": "🚀 جاري النشر إلى `{count}` قناة...", "cp_publish_finished": "🏁 اكتمل النشر!\n\n✅ نجح: `{success}`\n❌ فشل: `{failed}`", "cp_error_no_auto_msg_to_publish": "⚠️ لا توجد رسالة للنشر!", "cp_error_no_channels_to_publish": "⚠️ لا توجد قنوات مضافة!",
            "cm_menu_title": "📡 *إدارة القنوات*", "cm_add_button": "➕ إضافة قناة", "cm_view_button": "📖 عرض القنوات", "cm_ask_for_channel_id": "📡 أرسل الآن معرّف القناة (مثال: `@channel_username` أو `-100123456789`).\n\n*تأكد من أن البوت مشرف في القناة.*", "cm_add_success": "✅ تم إضافة القناة `{title}`!", "cm_add_fail_not_admin": "❌ فشل الإضافة. البوت ليس مشرفاً.", "cm_add_fail_invalid_id": "❌ فشل الإضافة. المعرّف غير صحيح.", "cm_add_fail_already_exists": "⚠️ هذه القناة مضافة بالفعل.", "cm_no_channels": "لم يتم إضافة قنوات.", "cm_deleted_success": "🗑️ تم حذف القناة.", "cm_test_button": "🔬 تجربة", "cm_test_success": "✅ تم إرسال رسالة تجريبية إلى `{title}`.", "cm_test_fail": "❌ فشل إرسال رسالة تجريبية إلى `{title}`.",
            "bm_menu_title": "🚫 *إدارة الحظر*", "bm_ban_button": "🚫 حظر مستخدم", "bm_unban_button": "✅ إلغاء حظر", "bm_view_button": "📖 عرض المحظورين", "bm_ask_for_user_id": "🆔 أرسل ID المستخدم للحظر.", "bm_ask_for_unban_user_id": "🆔 أرسل ID المستخدم لإلغاء الحظر.", "bm_user_banned_success": "🚫 تم حظر `{user_id}`.", "bm_user_already_banned": "⚠️ `{user_id}` محظور بالفعل.", "bm_user_unbanned_success": "✅ تم إلغاء حظر `{user_id}`.", "bm_user_not_banned": "⚠️ `{user_id}` ليس محظوراً.", "bm_invalid_user_id": "❌ ID غير صالح.", "bm_no_banned_users": "لا يوجد محظورين.",
            "bc_ask_for_message": "📣 *نشر للجميع*", "bc_confirmation": "⏳ سيتم الإرسال إلى `{count}` مستخدم. هل أنت متأكد؟", "bc_confirm_button": "✅ نعم، ابدأ", "bc_cancel_button": "❌ إلغاء", "bc_started": "🚀 بدأت عملية النشر...", "bc_progress": "⏳ جاري النشر...\nنجح: `{success}` | فشل: `{failed}` | متبقي: `{remaining}`", "bc_finished": "🏁 اكتمل النشر!\n\n✅ نجح: `{success}` | ❌ فشل: `{failed}`",
            "ui_menu_title": "🎨 *تخصيص الواجهة*", "ui_edit_date_button": "📅 تعديل زر التاريخ", "ui_edit_time_button": "⏰ تعديل زر الساعة", "ui_edit_reminder_button": "📿 تعديل زر الأذكار", "ui_edit_timezone_button": "🌍 تعديل المنطقة الزمنية", "ui_ask_for_new_text": "📝 أرسل الآن النص الجديد لـ *{item_name}*.", "ui_text_updated_success": "✅ تم تحديث نص *{item_name}* بنجاح.", "ui_ask_for_tz_identifier": "🌐 *الخطوة 1:* أرسل معرّف المنطقة الزمنية (مثال: `Asia/Riyadh`).", "ui_ask_for_tz_display_name": "✍️ *الخطوة 2:* أرسل الاسم الذي سيظهر للمستخدم (مثال: `بتوقيت صنعاء`).", "ui_tz_updated_success": "✅ تم تحديث المنطقة الزمنية.",

            # --- الإضافة الجديدة: نصوص واجهة الحماية والأمان ---
            "sec_menu_title": "🛡️ *الحماية والأمان*",
            "sec_bot_status_button": "🤖 حالة البوت",
            "sec_media_filtering_button": "🖼️ منع الوسائط",
            "sec_antiflood_button": "⏱️ منع التكرار",
            "sec_rejection_message_button": "✍️ تعديل رسالة الرفض",
            "sec_bot_active": "🟢 يعمل",
            "sec_bot_inactive": "🔴 متوقف",
            "sec_media_menu_title": "🖼️ *منع الوسائط المتعددة*\n\nاختر أنواع الرسائل التي تريد منعها.",
            "sec_media_photo": "🖼️ الصور",
            "sec_media_video": "📹 الفيديو",
            "sec_media_link": "🔗 الروابط",
            "sec_media_sticker": "🎭 الملصقات",
            "sec_media_document": "📁 الملفات",
            "sec_media_audio": "🎵 الصوتيات",
            "sec_media_voice": "🎤 الرسائل الصوتية",
            "sec_allowed": "✅ مسموح",
            "sec_blocked": "❌ ممنوع",
            "sec_rejection_msg_ask": "✍️ أرسل الآن رسالة الرفض الجديدة التي ستظهر للمستخدم عند إرساله لوسائط ممنوعة.",
            "sec_rejection_msg_updated": "✅ تم تحديث رسالة الرفض بنجاح.",
            "security_rejection_message": "عذراً، إرسال هذا النوع من الرسائل غير مسموح به.", # الرسالة الافتراضية
        }
        for key, value in defaults.items():
            await self.texts_collection.update_one({"_id": key}, {"$setOnInsert": {"text": value}}, upsert=True)
            
        await self.settings_collection.update_one({"_id": "timezone"}, {"$setOnInsert": {"identifier": "Asia/Riyadh", "display_name": "بتوقيت الرياض"}}, upsert=True)

        # إضافة إعدادات الحماية الافتراضية
        default_security = {
            "bot_status": "active",
            "blocked_media": {
                "photo": False, "video": False, "link": False, "sticker": False,
                "document": False, "audio": False, "voice": False,
            }
        }
        await self.settings_collection.update_one(
            {"_id": "security_settings"},
            {"$setOnInsert": default_security},
            upsert=True
        )

    # --- (الوظائف السابقة موجودة هنا دون تغيير) ---
    # ... وظائف الردود التلقائية، التذكيرات، منشورات القناة، إدارة القنوات، الحظر، النشر، تخصيص الواجهة ...
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
    async def add_publishing_channel(self, channel_id: int, channel_title: str): #...
        if not self.is_connected(): return None
        await self.publishing_channels_collection.update_one({"channel_id": channel_id}, {"$set": {"title": channel_title}}, upsert=True)
    async def get_publishing_channels(self, page: int = 1, limit: int = 10): #...
        if not self.is_connected(): return []
        return await self.publishing_channels_collection.find().skip((page - 1) * limit).limit(limit).to_list(length=limit)
    async def get_publishing_channels_count(self): #...
        if not self.is_connected(): return 0
        return await self.publishing_channels_collection.count_documents({})
    async def delete_publishing_channel(self, db_id: str): #...
        if not self.is_connected(): return False
        try:
            result = await self.publishing_channels_collection.delete_one({"_id": ObjectId(db_id)})
            return result.deleted_count > 0
        except Exception: return False
    async def get_all_publishing_channels(self): #...
        if not self.is_connected(): return []
        return await self.publishing_channels_collection.find().to_list(length=None)
    async def ban_user(self, user_id: int): #...
        if not self.is_connected(): return False
        if await self.is_user_banned(user_id): return False
        await self.banned_users_collection.insert_one({"_id": user_id, "ban_date": datetime.datetime.utcnow()})
        return True
    async def unban_user(self, user_id: int): #...
        if not self.is_connected(): return False
        result = await self.banned_users_collection.delete_one({"_id": user_id})
        return result.deleted_count > 0
    async def is_user_banned(self, user_id: int) -> bool: #...
        if not self.is_connected(): return False
        return await self.banned_users_collection.count_documents({"_id": user_id}) > 0
    async def get_banned_users(self, page: int = 1, limit: int = 10): #...
        if not self.is_connected(): return []
        return await self.banned_users_collection.find().skip((page - 1) * limit).limit(limit).to_list(length=limit)
    async def get_banned_users_count(self): #...
        if not self.is_connected(): return 0
        return await self.banned_users_collection.count_documents({})
    async def get_all_users(self): #...
        if not self.is_connected(): return []
        all_users_cursor = self.users_collection.find({}, {"user_id": 1, "_id": 0})
        all_user_ids = {user['user_id'] for user in await all_users_cursor.to_list(length=None)}
        banned_users_cursor = self.banned_users_collection.find({}, {"_id": 1})
        banned_user_ids = {user['_id'] for user in await banned_users_cursor.to_list(length=None)}
        active_user_ids = all_user_ids - banned_user_ids
        return list(active_user_ids)
    async def update_text(self, text_id: str, new_text: str): #...
        if not self.is_connected(): return
        await self.texts_collection.update_one({"_id": text_id}, {"$set": {"text": new_text}}, upsert=True)
    async def set_timezone(self, identifier: str, display_name: str): #...
        if not self.is_connected(): return
        await self.settings_collection.update_one({"_id": "timezone"}, {"$set": {"identifier": identifier, "display_name": display_name}}, upsert=True)
    async def get_timezone(self) -> dict: #...
        if not self.is_connected(): return {"identifier": "Asia/Riyadh", "display_name": "بتوقيت الرياض"}
        doc = await self.settings_collection.find_one({"_id": "timezone"})
        if doc: return {"identifier": doc.get("identifier", "Asia/Riyadh"), "display_name": doc.get("display_name", "بتوقيت الرياض")}
        return {"identifier": "Asia/Riyadh", "display_name": "بتوقيت الرياض"}

    # --- الإضافة الجديدة: وظائف الحماية والأمان ---
    async def get_security_settings(self):
        """يجلب جميع إعدادات الحماية في استدعاء واحد."""
        if not self.is_connected(): return {}
        doc = await self.settings_collection.find_one({"_id": "security_settings"})
        return doc or {} # إرجاع قاموس فارغ إذا لم يتم العثور على الإعدادات

    async def toggle_bot_status(self):
        """يغير حالة البوت بين 'active' و 'inactive'."""
        if not self.is_connected(): return
        current_settings = await self.get_security_settings()
        new_status = "inactive" if current_settings.get("bot_status", "active") == "active" else "active"
        await self.settings_collection.update_one(
            {"_id": "security_settings"},
            {"$set": {"bot_status": new_status}},
            upsert=True
        )
        return new_status

    async def toggle_media_blocking(self, media_type: str):
        """يغير حالة الحظر لنوع وسائط معين."""
        if not self.is_connected(): return
        # التأكد من أن media_type هو أحد المفاتيح الصالحة
        valid_keys = ["photo", "video", "link", "sticker", "document", "audio", "voice"]
        if media_type not in valid_keys:
            return None
        
        current_settings = await self.get_security_settings()
        current_blocked_media = current_settings.get("blocked_media", {})
        is_currently_blocked = current_blocked_media.get(media_type, False)
        
        await self.settings_collection.update_one(
            {"_id": "security_settings"},
            {"$set": {f"blocked_media.{media_type}": not is_currently_blocked}},
            upsert=True
        )
        return not is_currently_blocked

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
    async def get_subscription_channels(self) -> list[str]: #...
        if not self.is_connected(): return []
        channels_cursor = self.subscription_channels_collection.find({}, {"_id": 0, "username": 1})
        channels_list = await channels_cursor.to_list(length=None)
        return [ch["username"] for ch in channels_list]

db = DatabaseManager()
