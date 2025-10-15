# -*- coding: utf-8 -*-

import logging
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure
from bson.objectid import ObjectId
import datetime
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
        defaults = {
            "admin_panel_title": "أهلاً بك في لوحة التحكم.", "welcome_message": "أهلاً بك يا #name_user!", "date_button": "📅 التاريخ", "time_button": "⏰ الساعة الآن", "reminder_button": "📿 أذكار اليوم",
            "user_message_received": "✅ تم استلام رسالتك بنجاح، سيتم الرد عليك قريباً.",
            "ar_menu_title": "⚙️ *إدارة الردود التلقائية*", "ar_add_button": "➕ إضافة رد", "ar_view_button": "📖 عرض الردود", "ar_import_button": "📥 استيراد", "ar_back_button": "⬅️ عودة", "ar_ask_for_keyword": "📝 أرسل *الكلمة المفتاحية*", "ar_ask_for_content": "📝 أرسل *محتوى الرد*", "ar_added_success": "✅ تم الحفظ!", "ar_add_another_button": "➕ إضافة المزيد", "ar_ask_for_file": "📦 أرسل ملف `.txt`.", "ar_import_success": "✅ اكتمل.", "ar_no_replies": "لا توجد ردود.", "ar_deleted_success": "🗑️ تم الحذف.", "ar_page_info": "صفحة {current_page}/{total_pages}", "ar_next_button": "التالي ⬅️", "ar_prev_button": "➡️ السابق", "ar_delete_button": "🗑️ حذف",
            "rem_menu_title": "⏰ *إدارة التذكيرات*", "rem_add_button": "➕ إضافة", "rem_view_button": "📖 عرض", "rem_import_button": "📥 استيراد", "rem_ask_for_content": "📝 أرسل *نص التذكير*.", "rem_added_success": "✅ تم الحفظ!", "rem_add_another_button": "➕ إضافة المزيد", "rem_ask_for_file": "📦 أرسل ملف `.txt`.", "rem_import_success": "✅ اكتمل.", "rem_no_reminders": "لا توجد تذكيرات.", "rem_deleted_success": "🗑️ تم الحذف.", "rem_delete_button": "🗑️ حذف",
            "cp_menu_title": "📰 *إدارة منشورات القناة*", "cp_set_auto_msg_button": "✍️ تعيين الرسالة", "cp_view_auto_msg_button": "👀 عرض الرسالة", "cp_publish_now_button": "🚀 نشر الآن", "cp_schedule_button": "🗓️ جدولة منشور", "cp_view_scheduled_button": "👀 عرض المجدولة", "cp_ask_for_auto_msg": "📝 أرسل الرسالة.", "cp_auto_msg_set_success": "✅ تم الحفظ.", "cp_no_auto_msg": "لم يتم تعيين رسالة.", "cp_auto_msg_deleted_success": "🗑️ تم الحذف.", "cp_publish_started": "🚀 جاري النشر...", "cp_publish_finished": "🏁 اكتمل النشر!", "cp_error_no_auto_msg_to_publish": "⚠️ لا توجد رسالة!", "cp_error_no_channels_to_publish": "⚠️ لا توجد قنوات!",
            "cm_menu_title": "📡 *إدارة القنوات*", "cm_add_button": "➕ إضافة قناة", "cm_view_button": "📖 عرض القنوات", "cm_ask_for_channel_id": "📡 أرسل معرّف القناة.", "cm_add_success": "✅ تم الإضافة!", "cm_add_fail_not_admin": "❌ فشل.", "cm_add_fail_invalid_id": "❌ فشل.", "cm_add_fail_already_exists": "⚠️ مضافة بالفعل.", "cm_no_channels": "لا توجد قنوات.", "cm_deleted_success": "🗑️ تم الحذف.", "cm_test_button": "🔬 تجربة", "cm_test_success": "✅ نجح.", "cm_test_fail": "❌ فشل.",
            "bm_menu_title": "🚫 *إدارة الحظر*", "bm_ban_button": "🚫 حظر", "bm_unban_button": "✅ إلغاء حظر", "bm_view_button": "📖 عرض", "bm_ask_for_user_id": "🆔 أرسل ID.", "bm_ask_for_unban_user_id": "🆔 أرسل ID.", "bm_user_banned_success": "🚫 تم الحظر.", "bm_user_already_banned": "⚠️ محظور بالفعل.", "bm_user_unbanned_success": "✅ تم إلغاء الحظر.", "bm_user_not_banned": "⚠️ ليس محظوراً.", "bm_invalid_user_id": "❌ ID غير صالح.", "bm_no_banned_users": "لا يوجد محظورين.",
            "bc_ask_for_message": "📣 *نشر للجميع*", "bc_confirmation": "⏳ متأكد؟", "bc_confirm_button": "✅ نعم", "bc_cancel_button": "❌ إلغاء", "bc_started": "🚀 بدأت النشر...", "bc_progress": "⏳ جاري النشر...", "bc_finished": "🏁 اكتمل النشر!",
            "ui_menu_title": "🎨 *تخصيص الواجهة*", "ui_edit_date_button": "📅 تعديل زر التاريخ", "ui_edit_time_button": "⏰ تعديل زر الساعة", "ui_edit_reminder_button": "📿 تعديل زر الأذكار", "ui_edit_timezone_button": "🌍 تعديل المنطقة الزمنية", "ui_ask_for_new_text": "📝 أرسل النص الجديد.", "ui_text_updated_success": "✅ تم التحديث.", "ui_ask_for_tz_identifier": "🌐 أرسل معرّف المنطقة الزمنية.", "ui_ask_for_tz_display_name": "✍️ أرسل اسم العرض.", "ui_tz_updated_success": "✅ تم التحديث.",
            "sec_menu_title": "🛡️ *الحماية والأمان*", "sec_bot_status_button": "🤖 حالة البوت", "sec_media_filtering_button": "🖼️ منع الوسائط", "sec_antiflood_button": "⏱️ منع التكرار", "sec_rejection_message_button": "✍️ تعديل رسالة الرفض", "sec_bot_active": "🟢 يعمل", "sec_bot_inactive": "🔴 متوقف", "sec_media_menu_title": "🖼️ *منع الوسائط*", "sec_media_photo": "🖼️ الصور", "sec_media_video": "📹 الفيديو", "sec_media_link": "🔗 الروابط", "sec_media_sticker": "🎭 الملصقات", "sec_media_document": "📁 الملفات", "sec_media_audio": "🎵 الصوتيات", "sec_media_voice": "🎤 الرسائل الصوتية", "sec_allowed": "✅ مسموح", "sec_blocked": "❌ ممنوع", "sec_rejection_msg_ask": "✍️ أرسل رسالة الرفض.", "sec_rejection_msg_updated": "✅ تم التحديث.", "security_rejection_message": "عذراً، هذا غير مسموح.",
            "mm_menu_title": "🗑️ *إدارة الذاكرة*", "mm_clear_user_state_button": "👤 حذف ذاكرة", "mm_ask_for_user_id": "🆔 أرسل ID.", "mm_state_cleared_success": "✅ تم الحذف.", "mm_state_not_found": "ℹ️ لا توجد ذاكرة.",
            "stats_title": "📊 *إحصائيات البوت*", "stats_total_users": "👤 المستخدمون", "stats_banned_users": "🚫 المحظورون", "stats_auto_replies": "📝 الردود", "stats_reminders": "⏰ التذكيرات", "stats_refresh_button": "🔄 تحديث",
            "lib_menu_title": "📚 *إدارة المكتبة*", "lib_add_button": "➕ إضافة", "lib_view_button": "📖 عرض", "lib_ask_for_item": "📥 أرسل أي رسالة.", "lib_item_saved": "✅ تم الحفظ.", "lib_no_items": "🗄️ فارغة.", "lib_deleted_success": "🗑️ تم الحذف.", "lib_item_info": "عنصر {current_item}/{total_items}",
            "fs_menu_title": "🔗 *الاشتراك الإجباري*", "fs_status_button": "🚦 الحالة", "fs_add_button": "➕ إضافة قناة", "fs_view_button": "📖 عرض القنوات", "fs_enabled": "🟢 مفعل", "fs_disabled": "🔴 معطل", "fs_ask_for_channel_id": "📡 أرسل معرّف القناة.", "fs_add_success": "✅ تم الإضافة!", "fs_add_fail_not_admin": "❌ فشل.", "fs_no_channels": "لا توجد قنوات.", "fs_deleted_success": "🗑️ تم الحذف.",
            "sm_title": "🖥️ *مراقبة النظام*", "sm_status_ok": "🟢 كل الأنظمة تعمل.", "sm_status_degraded": "🟡 مشاكل.", "sm_health_checks": "المؤشرات الحيوية", "sm_performance": "الأداء", "sm_deploy_info": "معلومات النشر", "sm_bot_status": "حالة البوت", "sm_db_status": "قاعدة البيانات", "sm_uptime": "مدة التشغيل", "sm_tg_latency": "استجابة تيليجرام", "sm_last_update": "آخر تحديث", "sm_status_operational": "يعمل", "sm_status_connected": "متصل", "sm_status_unreachable": "غير متصل",
            "te_menu_title": "✍️ *محرر النصوص*", "te_ask_for_new_text": "📝 أرسل النص الجديد.", "te_updated_success": "✅ تم التحديث!",
            "sch_ask_for_message": "📝 أرسل المنشور للجدولة.", "sch_ask_for_channels": "📡 اختر القنوات.", "sch_all_channels_button": "📢 كل القنوات", "sch_ask_for_datetime": "⏰ أرسل تاريخ ووقت النشر `YYYY-MM-DD HH:MM`.", "sch_invalid_datetime": "❌ صيغة التاريخ خاطئة.", "sch_datetime_in_past": "❌ لا يمكن الجدولة في الماضي.", "sch_add_success": "✅ تم جدولة المنشور.", "sch_no_jobs": "لا توجد منشورات مجدولة.", "sch_deleted_success": "🗑️ تم الحذف.",
            "af_menu_title": "⏱️ *إعدادات منع التكرار*", "af_status_button": "🚦 حالة البروتوكول", "af_enabled": "🟢 مفعل", "af_disabled": "🔴 معطل", "af_edit_threshold_button": "⚡️ تعديل عتبة الإزعاج", "af_edit_mute_duration_button": "⏳ تعديل مدة التقييد", "af_ask_for_new_value": "✍️ أرسل القيمة الجديدة.", "af_updated_success": "✅ تم التحديث.", "af_mute_notification": "🔇 *تم تقييدك مؤقتاً.*\nبسبب إرسال رسائل سريعة، تم منعك من الإرسال لمدة {duration} دقيقة.", "af_ban_notification": "🚫 *لقد تم حظرك نهائياً.*\nبسبب تكرار السلوك المزعج، تم منعك من استخدام البوت.",
        }
        for key, value in defaults.items():
            await self.texts_collection.update_one({"_id": key}, {"$setOnInsert": {"text": value}}, upsert=True)
        await self.settings_collection.update_one({"_id": "timezone"}, {"$setOnInsert": {"identifier": "Asia/Riyadh", "display_name": "بتوقيت الرياض"}}, upsert=True)
        default_security = {"bot_status": "active", "blocked_media": {}}
        await self.settings_collection.update_one({"_id": "security_settings"}, {"$setOnInsert": default_security}, upsert=True)
        await self.settings_collection.update_one({"_id": "force_subscribe"}, {"$setOnInsert": {"enabled": True}}, upsert=True)
        default_antiflood = {"enabled": True, "rate_limit": 7, "time_window": 2, "mute_duration": 30}
        await self.settings_collection.update_one({"_id": "antiflood_settings"}, {"$setOnInsert": default_antiflood}, upsert=True)

    async def load_texts_into_cache(self):
        if not self.is_connected(): return
        logger.info("🚀 Caching all UI texts...")
        cursor = self.texts_collection.find({}, {"_id": 1, "text": 1})
        async for doc in cursor: TEXTS_CACHE[doc['_id']] = doc.get('text', f"[{doc['_id']}]")
        logger.info(f"✅ Cached {len(TEXTS_CACHE)} text items.")

    async def get_text(self, text_id: str) -> str:
        return TEXTS_CACHE.get(text_id, f"[{text_id}]")

    async def update_text(self, text_id: str, new_text: str):
        if not self.is_connected(): return
        await self.texts_collection.update_one({"_id": text_id}, {"$set": {"text": new_text}}, upsert=True)
        TEXTS_CACHE[text_id] = new_text
        
    async def add_scheduled_post(self, job_id: str, message_data: dict, target_channels: list, run_date: datetime.datetime):
        if not self.is_connected(): return
        await self.scheduled_posts_collection.insert_one({"_id": job_id, "message_data": message_data, "target_channels": target_channels, "run_date": run_date, "status": "pending"})

    async def get_scheduled_posts(self, page: int = 1, limit: int = 10):
        if not self.is_connected(): return []
        return await self.scheduled_posts_collection.find({"status": "pending"}).sort("run_date", 1).skip((page - 1) * limit).limit(limit).to_list(length=limit)

    async def get_scheduled_posts_count(self) -> int:
        if not self.is_connected(): return 0
        return await self.scheduled_posts_collection.count_documents({"status": "pending"})

    async def delete_scheduled_post(self, job_id: str):
        if not self.is_connected(): return False
        result = await self.scheduled_posts_collection.delete_one({"_id": job_id})
        return result.deleted_count > 0
        
    async def get_all_pending_scheduled_posts(self):
        if not self.is_connected(): return []
        return await self.scheduled_posts_collection.find({"status": "pending"}).to_list(length=None)

    async def mark_scheduled_post_as_done(self, job_id: str):
        if not self.is_connected(): return
        await self.scheduled_posts_collection.update_one({"_id": job_id}, {"$set": {"status": "done"}})
        
    async def get_all_editable_texts(self):
        if not self.is_connected(): return []
        cursor = self.texts_collection.find({}, {"_id": 1})
        docs = await cursor.sort("_id", 1).to_list(length=None)
        return [doc['_id'] for doc in docs]
        
    async def ping_database(self) -> bool:
        if not self.client: return False
        try:
            await self.client.admin.command("ping")
            return True
        except ConnectionFailure: return False
        
    async def get_auto_replies_count(self):
        if not self.is_connected(): return 0
        return await self.auto_replies_collection.count_documents({})
        
    async def get_reminders_count(self):
        if not self.is_connected(): return 0
        return await self.reminders_collection.count_documents({})
        
    async def get_publishing_channels_count(self):
        if not self.is_connected(): return 0
        return await self.publishing_channels_collection.count_documents({})
        
    async def get_banned_users_count(self):
        if not self.is_connected(): return 0
        return await self.banned_users_collection.count_documents({})
        
    async def get_bot_statistics(self) -> dict:
        if not self.is_connected(): return {}
        tasks = [
            self.users_collection.count_documents({}),
            self.banned_users_collection.count_documents({}),
            self.auto_replies_collection.count_documents({}),
            self.reminders_collection.count_documents({})
        ]
        results = await asyncio.gather(*tasks)
        return {"total_users": results[0], "banned_users": results[1], "auto_replies": results[2], "reminders": results[3]}
    
    async def ban_user(self, user_id: int):
        if not self.is_connected(): return False
        if await self.is_user_banned(user_id): return False
        await self.banned_users_collection.insert_one({"_id": user_id, "ban_date": datetime.datetime.utcnow()})
        return True
        
    async def unban_user(self, user_id: int):
        if not self.is_connected(): return False
        result = await self.banned_users_collection.delete_one({"_id": user_id})
        await self.clear_user_violations(user_id) # العفو الشامل
        return result.deleted_count > 0

    async def is_user_banned(self, user_id: int) -> bool:
        if not self.is_connected(): return False
        return await self.banned_users_collection.count_documents({"_id": user_id}) > 0
        
    async def get_antiflood_settings(self):
        if not self.is_connected(): return {}
        doc = await self.settings_collection.find_one({"_id": "antiflood_settings"})
        return doc or {}

    async def update_antiflood_setting(self, key: str, value):
        if not self.is_connected(): return
        valid_keys = ["enabled", "rate_limit", "time_window", "mute_duration"]
        if key not in valid_keys: return
        await self.settings_collection.update_one({"_id": "antiflood_settings"}, {"$set": {key: value}}, upsert=True)
        
    async def record_antiflood_violation(self, user_id: int):
        if not self.is_connected(): return
        await self.antiflood_violations_collection.insert_one({"user_id": user_id, "timestamp": datetime.datetime.utcnow()})

    async def get_user_violation_count(self, user_id: int, within_hours: int = 1) -> int:
        if not self.is_connected(): return 0
        time_threshold = datetime.datetime.utcnow() - datetime.timedelta(hours=within_hours)
        return await self.antiflood_violations_collection.count_documents({"user_id": user_id, "timestamp": {"$gte": time_threshold}})
    
    async def clear_user_violations(self, user_id: int):
        if not self.is_connected(): return
        await self.antiflood_violations_collection.delete_many({"user_id": user_id})
    
    # ... (all other functions like get_all_users, etc.)
    async def find_auto_reply_by_keyword(self, keyword: str):
        if not self.is_connected(): return None
        return await self.auto_replies_collection.find_one({"keyword_lower": keyword.lower()})
    async def get_auto_replies(self, page: int = 1, limit: int = 10):
        if not self.is_connected(): return []
        return await self.auto_replies_collection.find().skip((page - 1) * limit).limit(limit).to_list(length=limit)
    async def delete_auto_reply(self, reply_id: str):
        if not self.is_connected(): return False
        try:
            result = await self.auto_replies_collection.delete_one({"_id": ObjectId(reply_id)})
            return result.deleted_count > 0
        except Exception: return False
    async def add_reminder(self, text: str):
        if not self.is_connected(): return
        await self.reminders_collection.insert_one({"text": text})
    async def get_reminders(self, page: int = 1, limit: int = 10):
        if not self.is_connected(): return []
        return await self.reminders_collection.find().skip((page - 1) * limit).limit(limit).to_list(length=limit)
    async def delete_reminder(self, reminder_id: str):
        if not self.is_connected(): return False
        try:
            result = await self.reminders_collection.delete_one({"_id": ObjectId(reminder_id)})
            return result.deleted_count > 0
        except Exception: return False
    async def set_auto_publication_message(self, message_data: dict):
        if not self.is_connected(): return
        await self.settings_collection.update_one({"_id": "auto_publication_message"}, {"$set": {"message": message_data}}, upsert=True)
    async def delete_auto_publication_message(self):
        if not self.is_connected(): return False
        result = await self.settings_collection.delete_one({"_id": "auto_publication_message"})
        return result.deleted_count > 0
    async def add_publishing_channel(self, channel_id: int, channel_title: str):
        if not self.is_connected(): return None
        await self.publishing_channels_collection.update_one({"channel_id": channel_id}, {"$set": {"title": channel_title}}, upsert=True)
    async def get_publishing_channels(self, page: int = 1, limit: int = 10):
        if not self.is_connected(): return []
        return await self.publishing_channels_collection.find().skip((page - 1) * limit).limit(limit).to_list(length=limit)
    async def get_banned_users(self, page: int = 1, limit: int = 10):
        if not self.is_connected(): return []
        return await self.banned_users_collection.find().skip((page - 1) * limit).limit(limit).to_list(length=limit)
    async def add_to_library(self, message: dict):
        if not self.is_connected(): return
        await self.library_collection.insert_one({"message": message, "added_date": datetime.datetime.utcnow()})
    async def get_library_items(self, page: int = 1, limit: int = 5):
        if not self.is_connected(): return []
        return await self.library_collection.find().sort("added_date", -1).skip((page-1)*limit).limit(limit).to_list(length=limit)
    async def get_library_items_count(self):
        if not self.is_connected(): return 0
        return await self.library_collection.count_documents({})
    async def delete_library_item(self, item_id: str):
        if not self.is_connected(): return False
        try:
            result = await self.library_collection.delete_one({"_id": ObjectId(item_id)})
            return result.deleted_count > 0
        except Exception: return False
    async def add_subscription_channel(self, channel_id: int, channel_title: str, username: str):
        if not self.is_connected(): return
        await self.subscription_channels_collection.update_one({"channel_id": channel_id}, {"$set": {"title": channel_title, "username": username}}, upsert=True)
    async def get_all_subscription_channels_docs(self):
        if not self.is_connected(): return []
        return await self.subscription_channels_collection.find().to_list(length=None)
    async def delete_subscription_channel(self, db_id: str):
        if not self.is_connected(): return False
        try:
            result = await self.subscription_channels_collection.delete_one({"_id": ObjectId(db_id)})
            return result.deleted_count > 0
        except Exception: return False
    async def get_force_subscribe_status(self) -> bool:
        if not self.is_connected(): return True
        doc = await self.settings_collection.find_one({"_id": "force_subscribe"})
        return doc.get("enabled", True) if doc else True
    async def toggle_force_subscribe_status(self):
        if not self.is_connected(): return
        current_status = await self.get_force_subscribe_status()
        await self.settings_collection.update_one({"_id": "force_subscribe"}, {"$set": {"enabled": not current_status}}, upsert=True)
        return not current_status
    async def log_message_link(self, admin_message_id: int, user_id: int, user_message_id: int):
        if not self.is_connected(): return
        await self.forwarding_map_collection.insert_one({"_id": admin_message_id, "user_id": user_id, "user_message_id": user_message_id})
    async def get_message_link_info(self, admin_message_id: int):
        if not self.is_connected(): return None
        return await self.forwarding_map_collection.find_one({"_id": admin_message_id})
    async def add_user(self, user) -> bool:
        if not self.is_connected(): return False
        user_data = {'first_name': user.first_name or "", 'last_name': getattr(user, 'last_name', "") or "", 'username': user.username or ""}
        result = await self.users_collection.update_one({'user_id': user.id}, {'$set': user_data, '$setOnInsert': {'user_id': user.id}}, upsert=True)
        return result.upserted_id is not None
    async def get_random_reminder(self) -> str:
        if not self.is_connected(): return "لا توجد أذكار حالياً."
        pipeline = [{"$sample": {"size": 1}}]
        async for doc in self.reminders_collection.aggregate(pipeline): return doc.get("text", "لا توجد أذكار حالياً.")
        return "لا توجد أذكار حالياً."
    async def get_subscription_channels(self) -> list[str]:
        if not self.is_connected(): return []
        channels_cursor = self.subscription_channels_collection.find({}, {"_id": 0, "username": 1})
        channels_list = await channels_cursor.to_list(length=None)
        return [ch["username"] for ch in channels_list if ch.get("username")]
        
db = DatabaseManager()
