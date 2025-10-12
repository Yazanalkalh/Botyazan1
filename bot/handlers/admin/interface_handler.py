# -*- coding: utf-8 -*-

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, CallbackQueryHandler, ConversationHandler, MessageHandler, filters
)
from bot.database.manager import set_timezone, get_timezone
import pytz

# --- States for ConversationHandler ---
CHANGE_TIMEZONE = range(1)

# --- Menu Handler ---
async def interface_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("🌍 تغيير المنطقة الزمنية", callback_data="change_timezone_start")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel_back")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text="اختر إعداداً لتخصيص الواجهة:", reply_markup=reply_markup)

# --- Change Timezone Conversation ---
async def change_timezone_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    current_timezone = await get_timezone()
    
    text = (
        f"المنطقة الزمنية الحالية هي: `{current_timezone}`\n\n"
        f"أرسل الآن اسم المنطقة الزمنية الجديدة.\n"
        f"مثال: `Asia/Riyadh` أو `Africa/Cairo`"
    )
    keyboard = [[InlineKeyboardButton("🔙 إلغاء", callback_data="cancel_change_timezone")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    return CHANGE_TIMEZONE

async def change_timezone_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_timezone = update.message.text.strip()
    
    if new_timezone not in pytz.all_timezones:
        await update.message.reply_text("❌ اسم المنطقة الزمنية غير صالح. يرجى المحاولة مرة أخرى.")
        return CHANGE_TIMEZONE

    await set_timezone(new_timezone)
    
    # --- الإصلاح ---
    keyboard = [
        [InlineKeyboardButton("🌍 تغيير المنطقة الزمنية", callback_data="change_timezone_start")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel_back")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(f"✅ تم تحديث المنطقة الزمنية إلى: `{new_timezone}`\n\nاختر إعداداً لتخصيص الواجهة:", reply_markup=reply_markup, parse_mode='Markdown')

    return ConversationHandler.END

async def cancel_change_timezone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await interface_menu(update, context)
    return ConversationHandler.END

# --- Handlers Definition ---
interface_menu_handler = CallbackQueryHandler(interface_menu, pattern="^interface_panel$")

change_timezone_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(change_timezone_start, pattern="^change_timezone_start$")],
    states={
        CHANGE_TIMEZONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, change_timezone_receive)]
    },
    fallbacks=[CallbackQueryHandler(cancel_change_timezone, pattern="^cancel_change_timezone$")],
    per_message=False
)
