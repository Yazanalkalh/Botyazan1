# -*- coding: utf-8 -*-

import asyncio
from collections import defaultdict
from datetime import datetime, timedelta
from aiogram import types, Dispatcher
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.dispatcher.handler import CancelHandler
from aiogram.utils.exceptions import TelegramAPIError

from bot.database.manager import db
from config import ADMIN_USER_ID

# ذاكرة مؤقتة لتتبع رسائل المستخدمين بسرعة
user_messages = defaultdict(list)

class AntiFloodMiddleware(BaseMiddleware):
    """
    بروتوكول سيربيروس: الحارس ثلاثي الرؤوس.
    """
    async def on_pre_process_message(self, message: types.Message, data: dict):
        user = message.from_user
        if user.id == ADMIN_USER_ID:
            return

        settings = await db.get_antiflood_settings()
        if not settings.get("enabled", True):
            return

        now = datetime.now()
        user_id = user.id
        
        # إضافة الطابع الزمني للرسالة الحالية
        user_messages[user_id].append(now)

        # تنظيف الطوابع الزمنية القديمة
        rate_limit = settings.get("rate_limit", 7)
        time_window = settings.get("time_window", 2)
        
        user_messages[user_id] = [
            msg_time for msg_time in user_messages[user_id]
            if now - msg_time < timedelta(seconds=time_window)
        ]

        # --- الرأس الأول والثاني: المراقب والمنفذ ---
        if len(user_messages[user_id]) >= rate_limit:
            # منع الرسالة الحالية
            del user_messages[user_id][-1]
            
            # تسجيل مخالفة
            await db.record_antiflood_violation(user_id)
            violation_count = await db.get_user_violation_count(user_id)
            
            # --- الرأس الثالث: القاضي ---
            if violation_count >= 2: # المخالفة الثانية = حظر
                await db.ban_user(user_id)
                ban_notification = await db.get_text("af_ban_notification")
                admin_notification_text = f"🚫 تم الحظر التلقائي\n\nالمستخدم: {user.get_mention(as_html=True)} (`{user_id}`)\nالسبب: الإزعاج المتكرر"
                
                try: await message.answer(ban_notification)
                except Exception: pass
                
                keyboard = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("✅ إلغاء الحظر", callback_data=f"bm_unban_direct:{user_id}"))
                await message.bot.send_message(ADMIN_USER_ID, admin_notification_text, reply_markup=keyboard, parse_mode="HTML")

            else: # المخالفة الأولى = تقييد
                mute_duration = settings.get("mute_duration", 30)
                mute_end_time = datetime.now() + timedelta(minutes=mute_duration)
                
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

# دالة مساعدة لتسجيل معالج زر إلغاء الحظر المباشر
def register_direct_unban_handler(dp: Dispatcher):
    async def direct_unban(call: types.CallbackQuery):
        user_id_to_unban = int(call.data.split(":")[-1])
        if await db.unban_user(user_id_to_unban):
            await call.answer(f"✅ تم إلغاء حظر المستخدم {user_id_to_unban}")
            await call.message.edit_text(call.message.text + "\n\n---\n*تم إلغاء الحظر بنجاح.*")
        else:
            await call.answer("⚠️ المستخدم ليس محظوراً.", show_alert=True)

    dp.register_callback_query_handler(direct_unban, text_startswith="bm_unban_direct:", is_admin=True)
