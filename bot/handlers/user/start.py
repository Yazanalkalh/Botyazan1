# -*- coding: utf-8 -*-

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler

# --- شرح ---
# هنا نقوم بتعريف الأزرار التي تظهر للمستخدم العادي
keyboard = [
    [
        InlineKeyboardButton("📅 التاريخ", callback_data='show_date'),
        InlineKeyboardButton("⏰ الساعة الآن", callback_data='show_time'),
    ],
    [
        InlineKeyboardButton("📿 أذكار اليوم", callback_data='show_reminder'),
    ]
]
reply_markup = InlineKeyboardMarkup(keyboard)

# هذه الدالة يتم استدعاؤها عندما يرسل المستخدم الأمر /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    welcome_message = f"أهلاً بك يا {user.mention_html()} في البوت الإسلامي."
    
    await update.message.reply_html(welcome_message, reply_markup=reply_markup)

# ربط الأمر /start بالدالة الخاصة به
start_handler = CommandHandler('start', start)
