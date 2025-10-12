# -*- coding: utf-8 -*-

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from telegram.constants import ChatMemberStatus
from bot.database.manager import db

# --- متغيرات النصوص ---
WELCOME_MESSAGE_KEY = "welcome_message"
FORCE_SUB_MESSAGE_KEY = "force_sub_message"
# ... (بقية مفاتيح الأزرار)
DATE_BUTTON_KEY = "date_button"
TIME_BUTTON_KEY = "time_button"
REMINDER_BUTTON_KEY = "reminder_button"
CONTACT_BUTTON_KEY = "contact_button"


# --- "حارس الأمن" الخبير: وظيفة مركزية للتحقق من الاشتراك ---
async def is_user_subscribed(user_id: int, context: ContextTypes.DEFAULT_TYPE):
    """
    يتحقق مما إذا كان المستخدم مشتركاً في جميع القنوات الإجبارية.
    يعود بقائمة القنوات غير المشترك فيها، أو بقائمة فارغة إذا كان مشتركاً في الكل.
    """
    channels = await db.get_subscription_channels()
    if not channels:
        return []  # لا توجد قنوات اشتراك إجباري، اسمح للمستخدم بالمرور

    not_subscribed_channels = []
    for channel in channels:
        chat_id = channel.get('channel_id_int') or f"@{channel['channel_id']}"
        try:
            member = await context.bot.get_chat_member(chat_id=chat_id, user_id=user_id)
            if member.status not in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
                not_subscribed_channels.append(channel)
        except Exception as e:
            print(f"Error checking subscription for {chat_id} (User: {user_id}): {e}")
            # إذا حدث خطأ (مثل أن البوت ليس مشرفاً)، نعتبر القناة مشكلة
            not_subscribed_channels.append(channel)
            continue
            
    return not_subscribed_channels


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """إرسال رسالة ترحيبية عند إرسال المستخدم /start."""
    user = update.effective_user
    
    # --- استدعاء "حارس الأمن" الخبير ---
    not_subscribed_channels = await is_user_subscribed(user.id, context)
    
    if not_subscribed_channels:
        force_sub_message = await db.get_text(FORCE_SUB_MESSAGE_KEY, "عذراً، يجب عليك الاشتراك في القنوات التالية لاستخدام البوت:")
        
        keyboard = []
        for channel in not_subscribed_channels:
            keyboard.append([InlineKeyboardButton(channel['title'], url=f"https://t.me/{channel['channel_id']}")])
        
        keyboard.append([InlineKeyboardButton("✅ لقد اشتركت، تحقق مرة أخرى", callback_data="check_subscription")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # تعديل الرسالة الحالية أو إرسال جديدة
        if update.callback_query:
            await update.callback_query.message.edit_text(force_sub_message, reply_markup=reply_markup)
        else:
            await update.message.reply_text(force_sub_message, reply_markup=reply_markup)
        return

    # --- إذا كان المستخدم مشتركاً ---
    await db.add_user(user.id, user.first_name, user.username)

    welcome_message = await db.get_text(WELCOME_MESSAGE_KEY, "أهلاً بك في البوت الإسلامي!")
    
    keyboard = [
        [
            InlineKeyboardButton(await db.get_text(DATE_BUTTON_KEY, "📅 التاريخ"), callback_data="show_date"),
            InlineKeyboardButton(await db.get_text(TIME_BUTTON_KEY, "⏰ الساعة الآن"), callback_data="show_time"),
        ],
        [
            InlineKeyboardButton(await db.get_text(REMINDER_BUTTON_KEY, "📿 أذكار اليوم"), callback_data="show_reminder"),
            InlineKeyboardButton(await db.get_text(CONTACT_BUTTON_KEY, "📨 تواصل مع الإدارة"), callback_data="contact_admin"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text_to_send = welcome_message.format(user=user.first_name)
    
    if update.callback_query:
        await update.callback_query.message.edit_text(text_to_send, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text_to_send, reply_markup=reply_markup)


async def check_subscription_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """يعيد تشغيل عملية التحقق."""
    query = update.callback_query
    await query.answer("جاري التحقق من اشتراكك...")
    # استدعاء start مرة أخرى لإعادة التحقق
    await start(update, context)


start_handler = CommandHandler("start", start)
check_subscription_handler = CallbackQueryHandler(check_subscription_callback, pattern="^check_subscription$")
