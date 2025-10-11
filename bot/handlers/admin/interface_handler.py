# -*- coding: utf-8 -*-

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    CommandHandler,
)
import pytz

from bot.database.manager import set_setting, get_setting

# --- состояний разговора ---
AWAIT_TIMEZONE = range(1)

# --- 1. الواجهة الرئيسية لقسم التخصيص ---

async def interface_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """يعرض الأزرار الخاصة بقسم تخصيص الواجهة."""
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("🌍 تغيير المنطقة الزمنية", callback_data='change_timezone')],
        # يمكن إضافة أزرار أخرى هنا مستقبلاً (مثل تغيير النصوص)
        [InlineKeyboardButton("🔙 رجوع للوحة التحكم الرئيسية", callback_data='back_to_main_panel')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text="-- قسم تخصيص الواجهة --\n\nاختر الإعداد الذي تريد تعديله:",
        reply_markup=reply_markup
    )

# --- 2. منطق تغيير المنطقة الزمنية ---

async def ask_for_timezone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """يطلب من المدير إرسال المنطقة الزمنية الجديدة."""
    query = update.callback_query
    await query.answer()

    current_timezone = get_setting("timezone", "Asia/Riyadh") # القيمة الافتراضية
    
    message_text = (
        f"المنطقة الزمنية الحالية هي: `{current_timezone}`\n\n"
        "أرسل الآن اسم المنطقة الزمنية الجديد.\n"
        "مثال: `Asia/Aden` أو `Africa/Cairo`\n\n"
        "لإلغاء الأمر، أرسل /cancel"
    )
    await query.edit_message_text(text=message_text, parse_mode='Markdown')
    
    return AWAIT_TIMEZONE

async def save_timezone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """يتحقق من صحة المنطقة الزمنية ويحفظها."""
    new_timezone = update.message.text.strip()

    # التحقق من أن المنطقة الزمنية صالحة
    if new_timezone not in pytz.all_timezones:
        await update.message.reply_text(
            "❌ اسم المنطقة الزمنية غير صالح. يرجى التأكد منه وإعادة المحاولة.\n"
            "مثال صحيح: `Asia/Riyadh`"
        )
        return AWAIT_TIMEZONE # يبقى في نفس حالة الانتظار

    # الحفظ في قاعدة البيانات
    set_setting("timezone", new_timezone)
    await update.message.reply_text(f"✅ تم تحديث المنطقة الزمنية بنجاح إلى: `{new_timezone}`")
    
    # العودة إلى لوحة التخصيص بعد النجاح
    await show_interface_panel_after_action(update, context)
    return ConversationHandler.END

# --- 3. وظائف مساعدة ---

async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """يلغي العملية الحالية ويرجع للوحة التخصيص."""
    await update.message.reply_text("تم إلغاء العملية.")
    await show_interface_panel_after_action(update, context)
    return ConversationHandler.END

async def show_interface_panel_after_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """دالة مساعدة لإظهار لوحة التخصيص بعد انتهاء محادثة."""
    keyboard = [
        [InlineKeyboardButton("🌍 تغيير المنطقة الزمنية", callback_data='change_timezone')],
        [InlineKeyboardButton("🔙 رجوع للوحة التحكم الرئيسية", callback_data='back_to_main_panel')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text="-- قسم تخصيص الواجهة --\n\nاختر الإعداد:", reply_markup=reply_markup)

# --- 4. تجميع المعالجات (Handlers) ---

change_timezone_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(ask_for_timezone, pattern='^change_timezone$')],
    states={ AWAIT_TIMEZONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_timezone)] },
    fallbacks=[CommandHandler('cancel', cancel_conversation)],
)

interface_panel_handler = CallbackQueryHandler(interface_panel, pattern='^admin_panel_08$')
