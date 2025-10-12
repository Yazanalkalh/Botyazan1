# -*- coding: utf-8 -*-

import pytz
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ContextTypes, ConversationHandler, CallbackQueryHandler, MessageHandler, filters
)
from bot.database.manager import db

TIMEZONE_ALIASES = {
    "sanaa": "Asia/Aden", "صنعاء": "Asia/Aden", "aden": "Asia/Aden", "عدن": "Asia/Aden",
    "riyadh": "Asia/Riyadh", "الرياض": "Asia/Riyadh", "cairo": "Africa/Cairo", "القاهرة": "Africa/Cairo",
    "dubai": "Asia/Dubai", "دبي": "Asia/Dubai", "kuwait": "Asia/Kuwait", "الكويت": "Asia/Kuwait",
    "qatar": "Asia/Qatar", "قطر": "Asia/Qatar",
}
SELECTING_ACTION, ENTERING_TIMEZONE = range(2)

async def interface_menu_func(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("🌍 تغيير المنطقة الزمنية", callback_data="change_timezone")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel_back")],
    ]
    await query.edit_message_text(text="اختر الإعداد الذي تريد تعديله:", reply_markup=InlineKeyboardMarkup(keyboard))
    return SELECTING_ACTION

async def request_timezone_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    current_timezone = await db.get_timezone()
    await query.edit_message_text(
        text=f"المنطقة الزمنية الحالية هي: `{current_timezone}`\n\n"
             "أرسل الآن المنطقة الزمنية الجديدة.\n"
             "مثال: `Asia/Riyadh` أو يمكنك كتابة اسم المدينة مباشرة مثل `صنعاء`.",
        parse_mode='MarkdownV2'
    )
    return ENTERING_TIMEZONE

async def handle_timezone_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_input = update.message.text.strip()
    normalized_input = user_input.lower()
    timezone_to_check = TIMEZONE_ALIASES.get(normalized_input, user_input)

    try:
        pytz.timezone(timezone_to_check)
        await db.set_timezone(timezone_to_check)
        await update.message.reply_text(
            f"✅ تم تحديث المنطقة الزمنية بنجاح إلى: `{timezone_to_check}`",
            parse_mode='MarkdownV2'
        )
        # العودة إلى قائمة تخصيص الواجهة
        keyboard = [
            [InlineKeyboardButton("🌍 تغيير المنطقة الزمنية", callback_data="change_timezone")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel_back")],
        ]
        await update.message.reply_text(text="اختر الإعداد الذي تريد تعديله:", reply_markup=InlineKeyboardMarkup(keyboard))
        return ConversationHandler.END
    except pytz.UnknownTimeZoneError:
        await update.message.reply_text(
            "عذراً، هذه المنطقة الزمنية غير صالحة. يرجى التأكد من الاسم والمحاولة مرة أخرى."
        )
        return ENTERING_TIMEZONE

def get_interface_handlers():
    change_timezone_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(request_timezone_input, pattern="^change_timezone$")],
        states={
            ENTERING_TIMEZONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_timezone_input)],
        },
        fallbacks=[],
        per_message=False,
        map_to_parent={
            ConversationHandler.END: SELECTING_ACTION
        }
    )
    
    main_menu_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(interface_menu_func, pattern="^customize_interface$")],
        states={
            SELECTING_ACTION: [change_timezone_conv]
        },
        fallbacks=[CallbackQueryHandler(admin_panel_handler, pattern="^admin_panel_back$")],
        per_message=False
    )
    return [main_menu_conv]
