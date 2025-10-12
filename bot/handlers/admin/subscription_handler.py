# -*- coding: utf-8 -*-

import math
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler, CallbackQueryHandler, MessageHandler, filters
)
from bot.database.manager import db

# --- состояний ---
SELECTING_ACTION, ADDING_CHANNEL = range(2)
CHANNELS_PER_PAGE = 8 # عدد القنوات في كل صفحة

async def subscription_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """يعرض قائمة التحكم بالاشتراك الإجباري."""
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("➕ إضافة قناة", callback_data="add_sub_channel")],
        [InlineKeyboardButton("👁️ عرض القنوات", callback_data="view_sub_channels_page_1")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel_back")],
    ]
    
    await query.edit_message_text(
        text="اختر الإجراء المتعلق بقنوات الاشتراك الإجباري:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return SELECTING_ACTION

# --- منطق عرض الصفحات ---
async def view_channels_page(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """يعرض صفحة محددة من قنوات الاشتراك."""
    query = update.callback_query
    await query.answer()
    
    page = int(query.data.split('_')[-1])

    total_channels = await db.count_subscription_channels()
    if total_channels == 0:
        await query.edit_message_text(
            text="لم يتم إضافة أي قنوات للاشتراك الإجباري بعد.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ إضافة قناة", callback_data="add_sub_channel")],
                [InlineKeyboardButton("🔙 رجوع", callback_data="subscription_menu_back")]
            ])
        )
        return SELECTING_ACTION

    total_pages = math.ceil(total_channels / CHANNELS_PER_PAGE)
    channels_on_page = await db.get_subscription_channels_by_page(page=page, limit=CHANNELS_PER_PAGE)

    keyboard = []
    for channel in channels_on_page:
        keyboard.append([
            InlineKeyboardButton(f"@{channel['channel_username']}", url=f"https://t.me/{channel['channel_username']}"),
            InlineKeyboardButton("🗑️", callback_data=f"delete_sub_channel_{channel['channel_id']}_{page}")
        ])

    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton("◀️ السابق", callback_data=f"view_sub_channels_page_{page-1}"))
    
    nav_buttons.append(InlineKeyboardButton(f"صفحة {page}/{total_pages}", callback_data="noop"))

    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton("التالي ▶️", callback_data=f"view_sub_channels_page_{page+1}"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)

    keyboard.append([
        InlineKeyboardButton("➕ إضافة المزيد", callback_data="add_sub_channel"),
        InlineKeyboardButton("🔙 رجوع", callback_data="subscription_menu_back")
    ])

    await query.edit_message_text(
        text=f"قائمة قنوات الاشتراك الإجباري (صفحة {page}):",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return SELECTING_ACTION

# --- منطق الحذف ---
async def delete_channel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """يحذف قناة ويعيد عرض الصفحة الحالية."""
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split('_')
    channel_id = int(parts[3])
    page_to_return = int(parts[4])

    await db.delete_subscription_channel(channel_id)

    context.callback_query.data = f"view_sub_channels_page_{page_to_return}"
    return await view_channels_page(update, context)


# --- منطق الإضافة ---
async def request_channel_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="أرسل الآن معرف القناة (مثال: @mychannel).")
    return ADDING_CHANNEL

async def handle_channel_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    channel_username = update.message.text.strip().replace('@', '')
    
    try:
        chat = await context.bot.get_chat(f"@{channel_username}")
        await db.add_subscription_channel(chat.id, channel_username)
        await update.message.reply_text(f"✅ تم إضافة القناة @{channel_username} بنجاح.")
    except Exception as e:
        await update.message.reply_text(f"لم أتمكن من العثور على القناة أو لست مشرفاً فيها. الخطأ: {e}")

    from bot.handlers.admin.main_panel import subscription_menu_callback
    await subscription_menu_callback(update, context)
    return ConversationHandler.END


# --- بناء المعالجات ---
subscription_menu_handler = CallbackQueryHandler(subscription_menu, pattern="^force_subscribe$")
subscription_menu_back_handler = CallbackQueryHandler(subscription_menu, pattern="^subscription_menu_back$")

# معالج جديد لصفحات القنوات
subscription_page_handler = CallbackQueryHandler(view_channels_page, pattern=r"^view_sub_channels_page_\d+$")
delete_subscription_channel_handler = CallbackQueryHandler(delete_channel, pattern=r"^delete_sub_channel_.+_\d+$")


add_channel_conversation_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(request_channel_input, pattern="^add_sub_channel$")],
    states={
        ADDING_CHANNEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_channel_input)],
    },
    fallbacks=[],
    per_message=False
)
