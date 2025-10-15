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
            "cp_menu_title": "📰 *إدارة منشورات القناة*", "cp_set_auto_msg_button": "✍️ تعيين الرسالة", "cp_view_auto_msg_button": "👀 عرض الرسالة", "cp_publish_now_button": "🚀 نشر الآن", "cp_schedule_button": "🗓️ جدولة منشور", "cp_view_scheduled_button": "👀 عرض المجدولة", "cp_ask_for_auto_msg": "📝 أرسل الرسالة.", "cp_auto_msg_set_success": "✅ تم الحفظ.", "cp_no_auto_msg": "لم يتم تعيين رسالة.", "cp_auto_msg_deleted_success": "🗑️ تم الحذف.", "cp_publish_started": "🚀 جاري النشر لـ {count} قناة...", "cp_publish_finished": "🏁 اكتمل النشر!\n\n✅ نجح: {success}\n❌ فشل: {failed}", "cp_error_no_auto_msg_to_publish": "⚠️ لا توجد رسالة لنشرها!", "cp_error_no_channels_to_publish": "⚠️ لا توجد قنوات للنشر!",
            "bm_menu_title": "🚫 *إدارة الحظر*", "bm_ban_button": "🚫 حظر", "bm_unban_button": "✅ إلغاء حظر", "bm_view_button": "📖 عرض", "bm_ask_for_user_id": "🆔 أرسل ID.", "bm_ask_for_unban_user_id": "🆔 أرسل ID.", "bm_user_banned_success": "🚫 تم الحظر.", "bm_user_already_banned": "⚠️ محظور بالفعل.", "bm_user_unbanned_success": "✅ تم إلغاء الحظر.", "bm_user_not_banned": "⚠️ ليس محظوراً.", "bm_invalid_user_id": "❌ ID غير صالح.", "bm_no_banned_users": "لا يوجد محظورين.",
            "sec_menu_title": "🛡️ *الحماية والأمان*", "sec_bot_status_button": "🤖 حالة البوت", "sec_media_filtering_button": "🖼️ منع الوسائط", "sec_antiflood_button": "⏱️ منع التكرار", "sec_rejection_message_button": "✍️ تعديل رسالة الرفض", "sec_bot_active": "🟢 يعمل", "sec_bot_inactive": "🔴 متوقف", "security_rejection_message": "عذراً، هذا غير مسموح.",
            "sch_add_success": "✅ تم جدولة المنشور.", "sch_no_jobs": "لا توجد منشورات مجدولة.", "sch_deleted_success": "🗑️ تم الحذف.",
            "af_menu_title": "⏱️ *إعدادات منع التكرار*","af_status_button": "🚦 حالة البروتوكول", "af_enabled": "🟢 مفعل", "af_disabled": "🔴 معطل", "af_edit_threshold_button": "⚡️ تعديل عتبة الإزعاج", "af_edit_mute_duration_button": "⏳ تعديل مدة التقييد", "af_ask_for_new_value": "✍️ أرسل القيمة الجديدة.", "af_updated_success": "✅ تم تحديث الإعداد.", "af_mute_notification": "🔇 *تم تقييدك مؤقتاً.*\nبسبب إرسال رسائل سريعة، تم منعك من الإرسال لمدة {duration} دقيقة.", "af_ban_notification": "🚫 *لقد تم حظرك نهائياً.*\nبسبب تكرار السلوك المزعج، تم منعك من استخدام البوت.",
        }
        for key, value in defaults.items():
            await self.texts_collection.update_one({"_id": key}, {"$setOnInsert": {"text": value}}, upsert=True)
        # Add other default settings documents
        await self.settings_collection.update_one({"_id": "security_settings"}, {"$setOnInsert": {"bot_status": "active", "blocked_media": {}}}, upsert=True)
        await self.settings_collection.update_one({"_id": "force_subscribe"}, {"$setOnInsert": {"enabled": True}}, upsert=True)
        await self.settings_collection.update_one({"_id": "antiflood_settings"}, {"$setOnInsert": {"enabled": True, "rate_limit": 7, "time_window": 2, "mute_duration": 30}}, upsert=True)

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
        
    # --- User and Ban Management ---
    async def add_user(self, user) -> bool:
        if not self.is_connected() or await self.users_collection.find_one({"_id": user.id}):
            return False
        await self.users_collection.insert_one({
            "_id": user.id, "first_name": user.first_name, "last_name": user.last_name,
            "username": user.username, "join_date": datetime.utcnow()
        })
        return True

    async def ban_user(self, user_id: int) -> bool:
        if not self.is_connected() or await self.is_user_banned(user_id):
            return False
        await self.banned_users_collection.insert_one({"_id": user_id, "ban_date": datetime.utcnow()})
        return True

    async def unban_user(self, user_id: int) -> bool:
        if not self.is_connected(): return False
        result = await self.banned_users_collection.delete_one({"_id": user_id})
        return result.deleted_count > 0

    # --- 💡 هذه هي الدالة المفقودة التي تم إضافتها لحل المشكلة 💡 ---
    async def is_user_banned(self, user_id: int) -> bool:
        """Checks if a user ID is present in the banned users collection."""
        if not self.is_connected():
            return False
        user_doc = await self.banned_users_collection.find_one({"_id": user_id})
        return user_doc is not None

    # --- Settings Functions (Security, Anti-Flood, etc.) ---
    async def get_security_settings(self):
        if not self.is_connected(): return {}
        return await self.settings_collection.find_one({"_id": "security_settings"}) or {}

    async def get_antiflood_settings(self):
        if not self.is_connected(): return {}
        return await self.settings_collection.find_one({"_id": "antiflood_settings"}) or {}
    
    async def record_antiflood_violation(self, user_id: int):
        if not self.is_connected(): return
        await self.antiflood_violations_collection.update_one(
            {"user_id": user_id},
            {"$inc": {"count": 1}, "$set": {"last_violation": datetime.utcnow()}},
            upsert=True)

    async def get_user_violation_count(self, user_id: int, within_hours: int = 1) -> int:
        if not self.is_connected(): return 0
        threshold = datetime.utcnow() - timedelta(hours=within_hours)
        doc = await self.antiflood_violations_collection.find_one({"user_id": user_id, "last_violation": {"$gte": threshold}})
        return doc.get("count", 0) if doc else 0

    # --- Scheduled Posts Functions ---
    async def add_scheduled_post(self, job_id: str, message_data: dict, target_channels: list, run_date: datetime):
        if not self.is_connected(): return
        await self.scheduled_posts_collection.insert_one({
            "_id": job_id, "message_data": message_data, "target_channels": target_channels,
            "run_date": run_date, "is_sent": False
        })

    async def delete_scheduled_post(self, job_id: str):
        if not self.is_connected(): return
        await self.scheduled_posts_collection.delete_one({"_id": job_id})

    async def get_all_pending_scheduled_posts(self) -> list:
        if not self.is_connected(): return []
        cursor = self.scheduled_posts_collection.find({"is_sent": False, "run_date": {"$gte": datetime.utcnow()}})
        return await cursor.to_list(length=None)
    
    async def mark_scheduled_post_as_sent(self, job_id: str):
        if not self.is_connected(): return
        await self.scheduled_posts_collection.update_one({"_id": job_id}, {"$set": {"is_sent": True}})
        
    # --- Auto Reply Functions ---
    async def find_auto_reply_by_keyword(self, keyword: str) -> dict or None:
        if not self.is_connected(): return None
        return await self.auto_replies_collection.find_one({"keyword": keyword})

    # --- Channel Management ---
    async def get_all_publishing_channels(self) -> list:
        if not self.is_connected(): return []
        cursor = self.publishing_channels_collection.find({})
        return await cursor.to_list(length=None)

    async def get_auto_publication_message(self) -> dict or None:
        if not self.is_connected(): return None
        return await self.settings_collection.find_one({"_id": "auto_publication_message"})

    async def log_message_link(self, admin_message_id: int, user_id: int, user_message_id: int):
        if not self.is_connected(): return
        await self.forwarding_map_collection.insert_one({
            "_id": admin_message_id, "user_id": user_id, "user_message_id": user_message_id
        })
        
    async def get_subscription_channels(self) -> list:
        if not self.is_connected(): return []
        cursor = self.subscription_channels_collection.find({})
        # Return a list of usernames
        return [doc["username"] async for doc in cursor]
        
    async def get_force_subscribe_status(self) -> bool:
        if not self.is_connected(): return True # Default to enabled if DB is down
        doc = await self.settings_collection.find_one({"_id": "force_subscribe"})
        return doc.get("enabled", True) if doc else True

db = DatabaseManager()
