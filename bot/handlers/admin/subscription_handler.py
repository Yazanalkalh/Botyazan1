# -*- coding: utf-8 -*-

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, CallbackQueryHandler, ConversationHandler, MessageHandler, filters
)
from bot.database.manager import add_subscription_channel, get_subscription_channels, delete_subscription_channel

# --- States for ConversationHandler ---
ADD_CHANNEL_ID, ADD_CHANNEL_LINK = range(2)

# --- Menu Handler ---
async def subscription_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("➕ إضافة قناة جديدة", callback_data="add_sub_channel_start")],
        [InlineKeyboardButton("👀 عرض القنوات الحالية", callback_data="view_sub_channels")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel_back")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text="إدارة قنوات الاشتراك الإجباري:", reply_markup=reply_markup)

# --- View and Delete Handlers ---
async def view_channels_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    channels = await get_subscription_channels()
    if not channels:
        keyboard = [
             [InlineKeyboardButton("➕ إضافة قناة جديدة", callback_data="add_sub_channel_start")],
             [InlineKeyboardButton("🔙 رجوع", callback_data="subscription_panel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("لا توجد قنوات اشتراك إجباري حالياً.", reply_markup=reply_markup)
        return

    text = "قنوات الاشتراك الإجباري الحالية:\n"
    keyboard = []
    for channel in channels:
        keyboard.append([
            InlineKeyboardButton(channel['title'], url=channel['link']),
            InlineKeyboardButton("🗑️ حذف", callback_data=f"delete_sub_channel_{channel['_id']}")]
        )
    keyboard.append([InlineKeyboardButton("➕ إضافة قناة جديدة", callback_data="add_sub_channel_start")])
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="subscription_panel")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup)

async def delete_channel_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    channel_id = int(query.data.split("_")[3])
    await delete_subscription_channel(channel_id)
    await query.answer("✅ تم حذف القناة بنجاح.")
    await view_channels_main(update, context) # Refresh the list

# --- Add Channel Conversation ---
async def add_channel_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [[InlineKeyboardButton("🔙 إلغاء", callback_data="cancel_add_sub_channel")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        "**الخطوة 1 من 2:**\n\nأرسل لي معرف القناة (Channel ID).",
        reply_markup=reply_markup, parse_mode='Markdown'
    )
    return ADD_CHANNEL_ID

async def add_channel_id_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        channel_id = int(update.message.text.strip())
        chat = await context.bot.get_chat(channel_id)
        context.user_data['new_sub_channel_id'] = channel_id
        context.user_data['new_sub_channel_title'] = chat.title

        await update.message.reply_text(
            f"**الخطوة 2 من 2:**\nالآن أرسل رابط الدعوة الخاص بالقناة.",
            parse_mode='Markdown'
        )
        return ADD_CHANNEL_LINK
    except ValueError:
        await update.message.reply_text("المعرف غير صالح. حاول مرة أخرى.")
        return ADD_CHANNEL_ID
    except Exception as e:
        await update.message.reply_text(f"لم أتمكن من الوصول للقناة. تأكد أن البوت مشرف.\nالخطأ: {e}")
        return ADD_CHANNEL_ID

async def add_channel_link_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    channel_link = update.message.text.strip()
    channel_id = context.user_data['new_sub_channel_id']
    channel_title = context.user_data['new_sub_channel_title']

    await add_subscription_channel(channel_id, channel_title, channel_link)
    
    # --- الإصلاح ---
    keyboard = [
        [InlineKeyboardButton("➕ إضافة قناة جديدة", callback_data="add_sub_channel_start")],
        [InlineKeyboardButton("👀 عرض القنوات الحالية", callback_data="view_sub_channels")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel_back")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("✅ تم إضافة القناة بنجاح.\n\nإدارة قنوات الاشتراك الإجباري:", reply_markup=reply_markup)

    context.user_data.clear()
    return ConversationHandler.END

async def cancel_add_sub_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    await subscription_menu(update, context)
    return ConversationHandler.END

# --- Handlers Definition ---
subscription_menu_handler = CallbackQueryHandler(subscription_menu, pattern="^subscription_panel$")
view_channels_main_handler = CallbackQueryHandler(view_channels_main, pattern="^view_sub_channels$")
delete_channel_main_handler = CallbackQueryHandler(delete_channel_main, pattern="^delete_sub_channel_")

add_channel_conversation_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(add_channel_start, pattern="^add_sub_channel_start$")],
    states={
        ADD_CHANNEL_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_channel_id_receive)],
        ADD_CHANNEL_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_channel_link_receive)]
    },
    fallbacks=[CallbackQueryHandler(cancel_add_sub_channel, pattern="^cancel_add_sub_channel$")],
    per_message=False
)
