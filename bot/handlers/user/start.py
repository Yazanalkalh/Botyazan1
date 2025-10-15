# -*- coding: utf-8 -*-

import asyncio

from aiogram import types, Dispatcher, Bot
from aiogram.utils.exceptions import ChatNotFound, BadRequest

from bot.database.manager import db
from config import ADMIN_USER_ID

async def notify_admin_of_new_user(user: types.User, bot: Bot):
    """يرسل إشعاراً للمدير عند دخول مستخدم جديد."""
    try:
        user_link = f'<a href="tg://user?id={user.id}">{user.full_name}</a>'
        username = f"@{user.username}" if user.username else "لا يوجد"
        
        notification_text = (
            f"👤 <b>دخل شخص جديد إلى البوت</b>\n\n"
            f"🗣️ <b>اسمه:</b> {user_link}\n"
            f"🌀 <b>معرفه:</b> {username}\n"
            f"🆔 <b>ايديه:</b> <code>{user.id}</code>"
        )
        
        await bot.send_message(
            chat_id=ADMIN_USER_ID,
            text=notification_text,
            parse_mode=types.ParseMode.HTML
        )
    except Exception as e:
        print(f"فشل إرسال إشعار المستخدم الجديد: {e}")

async def is_user_subscribed(user_id: int, bot: Bot) -> bool:
    """وظيفة "حارس البوابة" فائقة السرعة للتحقق من الاشتراكات بشكل متوازٍ."""
    is_enabled = await db.get_force_subscribe_status()
    if not is_enabled:
        return True

    required_channels = await db.get_subscription_channels()
    if not required_channels:
        return True

    async def check_channel(channel_username: str):
        try:
            member = await bot.get_chat_member(chat_id=f"@{channel_username}", user_id=user_id)
            return member.status in ["creator", "administrator", "member"]
        except (ChatNotFound, BadRequest):
            print(f"تحذير: لا يمكن التحقق من القناة @{channel_username}. سنتجاوزها مؤقتاً.")
            return True

    tasks = [check_channel(channel) for channel in required_channels]
    subscription_statuses = await asyncio.gather(*tasks)
    return all(subscription_statuses)

# --- 💡 تم تحديث هذه الدالة بالكامل لتصبح أسرع 💡 ---
async def show_main_menu(message: types.Message, user: types.User, edit_mode: bool = False):
    """
    وظيفة مركزية فائقة السرعة لعرض القائمة الرئيسية.
    تقوم بجلب كل النصوص المطلوبة من قاعدة البيانات دفعة واحدة.
    """
    keyboard = types.InlineKeyboardMarkup(row_width=3)
    
    # --- بداية التحسين: جلب كل نصوص القائمة دفعة واحدة ---
    texts_to_fetch = [
        "date_button",
        "time_button",
        "reminder_button",
        "welcome_message"
    ]
    # نستخدم asyncio.gather لجلب كل النصوص في نفس الوقت بدلاً من انتظار كل واحد على حدة
    # هذا يجعل عرض القائمة الرئيسية وزر "العودة" شبه فوري
    results = await asyncio.gather(*(db.get_text(text_key) for text_key in texts_to_fetch))

    # الآن نوزع النصوص التي حصلنا عليها على المتغيرات الخاصة بها بالترتيب
    date_button_text, time_button_text, reminder_button_text, template = results
    # --- نهاية التحسين ---

    keyboard.add(
        types.InlineKeyboardButton(text=date_button_text, callback_data="show_date"),
        types.InlineKeyboardButton(text=time_button_text, callback_data="show_time"),
        types.InlineKeyboardButton(text=reminder_button_text, callback_data="show_reminder")
    )

    name_user_mention = user.get_mention(as_html=True)
    username_mention = f"@{user.username}" if user.username else "لا يوجد"
    first_name = user.first_name
    user_id_str = str(user.id)

    processed_text = template.replace("#name_user", name_user_mention)
    processed_text = processed_text.replace("#username", username_mention)
    processed_text = processed_text.replace("#name", first_name)
    processed_text = processed_text.replace("#id", user_id_str)
    
    if edit_mode:
        try:
            await message.edit_text(text=processed_text, reply_markup=keyboard, parse_mode=types.ParseMode.HTML)
        except Exception:
            pass # نتجنب أي خطأ قد يحدث إذا كانت الرسالة لم تتغير
    else:
        await message.answer(text=processed_text, reply_markup=keyboard, parse_mode=types.ParseMode.HTML)

async def show_subscription_message(message: types.Message):
    """يعرض رسالة وقنوات الاشتراك الإجباري."""
    channels = await db.get_subscription_channels()
    keyboard = types.InlineKeyboardMarkup()
    text = "🛑 <b>عذراً، يجب عليك الاشتراك في القنوات التالية أولاً لاستخدام البوت:</b>\n\n"
    for username in channels:
        text += f"▪️ @{username}\n"
        keyboard.add(types.InlineKeyboardButton(text=f"الانضمام إلى @{username}", url=f"https://t.me/{username}"))
    keyboard.add(types.InlineKeyboardButton(text="✅ لقد اشتركت، تحقق الآن", callback_data="check_subscription"))
    await message.answer(text, reply_markup=keyboard, parse_mode=types.ParseMode.HTML)

async def start_command(message: types.Message):
    """المعالج الرئيسي لأمر /start."""
    user = message.from_user
    is_new = await db.add_user(user)
    if is_new:
        await notify_admin_of_new_user(user, message.bot)
    
    if await is_user_subscribed(user.id, message.bot):
        await show_main_menu(message, user=user)
    else:
        await show_subscription_message(message)

async def check_subscription_callback(call: types.CallbackQuery):
    """يستجيب لزر "تحقق الآن"."""
    await call.answer(text="جاري التحقق من اشتراكك...", show_alert=False)
    user = call.from_user
    if await is_user_subscribed(user.id, call.bot):
        await show_main_menu(call.message, user=user, edit_mode=True)
    else:
        await call.answer(text="عذراً، لم تشترك في جميع القنوات بعد. يرجى المحاولة مرة أخرى.", show_alert=True)

def register_start_handlers(dp: Dispatcher):
    """وظيفة التسجيل التلقائي لهذه الوحدة."""
    dp.register_message_handler(start_command, commands=["start"])
    dp.register_callback_query_handler(check_subscription_callback, text="check_subscription")
