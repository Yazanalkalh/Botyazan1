# -*- coding: utf-8 -*-

import math
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ContextTypes, ConversationHandler, CallbackQueryHandler, MessageHandler, filters
)
from bot.database.manager import db

# --- состояний ---
ADDING_CHANNEL = 1
PAGE_SIZE = 10

async def subscription_menu_handler_func(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("➕ إضافة قناة جديدة", callback_data="add_sub_channel")],
        [InlineKeyboardButton("📋 عرض القنوات الحالية", callback_data="view_sub_channels_1")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel_back")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text="إدارة قنوات الاشتراك الإجباري:", reply_markup=reply_markup)

async def request_channel_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "أرسل الآن معرف القناة (username) بدون @، أو قم بإعادة توجيه أي رسالة من القناة إلى هنا."
    )
    return ADDING_CHANNEL

async def handle_channel_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    channel_id = None
    channel_title = None

    if update.message.forward_from_chat:
        chat = update.message.forward_from_chat
        if chat.type == 'channel':
            channel_id = f"@{chat.username}" if chat.username else str(chat.id)
            channel_title = chat.title
    elif update.message.text:
        text = update.message.text.strip()
        channel_id = f"@{text.replace('@', '')}"
        try:
            chat = await context.bot.get_chat(channel_id)
            channel_title = chat.title
        except Exception as e:
            await update.message.reply_text(f"لم أتمكن من العثور على القناة. الخطأ: {e}")
            return ADDING_CHANNEL
    
    if channel_id and channel_title:
        await db.add_subscription_channel(channel_id, channel_title)
        await update.message.reply_text(f"✅ تم إضافة القناة '{channel_title}' بنجاح!")
    else:
        await update.message.reply_text("لم أتمكن من تحديد القناة. يرجى المحاولة مرة أخرى.")
        return ADDING_CHANNEL
        
    # العودة إلى قائمة الاشتراك
    keyboard = [
        [InlineKeyboardButton("➕ إضافة قناة جديدة", callback_data="add_sub_channel")],
        [InlineKeyboardButton("📋 عرض القنوات الحالية", callback_data="view_sub_channels_1")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel_back")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text="إدارة قنوات الاشتراك الإجباري:", reply_markup=reply_markup)
    return ConversationHandler.END

async def view_subscription_channels_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    page = int(query.data.split('_')[-1])

    total_channels = await db.get_subscription_channels_count()
    total_pages = math.ceil(total_channels / PAGE_SIZE)
    channels = await db.get_subscription_channels_page(page, PAGE_SIZE)

    text = f"قنوات الاشتراك (صفحة {page} من {total_pages}):\n\n"
    keyboard = []
    if not channels:
        text += "لا توجد قنوات مضافة."
    else:
        for channel in channels:
            keyboard.append([InlineKeyboardButton(f"🗑️ {channel['title']}", callback_data=f"del_sub_{channel['_id']}_{page}")])

    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton("◀️ السابق", callback_data=f"view_sub_channels_{page-1}"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton("التالي ▶️", callback_data=f"view_sub_channels_{page+1}"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)

    keyboard.append([
        InlineKeyboardButton("➕ إضافة المزيد", callback_data="add_sub_channel"),
        InlineKeyboardButton("🔙 رجوع", callback_data="subscription_menu_back")
    ])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup)

async def delete_subscription_channel_handler_func(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split('_')
    channel_id = parts[2]
    page_to_return = int(parts[3])
    await db.delete_subscription_channel(channel_id)
    context.callback_data = f"view_sub_channels_{page_to_return}"
    await view_subscription_channels_page(update, context)

def get_subscription_handlers():
    add_channel_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(request_channel_input, pattern="^add_sub_channel$")],
        states={ADDING_CHANNEL: [MessageHandler(filters.TEXT | filters.FORWARDED, handle_channel_input)]},
        fallbacks=[],
        per_message=False
    )
    return [
        CallbackQueryHandler(subscription_menu_handler_func, pattern="^subscription_menu$"),
        CallbackQueryHandler(subscription_menu_handler_func, pattern="^subscription_menu_back$"),
        CallbackQueryHandler(view_subscription_channels_page, pattern="^view_sub_channels_"),
        CallbackQueryHandler(delete_subscription_channel_handler_func, pattern="^del_sub_"),
        add_channel_conv,
    ]
