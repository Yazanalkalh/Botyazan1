# -*- coding: utf-8 -*-

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler
from telegram.constants import ChatMemberStatus
from bot.database.manager import db  # <-- التصحيح: استدعاء المدير db مباشرة

# --- متغيرات ---
# مفاتيح النصوص القابلة للتعديل
WELCOME_MESSAGE_KEY = "welcome_message"
DATE_BUTTON_KEY = "date_button"
TIME_BUTTON_KEY = "time_button"
REMINDER_BUTTON_KEY = "reminder_button"
CONTACT_BUTTON_KEY = "contact_button"
FORCE_SUB_MESSAGE_KEY = "force_sub_message"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """إرسال رسالة ترحيبية عند إرسال المستخدم /start."""
    user = update.effective_user
    
    # --- التحقق من الاشتراك الإجباري ---
    # التصحيح: استدعاء المهارة من المدير db
    channels = await db.get_subscription_channels()
    if channels:
        not_subscribed_channels = []
        for channel in channels:
            try:
                member = await context.bot.get_chat_member(chat_id=f"@{channel['channel_id']}", user_id=user.id)
                if member.status not in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
                    not_subscribed_channels.append(channel)
            except Exception as e:
                print(f"Error checking subscription for @{channel['channel_id']}: {e}")
                # قد يكون البوت ليس مشرفاً في القناة أو المعرف خاطئ
                continue
        
        if not_subscribed_channels:
            # التصحيح: استدعاء المهارة من المدير db
            force_sub_message = await db.get_text(FORCE_SUB_MESSAGE_KEY, "عذراً، يجب عليك الاشتراك في القنوات التالية لاستخدام البوت:")
            
            keyboard = []
            for channel in not_subscribed_channels:
                keyboard.append([InlineKeyboardButton(channel['title'], url=f"https://t.me/{channel['channel_id']}")])
            
            keyboard.append([InlineKeyboardButton("✅ لقد اشتركت، تحقق مرة أخرى", callback_data="check_subscription")])
            
            await update.message.reply_text(
                force_sub_message,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return

    # --- تسجيل المستخدم في قاعدة البيانات ---
    # التصحيح: استدعاء المهارة من المدير db
    await db.add_user(user.id, user.first_name, user.username)

    # --- إرسال الرسالة الترحيبية ---
    # التصحيح: استدعاء المهارة من المدير db
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
    await update.message.reply_text(f"{welcome_message.format(user=user.first_name)}", reply_markup=reply_markup)


async def check_subscription_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """التحقق من الاشتراك مرة أخرى بعد الضغط على الزر."""
    query = update.callback_query
    await query.answer("جاري التحقق من اشتراكك...")
    # إعادة تشغيل منطق /start للتحقق مرة أخرى
    await start(query.message, context)
    # حذف رسالة الاشتراك الإجباري
    await query.message.delete()


start_handler = CommandHandler("start", start)
check_subscription_handler = CallbackQueryHandler(check_subscription_callback, pattern="^check_subscription$")
