# -*- coding: utf-8 -*-

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
    """
    وظيفة "حارس البوابة": تتحقق مما إذا كان المستخدم مشتركاً في جميع القنوات.
    """
    required_channels = await db.get_subscription_channels()
    if not required_channels:
        return True

    for channel_username in required_channels:
        try:
            member = await bot.get_chat_member(chat_id=f"@{channel_username}", user_id=user_id)
            if member.status not in ["creator", "administrator", "member"]:
                return False
        except (ChatNotFound, BadRequest):
            print(f"تحذير: لا يمكن التحقق من القناة @{channel_username}.")
            continue
    return True

# --- 💡 تم تحديث هذه الدالة بالكامل 💡 ---
async def show_main_menu(message: types.Message, user: types.User, edit_mode: bool = False):
    """
    وظيفة مركزية ومحسّنة لعرض القائمة الرئيسية.
    تدعم الآن الهاشتاقات المخصصة في رسالة الترحيب.
    """
    keyboard = types.InlineKeyboardMarkup(row_width=3)
    date_button_text = await db.get_text("date_button")
    time_button_text = await db.get_text("time_button")
    reminder_button_text = await db.get_text("reminder_button")
    keyboard.add(
        types.InlineKeyboardButton(text=date_button_text, callback_data="show_date"),
        types.InlineKeyboardButton(text=time_button_text, callback_data="show_time"),
        types.InlineKeyboardButton(text=reminder_button_text, callback_data="show_reminder")
    )

    # 1. جلب قالب الرسالة الخام من قاعدة البيانات
    template = await db.get_text("welcome_message")

    # 2. تجهيز القيم التي سيتم استبدالها
    name_user_mention = user.get_mention(as_html=True)  # <a href="tg://user?id=123">الاسم الكامل</a>
    username_mention = f"@{user.username}" if user.username else "لا يوجد"
    first_name = user.first_name
    user_id_str = str(user.id)

    # 3. تنفيذ عملية الاستبدال الذكية
    processed_text = template.replace("#name_user", name_user_mention)
    processed_text = processed_text.replace("#username", username_mention)
    processed_text = processed_text.replace("#name", first_name)
    processed_text = processed_text.replace("#id", user_id_str)
    
    # 4. إرسال الرس النهائية مع استخدام وضع HTML لدعم الروابط والتنسيقات
    if edit_mode:
        try:
            await message.edit_text(text=processed_text, reply_markup=keyboard, parse_mode=types.ParseMode.HTML)
        except Exception:
            pass # نتجاهل الأخطاء مثل "الرسالة لم تتغير"
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
        # 💡 التعديل: نمرر كائن المستخدم للدالة
        await show_main_menu(message, user=user)
    else:
        await show_subscription_message(message)

async def check_subscription_callback(call: types.CallbackQuery):
    """يستجيب لزر "تحقق الآن"."""
    await call.answer(text="جاري التحقق من اشتراكك...", show_alert=False)
    user = call.from_user
    if await is_user_subscribed(user.id, call.bot):
        # 💡 التعديل: نمرر كائن المستخدم للدالة
        await show_main_menu(call.message, user=user, edit_mode=True)
    else:
        await call.answer(text="عذراً، لم تشترك في جميع القنوات بعد. يرجى المحاولة مرة أخرى.", show_alert=True)

def register_start_handlers(dp: Dispatcher):
    """وظيفة التسجيل التلقائي لهذه الوحدة."""
    dp.register_message_handler(start_command, commands=["start"])
    dp.register_callback_query_handler(check_subscription_callback, text="check_subscription")
