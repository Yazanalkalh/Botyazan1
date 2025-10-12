# -*- coding: utf-8 -*-

from aiogram import types, Dispatcher
from aiogram.utils.exceptions import ChatNotFound, BadRequest

from bot.database.manager import db

async def is_user_subscribed(user_id: int, bot: types.Bot) -> bool:
    """
    وظيفة مركزية للتحقق مما إذا كان المستخدم مشتركاً في جميع القنوات الإلزامية.
    """
    required_channels = await db.get_subscription_channels()
    if not required_channels:
        return True # إذا لم تكن هناك قنوات إلزامية، نعتبره مشتركاً

    for channel_username in required_channels:
        try:
            # get_chat_member يتطلب معرّف القناة (username) ومعرّف المستخدم
            member = await bot.get_chat_member(chat_id=f"@{channel_username}", user_id=user_id)
            # التحقق من أن المستخدم ليس خارج القناة أو محظوراً
            if member.status not in ["creator", "administrator", "member"]:
                return False
        except (ChatNotFound, BadRequest):
            # إذا لم يتم العثور على القناة أو كان البوت ليس مشرفاً فيها، نتجاهل هذه القناة
            print(f"Warning: Could not check channel @{channel_username}. Bot might not be an admin or channel is private.")
            continue # يمكنك تغيير هذا السلوك إذا أردت أن يكون الشرط صارماً
    
    return True

async def show_main_menu(message: types.Message, edit_mode: bool = False):
    """
    وظيفة مركزية لعرض القائمة الرئيسية التفاعلية.
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

    welcome_text = (await db.get_text("welcome_message")).format(user_mention=message.chat.get_mention(as_html=True))
    
    # تحديد طريقة الإرسال (تعديل رسالة موجودة أو إرسال جديدة)
    if edit_mode:
        try:
            await message.edit_text(text=welcome_text, reply_markup=keyboard, parse_mode=types.ParseMode.HTML)
        except Exception:
            pass # تجاهل الخطأ إذا لم يتغير محتوى الرسالة
    else:
        await message.answer(text=welcome_text, reply_markup=keyboard, parse_mode=types.ParseMode.HTML)


async def show_subscription_message(message: types.Message):
    """
    يعرض رسالة تطلب من المستخدم الاشتراك في القنوات.
    """
    channels = await db.get_subscription_channels()
    keyboard = types.InlineKeyboardMarkup()
    
    text = "🛑 **عذراً، يجب عليك الاشتراك في القنوات التالية أولاً لاستخدام البوت:**\n\n"
    
    for username in channels:
        text += f"▪️ `@{username}`\n"
        # إضافة زر لكل قناة
        keyboard.add(types.InlineKeyboardButton(text=f"الانضمام إلى @{username}", url=f"https://t.me/{username}"))
        
    # إضافة زر التحقق
    keyboard.add(types.InlineKeyboardButton(text="✅ لقد اشتركت، تحقق الآن", callback_data="check_subscription"))
    
    await message.answer(text, reply_markup=keyboard, parse_mode=types.ParseMode.MARKDOWN)


async def start_command(message: types.Message):
    """
    المعالج الرئيسي لأمر /start.
    يقوم بالتحقق من الاشتراك قبل عرض الواجهة.
    """
    await db.add_user(message.from_user)
    
    if await is_user_subscribed(message.from_user.id, message.bot):
        # إذا كان مشتركاً، اعرض القائمة الرئيسية
        await show_main_menu(message)
    else:
        # إذا لم يكن مشتركاً، اعرض رسالة الاشتراك
        await show_subscription_message(message)


async def check_subscription_callback(call: types.CallbackQuery):
    """
    يتم استدعاؤه عند الضغط على زر "تحقق الآن".
    """
    await call.answer(text="جاري التحقق من اشتراكك...", show_alert=False)
    
    if await is_user_subscribed(call.from_user.id, call.bot):
        # إذا أصبح مشتركاً، قم بتعديل الرسالة لعرض القائمة الرئيسية
        await show_main_menu(call.message, edit_mode=True)
    else:
        # إذا لم يكن مشتركاً بعد، اعرض إشعاراً سريعاً
        await call.answer(text="عذراً، يبدو أنك لم تشترك في جميع القنوات بعد. يرجى المحاولة مرة أخرى.", show_alert=True)


def register_start_handlers(dp: Dispatcher):
    """تسجيل معالجات المستخدم."""
    dp.register_message_handler(start_command, commands=["start"])
    dp.register_callback_query_handler(check_subscription_callback, text="check_subscription")
