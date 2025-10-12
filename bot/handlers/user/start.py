# -*- coding: utf-8 -*-

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from telegram.constants import ChatMemberStatus
from bot.database.manager import db

# --- وظيفة التحقق من الاشتراك (مركزية) ---
async def is_user_subscribed(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    channels = await db.get_subscription_channels()
    if not channels:
        return True  # لا توجد قنوات للاشتراك، اسمح بالمرور
    
    for channel in channels:
        try:
            member = await context.bot.get_chat_member(chat_id=channel['_id'], user_id=user_id)
            if member.status not in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
                return False  # المستخدم ليس عضواً في إحدى القنوات
        except Exception:
            # إذا حدث خطأ (مثل عدم وجود البوت في القناة)، اعتبر المستخدم غير مشترك
            return False
    return True # المستخدم مشترك في جميع القنوات

# --- معالج أمر البدء ---
async def start_handler_func(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    
    # تسجيل المستخدم في قاعدة البيانات
    await db.add_user(user_id=user.id, first_name=user.first_name, username=user.username)

    # التحقق من الاشتراك
    if not await is_user_subscribed(user.id, context):
        channels = await db.get_subscription_channels()
        text = "عذراً، يجب عليك الاشتراك في القنوات التالية أولاً لاستخدام البوت:\n\n"
        keyboard = []
        for channel in channels:
            try:
                # محاولة الحصول على رابط القناة
                chat = await context.bot.get_chat(channel['_id'])
                invite_link = chat.invite_link
                if not invite_link: # إذا لم يكن هناك رابط دعوة، استخدم رابط t.me
                    invite_link = f"https://t.me/{chat.username}"
                keyboard.append([InlineKeyboardButton(channel['title'], url=invite_link)])
            except Exception:
                # في حالة فشل الحصول على معلومات القناة، اعرض المعرف فقط
                keyboard.append([InlineKeyboardButton(channel['title'], url=f"https://t.me/{channel['_id'][1:]}")]) # إزالة @
        
        keyboard.append([InlineKeyboardButton("تحققت من الاشتراك", callback_data="check_subscription")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(text, reply_markup=reply_markup)
        return

    # إذا كان المستخدم مشتركاً، اعرض الواجهة الرئيسية
    welcome_text = await db.get_text('welcome_message', "أهلاً بك في بوت التقويم الإسلامي!")
    date_button_text = await db.get_text('date_button', "📅 التاريخ")
    time_button_text = await db.get_text('time_button', "⏰ الساعة الآن")
    reminder_button_text = await db.get_text('reminder_button', "📿 أذكار اليوم")
    contact_button_text = await db.get_text('contact_button', "📨 تواصل مع الإدارة")

    keyboard = [
        [InlineKeyboardButton(date_button_text, callback_data="show_date")],
        [InlineKeyboardButton(time_button_text, callback_data="show_time")],
        [InlineKeyboardButton(reminder_button_text, callback_data="show_reminder")],
        [InlineKeyboardButton(contact_button_text, callback_data="contact_admin")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

# --- معالج زر التحقق ---
async def check_subscription_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user = query.effective_user
    
    if await is_user_subscribed(user.id, context):
        await query.answer("شكراً لاشتراكك! يمكنك الآن استخدام البوت.", show_alert=True)
        # إزالة رسالة الاشتراك وعرض الواجهة الرئيسية
        await query.delete_message()
        
        # إعادة إرسال الواجهة الرئيسية
        welcome_text = await db.get_text('welcome_message', "أهلاً بك في بوت التقويم الإسلامي!")
        date_button_text = await db.get_text('date_button', "📅 التاريخ")
        time_button_text = await db.get_text('time_button', "⏰ الساعة الآن")
        reminder_button_text = await db.get_text('reminder_button', "📿 أذكار اليوم")
        contact_button_text = await db.get_text('contact_button', "📨 تواصل مع الإدارة")

        keyboard = [
            [InlineKeyboardButton(date_button_text, callback_data="show_date")],
            [InlineKeyboardButton(time_button_text, callback_data="show_time")],
            [InlineKeyboardButton(reminder_button_text, callback_data="show_reminder")],
            [InlineKeyboardButton(contact_button_text, callback_data="contact_admin")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(welcome_text, reply_markup=reply_markup)
    else:
        await query.answer("عذراً، يبدو أنك لم تشترك في جميع القنوات بعد. يرجى المحاولة مرة أخرى.", show_alert=True)

start_handler = CommandHandler("start", start_handler_func)
check_subscription_handler = CallbackQueryHandler(check_subscription_callback, pattern="^check_subscription$")
