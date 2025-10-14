# -*- coding: utf-8 -*-

import logging
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure
from bson.objectid import ObjectId
import datetime
import asyncio

# --- نستورد ذاكرة التوربو ---
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
            # --- الإضافة الجديدة: مجموعة المنشورات المجدولة ---
            self.scheduled_posts_collection = self.db.scheduled_posts
            
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
            # ... (جميع النصوص السابقة موجودة هنا)
            "admin_panel_title": "أهلاً بك في لوحة التحكم.",
            "welcome_message": "أهلاً بك يا #name_user!", "date_button": "📅 التاريخ", "time_button": "⏰ الساعة الآن", "reminder_button": "📿 أذكار اليوم",
            "ar_menu_title": "⚙️ *إدارة الردود التلقائية*", "ar_add_button": "➕ إضافة رد", "ar_view_button": "📖 عرض الردود", "ar_import_button": "📥 استيراد", "ar_back_button": "⬅️ عودة", "ar_ask_for_keyword": "📝 أرسل *الكلمة المفتاحية*", "ar_ask_for_content": "📝 أرسل *محتوى الرد*", "ar_added_success": "✅ تم الحفظ!", "ar_add_another_button": "➕ إضافة المزيد", "ar_ask_for_file": "📦 أرسل ملف `.txt`.", "ar_import_success": "✅ اكتمل.", "ar_no_replies": "لا توجد ردود.", "ar_deleted_success": "🗑️ تم الحذف.", "ar_page_info": "صفحة {current_page}/{total_pages}", "ar_next_button": "التالي ⬅️", "ar_prev_button": "➡️ السابق", "ar_delete_button": "🗑️ حذف",
            "rem_menu_title": "⏰ *إدارة التذكيرات*", "rem_add_button": "➕ إضافة", "rem_view_button": "📖 عرض", "rem_import_button": "📥 استيراد", "rem_ask_for_content": "📝 أرسل *نص التذكير*.", "rem_added_success": "✅ تم الحفظ!", "rem_add_another_button": "➕ إضافة المزيد", "rem_ask_for_file": "📦 أرسل ملف `.txt`.", "rem_import_success": "✅ اكتمل.", "rem_no_reminders": "لا توجد تذكيرات.", "rem_deleted_success": "🗑️ تم الحذف.", "rem_delete_button": "🗑️ حذف",
            "cp_menu_title": "📰 *إدارة منشورات القناة*", "cp_set_auto_msg_button": "✍️ تعيين الرسالة", "cp_view_auto_msg_button": "👀 عرض الرسالة", "cp_publish_now_button": "🚀 نشر الآن", "cp_ask_for_auto_msg": "📝 أرسل الرسالة.", "cp_auto_msg_set_success": "✅ تم الحفظ.", "cp_no_auto_msg": "لم يتم تعيين رسالة.", "cp_auto_msg_deleted_success": "🗑️ تم الحذف.", "cp_publish_started": "🚀 جاري النشر...", "cp_publish_finished": "🏁 اكتمل النشر!", "cp_error_no_auto_msg_to_publish": "⚠️ لا توجد رسالة!", "cp_error_no_channels_to_publish": "⚠️ لا توجد قنوات!",
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

            # --- الإضافة الجديدة: نصوص واجهة جدولة المنشورات ---
            "cp_schedule_button": "🗓️ جدولة منشور",
            "cp_view_scheduled_button": "👀 عرض المجدولة",
            "sch_ask_for_message": "📝 *الخطوة 1:* أرسل الآن المنشور الذي تريد جدولته.",
            "sch_ask_for_channels": "📡 *الخطوة 2:* اختر القنوات التي تريد النشر فيها.",
            "sch_all_channels_button": "📢 كل القنوات",
            "sch_ask_for_datetime": "⏰ *الخطوة 3:* أرسل تاريخ ووقت النشر بالصيغة التالية:\n`YYYY-MM-DD HH:MM`\nمثال: `2024-12-31 22:30`",
            "sch_invalid_datetime": "❌ صيغة التاريخ والوقت غير صالحة. يرجى استخدام الصيغة `YYYY-MM-DD HH:MM`.",
            "sch_datetime_in_past": "❌ لا يمكن الجدولة في وقت قد مضى. يرجى إدخال وقت مستقبلي.",
            "sch_add_success": "✅ تم جدولة المنشور بنجاح ليتم نشره في `{run_date}`.",
            "sch_no_jobs": "لا توجد أي منشورات مجدولة حالياً.",
            "sch_deleted_success": "🗑️ تم حذف المنشور المجدول بنجاح.",
        }
        for key, value in defaults.items():
            await self.texts_collection.update_one({"_id": key}, {"$setOnInsert": {"text": value}}, upsert=True)
        await self.settings_collection.update_one({"_id": "timezone"}, {"$setOnInsert": {"identifier": "Asia/Riyadh", "display_name": "بتوقيت الرياض"}}, upsert=True)
        default_security = {"bot_status": "active", "blocked_media": {}}
        await self.settings_collection.update_one({"_id": "security_settings"}, {"$setOnInsert": default_security}, upsert=True)
        await self.settings_collection.update_one({"_id": "force_subscribe"}, {"$setOnInsert": {"enabled": True}}, upsert=True)

    # --- (الوظائف السابقة موجودة هنا دون تغيير) ---
    # ...
        
    # --- الإضافة الجديدة: وظائف جدولة المنشورات ---
    async def add_scheduled_post(self, job_id: str, message_data: dict, target_channels: list, run_date: datetime.datetime):
        """يحفظ معلومات المنشور المجدول في قاعدة البيانات."""
        if not self.is_connected(): return
        await self.scheduled_posts_collection.insert_one({
            "_id": job_id,
            "message_data": message_data,
            "target_channels": target_channels,
            "run_date": run_date,
            "status": "pending"
        })

    async def get_scheduled_posts(self, page: int = 1, limit: int = 10):
        """يجلب قائمة المنشورات المجدولة مع تقسيم الصفحات."""
        if not self.is_connected(): return []
        return await self.scheduled_posts_collection.find({"status": "pending"}).sort("run_date", 1).skip((page - 1) * limit).limit(limit).to_list(length=limit)

    async def get_scheduled_posts_count(self) -> int:
        """يحسب عدد المنشورات المجدولة."""
        if not self.is_connected(): return 0
        return await self.scheduled_posts_collection.count_documents({"status": "pending"})

    async def delete_scheduled_post(self, job_id: str):
        """يحذف منشوراً مجدولاً من قاعدة البيانات."""
        if not self.is_connected(): return False
        result = await self.scheduled_posts_collection.delete_one({"_id": job_id})
        return result.deleted_count > 0
        
    async def get_all_pending_scheduled_posts(self):
        """يجلب كل المنشورات المجدولة التي لم يتم تنفيذها بعد (عند إعادة تشغيل البوت)."""
        if not self.is_connected(): return []
        return await self.scheduled_posts_collection.find({"status": "pending"}).to_list(length=None)

    async def mark_scheduled_post_as_done(self, job_id: str):
        """يضع علامة 'منفذ' على المنشور المجدول."""
        if not self.is_connected(): return
        await self.scheduled_posts_collection.update_one({"_id": job_id}, {"$set": {"status": "done"}})

    # --- (بقية الوظائف موجودة هنا دون تغيير) ---
    # ...
    db = DatabaseManager()
