# -*- coding: utf-8 -*-

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from telegram.error import BadRequest
from bot.database.manager import add_user, get_subscription_channels, get_text
from config import ADMIN_USER_ID

# --- شرح ---
# هذا الملف مسؤول عن تجربة المستخدم الأولية.
# 1. التحقق من الاشتراك الإجباري.
# 2. تسجيل المستخدم في قاعدة البيانات.
# 3. عرض القائمة الرئيسية بالأزرار المخصصة.

async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """يتحقق مما إذا كان المستخدم مشتركًا في جميع القنوات المطلوبة."""
    user_id = update.effective_user.id
    if user_id == ADMIN_USER_ID:
        return True

    required_channels = await get_subscription_channels()
    if not required_channels:
        return True

    unsubscribed_channels = []
    for channel in required_channels:
        try:
            member = await context.bot.get_chat_member(chat_id=channel["_id"], user_id=user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                unsubscribed_channels.append(channel)
        except BadRequest:
            unsubscribed_channels.append(channel)
            # يمكن إرسال إشعار للمدير بأن هناك مشكلة في إحدى القنوات
            error_text = await get_text("sub_channel_error_admin", "خطأ في قناة الاشتراك: {channel_title}. قد يكون البوت ليس مشرفاً فيها أو المعرف خاطئ.")
            await context.bot.send_message(chat_id=ADMIN_USER_ID, text=error_text.format(channel_title=channel.get('title', 'غير معروف')))
        except Exception:
            unsubscribed_channels.append(channel)

    if unsubscribed_channels:
        buttons = []
        text = await get_text("sub_required_text", "عذراً، يجب عليك الاشتراك في القنوات التالية لاستخدام البوت:\n\n")
        for i, ch in enumerate(unsubscribed_channels):
            text += f"{i+1}. {ch['title']}\n"
            buttons.append([InlineKeyboardButton(f"اشتراك في {ch['title']}", url=ch['link'])])
        
        recheck_button_text = await get_text("sub_recheck_button", "تحققت من الاشتراك")
        buttons.append([InlineKeyboardButton(recheck_button_text, callback_data="recheck_subscription")])
        
        reply_markup = InlineKeyboardMarkup(buttons)
        
        # إذا كان تفاعلًا جديدًا، أرسل رسالة. إذا كان ضغطة زر، عدّل الرسالة.
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
        else:
            await update.message.reply_text(text, reply_markup=reply_markup)
        return False
        
    return True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """يعالج الأمر /start."""
    user = update.effective_user
    # تسجيل المستخدم في قاعدة البيانات
    await add_user(user_id=user.id, full_name=user.full_name, username=user.username)

    if not await check_subscription(update, context):
        return

    # جلب النصوص المخصصة من قاعدة البيانات
    welcome_text = await get_text("welcome_message", "أهلاً بك في بوت الخير!\nاستخدم الأزرار أدناه للحصول على المعلومات.")
    date_button_text = await get_text("date_button", "📅 التاريخ")
    time_button_text = await get_text("time_button", "⏰ الساعة الآن")
    reminder_button_text = await get_text("reminder_button", "📿 أذكار اليوم")
    contact_button_text = await get_text("contact_button", "📨 تواصل مع الإدارة")

    keyboard = [
        [InlineKeyboardButton(date_button_text, callback_data='show_date'), InlineKeyboardButton(time_button_text, callback_data='show_time')],
        [InlineKeyboardButton(reminder_button_text, callback_data='show_reminder')],
        [InlineKeyboardButton(contact_button_text, callback_data='contact_admin')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text.format(user=user.full_name), reply_markup=reply_markup)

async def recheck_subscription_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """يعيد التحقق من الاشتراك بعد ضغط المستخدم على الزر."""
    await update.callback_query.answer("جاري التحقق...")
    if await check_subscription(update, context):
        # إذا تم الاشتراك، احذف رسالة الاشتراك وأرسل القائمة الرئيسية
        await update.callback_query.delete_message()
        # محاكاة أمر /start جديد لإرسال القائمة الرئيسية
        # إنشاء كائن update مزيف ليبدو كأنه رسالة جديدة
        from unittest.mock import Mock
        fake_update = Mock()
        fake_update.effective_user = update.effective_user
        fake_update.message = update.callback_query.message 
        await start(fake_update, context)

async def contact_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """يخبر المستخدم بكيفية التواصل مع الإدارة."""
    contact_prompt_text = await get_text("contact_prompt", "تفضل بإرسال رسالتك الآن (نص، صورة، فيديو...) وسيتم توصيلها مباشرة إلى الإدارة.")
    
    # التحقق من الاشتراك أولاً
    if not await check_subscription(update, context):
        return
        
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(contact_prompt_text)
    else:
        await update.message.reply_text(contact_prompt_text)


start_handler = CommandHandler("start", start)
recheck_subscription_callback_handler = CallbackQueryHandler(recheck_subscription_callback, pattern="^recheck_subscription$")
contact_admin_handler = CallbackQueryHandler(contact_admin_command, pattern="^contact_admin$")
