# -*- coding: utf-8 -*-

import logging
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure
from bson.objectid import ObjectId
from datetime import datetime, timedelta
import asyncio

from bot.core.cache import TEXTS_CACHE

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.client = None
        self.db = None

    def is_connected(self) -> bool:
        return self.client is not None and self.db is not None

    async def connect_to_database(self, uri: str):
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
            self.library_collection = self.db.library
            self.scheduled_posts_collection = self.db.scheduled_posts
            self.antiflood_violations_collection = self.db.antiflood_violations
            
            await self.initialize_defaults()
            await self.load_texts_into_cache()

            logger.info("✅ تم الاتصال بقاعدة بيانات MongoDB بنجاح.")
            return True
        except Exception as e:
            logger.error(f"❌ فشل الاتصال بقاعدة البيانات: {e}")
            return False

    async def initialize_defaults(self):
        if not self.is_connected(): return
        # A comprehensive list of default texts
        defaults = {
            "admin_panel_title": "أهلاً بك في لوحة التحكم.", "welcome_message": "أهلاً بك يا #name_user!", "date_button": "📅 التاريخ", "time_button": "⏰ الساعة الآن", "reminder_button": "📿 أذكار اليوم", "user_message_received": "✅ تم استلام رسالتك بنجاح، سيتم الرد عليك قريباً.",
            "ar_menu_title": "⚙️ *إدارة الردود التلقائية*", "ar_add_button": "➕ إضافة رد", "ar_view_button": "📖 عرض الردود", "ar_import_button": "📥 استيراد", "ar_back_button": "⬅️ عودة", "ar_ask_for_keyword": "📝 أرسل *الكلمة المفتاحية*", "ar_ask_for_content": "📝 أرسل *محتوى الرد*", "ar_added_success": "✅ تم الحفظ!", "ar_add_another_button": "➕ إضافة المزيد", "ar_ask_for_file": "📦 أرسل ملف `.txt`.", "ar_import_success": "✅ اكتمل.", "ar_no_replies": "لا توجد ردود.", "ar_deleted_success": "🗑️ تم الحذف.", "ar_page_info": "صفحة {current_page}/{total_pages}", "ar_next_button": "التالي ⬅️", "ar_prev_button": "➡️ السابق", "ar_delete_button": "🗑️ حذف",
            "rem_menu_title": "⏰ *إدارة التذكيرات*", "rem_add_button": "➕ إضافة", "rem_view_button": "📖 عرض", "rem_import_button": "📥 استيراد", "rem_ask_for_content": "📝 أرسل *نص التذكير*.", "rem_added_success": "✅ تم الحفظ!", "rem_add_another_button": "➕ إضافة المزيد", "rem_ask_for_file": "📦 أرسل ملف `.txt`.", "rem_import_success": "✅ اكتمل.", "rem_no_reminders": "لا توجد تذكيرات.", "rem_deleted_success": "🗑️ تم الحذف.", "rem_delete_button": "🗑️ حذف",
            "cp_menu_title": "📰 *إدارة منشورات القناة*", "cp_set_auto_msg_button": "✍️ تعيين الرسالة", "cp_view_auto_msg_button": "👀 عرض الرسالة", "cp_publish_now_button": "🚀 نشر الآن", "cp_schedule_button": "🗓️ جدولة منشور", "cp_view_scheduled_button": "👀 عرض المجدولة", "cp_ask_for_auto_msg": "📝 أرسل الرسالة.", "cp_auto_msg_set_success": "✅ تم الحفظ.", "cp_no_auto_msg": "لم يتم تعيين رسالة.", "cp_auto_msg_deleted_success": "🗑️ تم الحذف.", "cp_publish_started": "🚀 جاري النشر لـ {count} قناة...", "cp_publish_finished": "🏁 اكتمل النشر!\n\n✅ نجح: {success}\n❌ فشل: {failed}", "cp_error_no_auto_msg_to_publish": "⚠️ لا توجد رسالة لنشرها!", "cp_error_no_channels_to_publish": "⚠️ لا توجد قنوات للنشر!",
            "cm_menu_title": "📡 *إدارة القنوات*", "cm_add_button": "➕ إضافة قناة", "cm_view_button": "📖 عرض القنوات", "cm_ask_for_channel_id": "📡 أرسل معرّف القناة.", "cm_add_success": "✅ تم الإضافة!", "cm_add_fail_not_admin": "❌ فشل، البوت ليس مشرفاً.", "cm_add_fail_invalid_id": "❌ فشل، المعرف غير صالح.", "cm_add_fail_already_exists": "⚠️ هذه القناة مضافة بالفعل.", "cm_no_channels": "لا توجد قنوات.", "cm_deleted_success": "🗑️ تم الحذف.", "cm_test_button": "🔬 تجربة", "cm_test_success": "✅ نجح الإرسال.", "cm_test_fail": "❌ فشل الإرسال.",
            "bm_menu_title": "🚫 *إدارة الحظر*", "bm_ban_button": "🚫 حظر", "bm_unban_button": "✅ إلغاء حظر", "bm_view_button": "📖 عرض", "bm_ask_for_user_id": "🆔 أرسل ID.", "bm_ask_for_unban_user_id": "🆔 أرسل ID.", "bm_user_banned_success": "🚫 تم الحظر.", "bm_user_already_banned": "⚠️ محظور بالفعل.", "bm_user_unbanned_success": "✅ تم إلغاء الحظر.", "bm_user_not_banned": "⚠️ ليس محظوراً.", "bm_invalid_user_id": "❌ ID غير صالح.", "bm_no_banned_users": "لا يوجد محظورين.",
            "sec_menu_title": "🛡️ *الحماية والأمان*", "sec_bot_status_button": "🤖 حالة البوت", "sec_media_filtering_button": "🖼️ منع الوسائط", "sec_antiflood_button": "⏱️ منع التكرار", "sec_rejection_message_button": "✍️ تعديل رسالة الرفض", "sec_bot_active": "🟢 يعمل", "sec_bot_inactive": "🔴 متوقف", "sec_media_menu_title": "🖼️ *منع الوسائط*", "sec_media_photo": "🖼️ الصور", "sec_media_video": "📹 الفيديو", "sec_media_link": "🔗 الروابط", "sec_media_sticker": "🎭 الملصقات", "sec_media_document": "📁 الملفات", "sec_media_audio": "🎵 الصوتيات", "sec_media_voice": "🎤 الرسائل الصوتية", "sec_allowed": "✅ مسموح", "sec_blocked": "❌ ممنوع", "sec_rejection_msg_ask": "✍️ أرسل رسالة الرفض.", "sec_rejection_msg_updated": "✅ تم التحديث.", "security_rejection_message": "عذراً، هذا غير مسموح.",
            "fs_menu_title": "🔗 *الاشتراك الإجباري*", "fs_status_button": "🚦 الحالة", "fs_add_button": "➕ إضافة قناة", "fs_view_button": "📖 عرض القنوات", "fs_enabled": "🟢 مفعل", "fs_disabled": "🔴 معطل", "fs_ask_for_channel_id": "📡 أرسل معرّف القناة (username) بدون @.", "fs_add_success": "✅ تم الإضافة!", "fs_add_fail_not_admin": "❌ فشل، البوت ليس مشرفاً.", "fs_no_channels": "لا توجد قنوات.", "fs_deleted_success": "🗑️ تم الحذف.",
            "sch_ask_for_message": "📝 أرسل المنشور للجدولة.", "sch_ask_for_channels": "📡 اختر القنوات.", "sch_all_channels_button": "📢 كل القنوات", "sch_ask_for_datetime": "⏰ أرسل تاريخ ووقت النشر `YYYY-MM-DD HH:MM`.", "sch_invalid_datetime": "❌ صيغة التاريخ خاطئة.", "sch_datetime_in_past": "❌ لا يمكن الجدولة في الماضي.", "sch_add_success": "✅ تم جدولة المنشور.", "sch_no_jobs": "لا توجد منشورات مجدولة.", "sch_deleted_success": "🗑️ تم الحذف.",
            "af_menu_title": "⏱️ *إعدادات منع التكرار (بروتوكول سيربيروس)*","af_status_button": "🚦 حالة البروتوكول", "af_enabled": "🟢 مفعل", "af_disabled": "🔴 معطل", "af_edit_threshold_button": "⚡️ تعديل عتبة الإزعاج", "af_edit_mute_duration_button": "⏳ تعديل مدة التقييد", "af_ask_for_new_value": "✍️ أرسل القيمة الجديدة.", "af_updated_success": "✅ تم تحديث الإعداد بنجاح.", "af_mute_notification": "🔇 *تم تقييدك مؤقتاً.*\nبسبب إرسال رسائل سريعة، تم منعك من الإرسال لمدة {duration} دقيقة.", "af_ban_notification": "🚫 *لقد تم حظرك نهائياً.*\nبسبب تكرار السلوك المزعج، تم منعك من استخدام البوت.",
        }
        for key, value in defaults.items():
            await self.texts_collection.update_one({"_id": key}, {"$setOnInsert": {"text": value}}, upsert=True)

        default_security = {"bot_status": "active", "blocked_media": {}}
        await self.settings_collection.update_one({"_id": "security_settings"}, {"$setOnInsert": default_security}, upsert=True)
        await self.settings_collection.update_one({"_id": "force_subscribe"}, {"$setOnInsert": {"enabled": True}}, upsert=True)
        default_antiflood = {"enabled": True, "rate_limit": 7, "time_window": 2, "mute_duration": 30}
        await self.settings_collection.update_one({"_id": "antiflood_settings"}, {"$setOnInsert": default_antiflood}, upsert=True)

    async def load_texts_into_cache(self):
        if not self.is_connected(): return
        try:
            TEXTS_CACHE.clear()
            cursor = self.texts_collection.find({})
            async for document in cursor:
                TEXTS_CACHE[document['_id']] = document['text']
            logger.info(f"✅ تم تحميل {len(TEXTS_CACHE)} نص في الذاكرة المؤقتة (Cache).")
        except Exception as e:
            logger.error(f"❌ فشل تحميل النصوص في الذاكرة المؤقتة: {e}")

    async def get_text(self, text_id: str) -> str:
        return TEXTS_CACHE.get(text_id, f"[{text_id}]")
        
    # --- Anti-Flood (Cerberus) Protocol Functions ---
    async def get_antiflood_settings(self):
        if not self.is_connected(): return {}
        doc = await self.settings_collection.find_one({"_id": "antiflood_settings"})
        return doc or {}

    async def update_antiflood_setting(self, key: str, value):
        if not self.is_connected(): return
        valid_keys = ["enabled", "rate_limit", "time_window", "mute_duration"]
        if key not in valid_keys: return
        await self.settings_collection.update_one(
            {"_id": "antiflood_settings"},
            {"$set": {key: value}},
            upsert=True
        )

    async def record_antiflood_violation(self, user_id: int):
        if not self.is_connected(): return
        await self.antiflood_violations_collection.update_one(
            {"user_id": user_id},
            {"$inc": {"count": 1}, "$set": {"last_violation": datetime.utcnow()}},
            upsert=True
        )

    async def get_user_violation_count(self, user_id: int, within_hours: int = 1) -> int:
        if not self.is_connected(): return 0
        time_threshold = datetime.utcnow() - timedelta(hours=within_hours)
        doc = await self.antiflood_violations_collection.find_one({
            "user_id": user_id,
            "last_violation": {"$gte": time_threshold}
        })
        return doc.get("count", 0) if doc else 0

    # --- 💡 تم إضافة هذا القسم بالكامل لحل المشكلة 💡 ---
    # --- Scheduled Posts Functions ---
    async def add_scheduled_post(self, job_id: str, message_data: dict, target_channels: list, run_date: datetime):
        """Adds a new scheduled post to the database."""
        if not self.is_connected(): return
        await self.scheduled_posts_collection.insert_one({
            "_id": job_id,
            "message_data": message_data,
            "target_channels": target_channels,
            "run_date": run_date,
            "is_sent": False
        })

    async def delete_scheduled_post(self, job_id: str):
        """Deletes a scheduled post from the database by its job_id."""
        if not self.is_connected(): return
        await self.scheduled_posts_collection.delete_one({"_id": job_id})

    async def get_scheduled_posts_count(self) -> int:
        """Counts all scheduled posts."""
        if not self.is_connected(): return 0
        return await self.scheduled_posts_collection.count_documents({})

    async def get_scheduled_posts(self, page: int = 1, limit: int = 5) -> list:
        """Retrieves scheduled posts with pagination."""
        if not self.is_connected(): return []
        skip = (page - 1) * limit
        cursor = self.scheduled_posts_collection.find({}).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)

    async def get_all_pending_scheduled_posts(self) -> list:
        """
        Retrieves all posts that have not been sent and are scheduled for the future.
        This is used on bot startup to reload jobs.
        """
        if not self.is_connected(): return []
        cursor = self.scheduled_posts_collection.find({
            "is_sent": False,
            "run_date": {"$gte": datetime.utcnow()}
        })
        return await cursor.to_list(length=None) # length=None fetches all matching documents
    
    async def mark_scheduled_post_as_sent(self, job_id: str):
        """Marks a scheduled post as sent after successful execution."""
        if not self.is_connected(): return
        await self.scheduled_posts_collection.update_one(
            {"_id": job_id},
            {"$set": {"is_sent": True}}
        )
    # --- نهاية القسم المضاف ---

    # --- Other Helper Functions ---
    async def get_security_settings(self):
        if not self.is_connected():
            return {"bot_status": "active", "blocked_media": {}}
        settings = await self.settings_collection.find_one({"_id": "security_settings"})
        return settings or {"bot_status": "active", "blocked_media": {}}

    async def ban_user(self, user_id: int) -> bool:
        if not self.is_connected(): return False
        if await self.banned_users_collection.find_one({"_id": user_id}):
            return False
        await self.banned_users_collection.insert_one({"_id": user_id, "ban_date": datetime.utcnow()})
        return True

    async def unban_user(self, user_id: int) -> bool:
        if not self.is_connected(): return False
        result = await self.banned_users_collection.delete_one({"_id": user_id})
        return result.deleted_count > 0

    async def add_user(self, user) -> bool:
        if not self.is_connected(): return False
        if await self.users_collection.find_one({"_id": user.id}):
            return False
        await self.users_collection.insert_one({
            "_id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username,
            "join_date": datetime.utcnow()
        })
        return True

db = DatabaseManager()
