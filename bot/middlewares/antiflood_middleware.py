# -*- coding: utf-8 -*-

import logging
from datetime import datetime, timedelta
from aiogram import types, Dispatcher
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.dispatcher.handler import CancelHandler
from aiogram.utils.exceptions import TelegramAPIError

from bot.database.manager import db
from config import ADMIN_USER_ID

logger = logging.getLogger(__name__)

class AntiFloodMiddleware(BaseMiddleware):
    """
    بروتوكول سيربيروس 3.1: إصدار مُصحَح يضمن استمرارية التجاهل (الكتم) بشكل صحيح.
    """
    async def on_pre_process_message(self, message: types.Message, data: dict):
        user = message.from_user
        if not user or user.id == ADMIN_USER_ID:
            return

        settings = await db.get_antiflood_settings()
        if not settings.get("enabled", True):
            return

        dp = Dispatcher.get_current()
        storage = dp.storage
        user_id = user.id
        
        user_data = await storage.get_data(chat=user_id, user=user_id) or {}
        mute_until = user_data.get("mute_until")
        now = datetime.now()

        # الخطوة 1: التحقق مما إذا كان المستخدم قيد التجاهل (الكتم المؤقت)
        # هذا الجزء سيعمل الآن بشكل صحيح لأننا لن نحذف 'mute_until' عن طريق الخطأ
        if mute_until and now < datetime.fromisoformat(mute_until):
            raise CancelHandler() # إذا كان مقيداً، نتجاهل الرسالة تماماً

        timestamps = user_data.get("antiflood_timestamps", [])
        timestamps.append(now)
        rate_limit = settings.get("rate_limit", 7)
        time_window = settings.get("time_window", 2)
        
        recent_timestamps = [ts for ts in timestamps if now - ts < timedelta(seconds=time_window)]

        # الخطوة 2: التحقق من حدوث إزعاج
        if len(recent_timestamps) >= rate_limit:
            # تم اكتشاف إزعاج، لنبدأ بتطبيق العقوبات
            
            # نسجل المخالفة ونحصل على العدد الحالي
            await db.record_antiflood_violation(user_id)
            violation_count = await db.get_user_violation_count(user_id, within_hours=1)
            
            # الخطوة 3: تحديد العقوبة المناسبة
            if violation_count >= 2:
                # --- العقوبة الثانية: الحظر الدائم ---
                await db.ban_user(user_id)
                ban_notification = await db.get_text("af_ban_notification")
                admin_notification_text = f"🚫 تم الحظر التلقائي\n\nالمستخدم: {user.get_mention(as_html=True)} (`{user_id}`)\nالسبب: الإزعاج المتكرر"
                
                try: 
                    await message.answer(ban_notification)
                except TelegramAPIError as e:
                    logger.warning(f"Could not send ban notification to {user_id}: {e}")
                
                keyboard = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("✅ إلغاء الحظر", callback_data=f"bm_unban_direct:{user_id}"))
                await message.bot.send_message(ADMIN_USER_ID, admin_notification_text, reply_markup=keyboard, parse_mode="HTML")
                
                # نمسح بيانات المستخدم من الذاكرة بعد حظره
                await storage.set_data(chat=user_id, user=user_id, data={})

            else:
                # --- العقوبة الأولى: الكتم المؤقت (التجاهل) ---
                mute_duration = settings.get("mute_duration", 30)
                mute_end_time = now + timedelta(minutes=mute_duration)
                
                # نحصل على البيانات الحالية ونضيف إليها وقت التجاهل
                current_data = await storage.get_data(chat=user_id, user=user_id) or {}
                current_data['mute_until'] = mute_end_time.isoformat()
                current_data['antiflood_timestamps'] = [] # نفرغ الطوابع الزمنية بعد العقوبة
                await storage.set_data(chat=user_id, user=user_id, data=current_data)

                mute_notification = (await db.get_text("af_mute_notification")).format(duration=mute_duration)
                admin_notification_text = f"🔇 تم تجاهل المستخدم {user.get_mention(as_html=True)} (`{user_id}`) لمدة {mute_duration} دقيقة."

                try: 
                    await message.answer(mute_notification)
                except TelegramAPIError as e: 
                    logger.warning(f"Could not send mute notification to {user_id}: {e}")

                await message.bot.send_message(ADMIN_USER_ID, admin_notification_text, parse_mode="HTML")

            raise CancelHandler() # نوقف معالجة الرسالة بعد تطبيق العقوبة
        else:
            # --- 💡 بداية الإصلاح النهائي 💡 ---
            # الكود القديم كان يمسح 'mute_until'. الكود الجديد يحافظ عليه.
            # نحضر البيانات الحالية للمستخدم
            current_data = await storage.get_data(chat=user_id, user=user_id) or {}
            # نحدّث فقط قائمة الطوابع الزمنية
            current_data['antiflood_timestamps'] = recent_timestamps
            # نحفظ البيانات المحدثة كاملة دون أن نفقد شيئاً
            await storage.set_data(chat=user_id, user=user_id, data=current_data)
            # --- 💡 نهاية الإصلاح النهائي 💡 ---


def register_direct_unban_handler(dp: Dispatcher):
    """يسجل معالج زر إلغاء الحظر المباشر الذي يظهر في إشعار المدير."""
    async def direct_unban(call: types.CallbackQuery):
        user_id_to_unban = int(call.data.split(":")[-1])
        if await db.unban_user(user_id_to_unban):
            await call.answer(f"✅ تم إلغاء حظر المستخدم {user_id_to_unban}")
            try:
                await call.message.edit_text(call.message.html_text + "\n\n---\n<i>تم إلغاء الحظر بنجاح.</i>", parse_mode="HTML")
            except Exception:
                pass
        else:
            await call.answer("⚠️ المستخدم ليس محظوراً.", show_alert=True)

    dp.register_callback_query_handler(direct_unban, text_startswith="bm_unban_direct:", is_admin=True)
