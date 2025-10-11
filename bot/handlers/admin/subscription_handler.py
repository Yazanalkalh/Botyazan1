# -*- coding: utf-8 -*-

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler

from bot.database.manager import add_subscription_channel, get_all_subscription_channels, delete_subscription_channel

ADDING_CHANNEL = range(1)

async def forced_subscription_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("➕ إضافة قناة", callback_data="add_channel")],
        [InlineKeyboardButton("📋 عرض القنوات", callback_data="view_channels")],
        [InlineKeyboardButton("🔙 رجوع للوحة التحكم", callback_data="admin_panel_back")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.edit_text(
        text="⚙️ قسم إدارة الاشتراك الإجباري.\n\nمن هنا يمكنك التحكم بالقنوات التي يجب على المستخدمين الاشتراك بها لاستخدام البوت.",
        reply_markup=reply_markup
    )

async def request_channel_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.message.edit_text(
        text="أرسل الآن معرف القناة (username) مسبوقاً بـ @\nمثال: @my_channel_username\n\nتنبيه: يجب أن يكون البوت مشرفاً في القناة ليتمكن من التحقق من اشتراك المستخدمين."
    )
    return ADDING_CHANNEL

async def add_channel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    channel_username = update.message.text
    if not channel_username.startswith('@'):
        await update.message.reply_text("خطأ: المعرف يجب أن يبدأ بـ @. حاول مرة أخرى.")
        return ADDING_CHANNEL

    try:
        bot_member = await context.bot.get_chat_member(chat_id=channel_username, user_id=context.bot.id)
        if bot_member.status not in ['administrator', 'creator']:
            await update.message.reply_text("⚠️ البوت ليس مشرفاً في هذه القناة! يرجى رفع البوت كمشرف ثم حاول مرة أخرى.")
            return ConversationHandler.END
    except Exception as e:
        await update.message.reply_text(f"حدث خطأ أثناء التحقق من القناة: {e}\nتأكد من صحة المعرف وأن القناة عامة.")
        return ConversationHandler.END

    add_subscription_channel(channel_username)
    await update.message.reply_text(f"✅ تم إضافة القناة {channel_username} بنجاح إلى قائمة الاشتراك الإجباري.")
    await update.message.reply_text("اضغط /admin للعودة إلى لوحة التحكم.")
    return ConversationHandler.END

async def view_channels_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    channels = get_all_subscription_channels()
    if not channels:
        await update.callback_query.message.edit_text(text="لا توجد قنوات اشتراك إجباري حالياً.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="forced_subscription_menu")]]))
        return

    keyboard = []
    text = "قائمة قنوات الاشتراك الإجباري:\n\n"
    for channel in channels:
        channel_id = str(channel["_id"])
        channel_username = channel["username"]
        text += f"- {channel_username}\n"
        keyboard.append([InlineKeyboardButton(f"🗑️ حذف {channel_username}", callback_data=f"delete_channel_{channel_id}")])
    
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="forced_subscription_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.edit_text(text=text, reply_markup=reply_markup)

async def delete_channel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    channel_id = update.callback_query.data.split('_')[2]
    delete_subscription_channel(channel_id)
    await update.callback_query.answer("✅ تم حذف القناة بنجاح.")
    await view_channels_handler(update, context)


subscription_menu_handler = CallbackQueryHandler(forced_subscription_menu, pattern="^forced_subscription_menu$")
view_channels_main_handler = CallbackQueryHandler(view_channels_handler, pattern="^view_channels$")
delete_channel_main_handler = CallbackQueryHandler(delete_channel_handler, pattern="^delete_channel_")

add_channel_conversation_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(request_channel_info, pattern="^add_channel$")],
    states={ADDING_CHANNEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_channel_handler)]},
    fallbacks=[]
  )
