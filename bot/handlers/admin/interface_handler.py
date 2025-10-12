# -*- coding: utf-8 -*-

import pytz
from telegram import Update
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler, CallbackQueryHandler, MessageHandler, filters
)
from bot.database.manager import db
from bot.handlers.admin.main_panel import admin_panel_handler

# --- قاموس لترجمة الأسماء الشائعة إلى المناطق الزمنية الرسمية ---
TIMEZONE_ALIASES = {
    "sanaa": "Asia/Aden",
    "صنعاء": "Asia/Aden",
    "aden": "Asia/Aden",
    "عدن": "Asia/Aden",
    "riyadh": "Asia/Riyadh",
    "الرياض": "Asia/Riyadh",
    "cairo": "Africa/Cairo",
    "القاهرة": "Africa/Cairo",
    "dubai": "Asia/Dubai",
    "دبي": "Asia/Dubai",
    "kuwait": "Asia/Kuwait",
    "الكويت": "Asia/Kuwait",
    "qatar": "Asia/Qatar",
    "قطر": "Asia/Qatar",
    # يمكن إضافة المزيد من المرادفات هنا
}

# --- состояний ---
SELECTING_ACTION, ENTERING_TIMEZONE = range(2)

async def interface_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """يعرض قائمة تخصيص الواجهة."""
    query = update.callback_query
    await query.answer()

    keyboard = [
        [CallbackQueryHandler("🌍 تغيير المنطقة الزمنية", "change_timezone")],
        [CallbackQueryHandler("🔙 رجوع", "admin_panel_back")],
    ]
    
    await query.edit_message_text(
        text="اختر الإعداد الذي تريد تعديله:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return SELECTING_ACTION

async def request_timezone_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """يطلب من المدير إدخال المنطقة الزمنية الجديدة."""
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
    """يعالج إدخال المنطقة الزمنية ويحفظها."""
    user_input = update.message.text.strip()
    
    # تحويل الإدخال إلى حروف صغيرة للبحث في القاموس
    normalized_input = user_input.lower()
    
    # البحث عن مرادف، إذا لم يوجد، استخدم الإدخال الأصلي
    timezone_to_check = TIMEZONE_ALIASES.get(normalized_input, user_input)

    try:
        # التحقق من صحة المنطقة الزمنية
        pytz.timezone(timezone_to_check)
        
        # حفظ المنطقة الزمنية الرسمية في قاعدة البيانات
        await db.set_timezone(timezone_to_check)
        
        await update.message.reply_text(
            f"✅ تم تحديث المنطقة الزمنية بنجاح إلى: `{timezone_to_check}`",
            parse_mode='MarkdownV2'
        )
        # بعد النجاح، نعود إلى القائمة الرئيسية للمدير
        await admin_panel_handler(update, context, from_conversation=True)
        return ConversationHandler.END

    except pytz.UnknownTimeZoneError:
        await update.message.reply_text(
            "عذراً، هذه المنطقة الزمنية غير صالحة. يرجى التأكد من الاسم والمحاولة مرة أخرى.\n"
            "مثال: `Asia/Riyadh` أو `القاهرة`."
        )
        return ENTERING_TIMEZONE

# --- بناء معالج المحادثة ---
change_timezone_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(request_timezone_input, pattern="^change_timezone$")],
    states={
        ENTERING_TIMEZONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_timezone_input)],
    },
    fallbacks=[
        # يمكن إضافة معالج للرجوع أو الإلغاء هنا إذا أردنا
    ],
    per_message=False
)

interface_menu_handler = CallbackQueryHandler(interface_menu, pattern="^customize_interface$")
