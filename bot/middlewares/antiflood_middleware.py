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
    بروتوكول سيربيروس 2.3: الإصدار النهائي مع ترتيب منطقي صحيح لفترة التهدئة.
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
        
        user_data = await storage.get_data(chat=user_id, user=user_id)
        timestamps = user_data.get("antiflood_timestamps", [])
        last_punishment_time = user_data.get("last_punishment_time")

        now = datetime.now()
        
        timestamps.append(now)

        rate_limit = settings.get("rate_limit", 7)
        time_window = settings.get("time_window", 2)
        
        recent_timestamps = [
            ts for ts in timestamps
            if now - ts < timedelta(seconds=time_window)
        ]

        # --- 💡 الإصلاح الجذري: إعادة ترتيب المنطق بالكامل 💡 ---
        if len(recent_timestamps) >= rate_limit:
            # تم اكتشاف حدث إزعاج. الآن نتحقق من فترة التهدئة.
            
            # 1. التحقق من فترة المناعة (التهدئة)
            if last_punishment_time and (now - last_punishment_time < timedelta(seconds=10)):
                # نحن في فترة التهدئة، تجاهل الرسالة بهدوء وامنعها من الوصول لأي مكان آخر.
                raise CancelHandler()

            # 2. إذا لم نكن في فترة التهدئة، فهذه مخالفة جديدة تستحق العقاب.
            # نبدأ الإجراءات ونسجل وقت العقوبة لمنح "المناعة" للمخالفات التالية.
            await storage.set_data(chat=user_id, user=user_id, data={"antiflood_timestamps": [], "last_punishment_time": now})
            
            await db.record_antiflood_violation(user_id)
            violation_count = await db.get_user_violation_count(user_id, within_hours=1)
            
            if violation_count >= 2: # المخالفة الثانية خلال ساعة = حظر
                await db.ban_user(user_id)
                ban_notification = await db.get_text("af_ban_notification")
                admin_notification_text = f"🚫 تم الحظر التلقائي\n\nالمستخدم: {user.get_mention(as_html=True)} (`{user_id}`)\nالسبب: الإزعاج المتكرر"
                
                try: await message.answer(ban_notification)
                except Exception: pass
                
                keyboard = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("✅ إلغاء الحظر", callback_data=f"bm_unban_direct:{user_id}"))
                await message.bot.send_message(ADMIN_USER_ID, admin_notification_text, reply_markup=keyboard, parse_mode="HTML")

            else: # المخالفة الأولى = تقييد
                mute_duration = settings.get("mute_duration", 30)
                mute_end_time = now + timedelta(minutes=mute_duration)
                
                mute_notification = (await db.get_text("af_mute_notification")).format(duration=mute_duration)
                admin_notification_text = f"🔇 تم تقييد المستخدم {user.get_mention(as_html=True)} (`{user_id}`) لمدة {mute_duration} دقيقة."

                try:
                    await message.bot.restrict_chat_member(
                        chat_id=message.chat.id,
                        user_id=user_id,
                        permissions=types.ChatPermissions(can_send_messages=False),
                        until_date=mute_end_time
                    )
                    await message.answer(mute_notification)
                except Exception as e:
                    logger.error(f"Failed to mute user {user_id}: {e}")

                await message.bot.send_message(ADMIN_USER_ID, admin_notification_text, parse_mode="HTML")

            raise CancelHandler()
        else:
            # إذا لم يتم تجاوز الحد، نقوم بتحديث الذاكرة المركزية بالسجل النظيف
            await storage.update_data(chat=user_id, user=user_id, data={"antiflood_timestamps": recent_timestamps})

# (بقية الملف تبقى كما هي)
def register_direct_unban_handler(dp: Dispatcher):
    async def direct_unban(call: types.CallbackQuery):
        user_id_to_unban = int(call.data.split(":")[-1])
        if await db.unban_user(user_id_to_unban):
            await call.answer(f"✅ تم إلغاء حظر المستخدم {user_id_to_unban}")
            try:
                await call.message.edit_text(call.message.html_text + "\n\n---\n<i>تم إلغاء الحظر بنجاح.</i>")
            except Exception:
                pass
        else:
            await call.answer("⚠️ المستخدم ليس محظوراً.", show_alert=True)

    dp.register_callback_query_handler(direct_unban, text_startswith="bm_unban_direct:", is_admin=True)
