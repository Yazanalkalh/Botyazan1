# -*- coding: utf-8 -*-

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.constants import ChatMemberStatus

# استيراد وظيفة تسجيل المستخدم
from bot.database.manager import get_all_subscription_channels, get_setting, add_or_update_user

async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user_id = update.effective_user.id
    required_channels = get_all_subscription_channels()
    
    if not required_channels:
        return True

    unsubscribed_channels = []
    for channel in required_channels:
        channel_username = channel['username']
        try:
            member = await context.bot.get_chat_member(chat_id=channel_username, user_id=user_id)
            if member.status in [ChatMemberStatus.LEFT, ChatMemberStatus.KICKED]:
                unsubscribed_channels.append(channel_username)
        except Exception:
            unsubscribed_channels.append(channel_username)
            continue
            
    if unsubscribed_channels:
        keyboard = []
        text = "عذراً، يجب عليك الاشتراك في القنوات التالية أولاً لاستخدام البوت:\n\n"
        for i, ch in enumerate(unsubscribed_channels, 1):
            text += f"{i}- {ch}\n"
            keyboard.append([InlineKeyboardButton(f"الانضمام إلى {ch}", url=f"https://t.me/{ch.replace('@', '')}")])
        
        keyboard.append([InlineKeyboardButton("🔄 لقد اشتركت، تحقق الآن", callback_data="check_subscription_again")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.message.edit_text(text, reply_markup=reply_markup)
        else:
            await update.message.reply_text(text, reply_markup=reply_markup)
        return False

    return True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # --- جديد: تسجيل أو تحديث بيانات المستخدم في قاعدة البيانات ---
    add_or_update_user(
        user_id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        username=user.username
    )
    
    if not await check_subscription(update, context):
        return

    user_mention = user.mention_html()

    welcome_message = get_setting("text_welcome", "أهلاً بك يا {user_mention} في بوت الخير!")
    btn_date_text = get_setting("btn_date", "📅 التاريخ")
    btn_time_text = get_setting("btn_time", "⏰ الساعة الآن")
    btn_reminder_text = get_setting("btn_reminder", "📿 أذكار اليوم")
    btn_contact_text = get_setting("btn_contact", "📨 تواصل مع الإدارة") # زر جديد

    keyboard = [
        [InlineKeyboardButton(btn_date_text, callback_data='show_date')],
        [InlineKeyboardButton(btn_time_text, callback_data='show_time')],
        [InlineKeyboardButton(btn_reminder_text, callback_data='show_reminder')],
        [InlineKeyboardButton(btn_contact_text, callback_data='contact_admin')] # زر جديد
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    final_message = welcome_message.format(user_mention=user_mention)
    
    if update.callback_query: # إذا كان قادماً من زر "التحقق"
        await update.callback_query.message.edit_text(final_message, reply_markup=reply_markup, parse_mode='HTML')
    else:
        await update.message.reply_text(final_message, reply_markup=reply_markup, parse_mode='HTML')


async def recheck_subscription_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # بعد التحقق، نقوم باستدعاء وظيفة start لعرض القائمة الرئيسية إذا نجح
    if await check_subscription(update, context):
        await start(update, context)

# معالج زر التواصل مع الإدارة
async def contact_admin_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """يستجيب لزر التواصل ويرسل إرشادات للمستخدم."""
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("تفضل بإرسال رسالتك الآن (نص، صورة، ملصق...) وسيتم توصيلها إلى الإدارة مباشرة.")


start_handler = CommandHandler("start", start)
recheck_subscription_callback_handler = CallbackQueryHandler(recheck_subscription_handler, pattern="^check_subscription_again$")
contact_admin_handler = CallbackQueryHandler(contact_admin_button_handler, pattern="^contact_admin$")
