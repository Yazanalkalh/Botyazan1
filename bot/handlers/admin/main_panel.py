# -*- coding: utf-8 -*-

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler

# --- تعريف لوحة التحكم الرئيسية ---
async def admin_panel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """يعرض لوحة تحكم المدير الرئيسية."""
    
    # تحديد مصدر الاستدعاء
    query = update.callback_query
    if query:
        await query.answer()
        user = query.from_user
        message_sender = query.edit_message_text
    else:
        user = update.effective_user
        message_sender = update.effective_message.reply_text

    admin_id = int(context.bot_data.get("ADMIN_USER_ID", 0))
    if user.id != admin_id:
        await message_sender("عذراً، هذه المنطقة مخصصة للمدير فقط.")
        return

    # حفظ معرّف المدير في بيانات المستخدم
    context.user_data['admin_id'] = admin_id

    keyboard = [
        [
            InlineKeyboardButton("✍️ الردود التلقائية", callback_data="auto_replies_menu"),
            InlineKeyboardButton("🗓️ التذكيرات", callback_data="reminders_panel")
        ],
        [
            InlineKeyboardButton("📢 منشورات القناة", callback_data="new_post"), # <-- تم التصحيح هنا
            InlineKeyboardButton("📨 تواصل مع المستخدمين", callback_data="communication_menu")
        ],
        [
            InlineKeyboardButton("📊 الإحصائيات", callback_data="stats_menu"),
            InlineKeyboardButton("🚫 إدارة الحظر", callback_data="ban_management_menu")
        ],
        [
            InlineKeyboardButton("📣 نشر للجميع", callback_data="broadcast_menu"),
            InlineKeyboardButton("🎨 تخصيص الواجهة", callback_data="customize_interface")
        ],
        [
            InlineKeyboardButton("🛡️ الحماية والأمان", callback_data="security_menu"),
            InlineKeyboardButton("🗂️ إدارة القنوات", callback_data="channels_menu")
        ],
        [
            InlineKeyboardButton("强制订阅", callback_data="subscription_menu"), # اشتراك إجباري
            InlineKeyboardButton("✏️ تعديل النصوص", callback_data="edit_texts_menu")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await message_sender(
        text="أهلاً بك في لوحة تحكم المدير. اختر أحد الخيارات:",
        reply_markup=reply_markup
    )

# --- المعالجات ---
admin_command_handler = CommandHandler("admin", admin_panel_handler)
admin_panel_callback_handler = CallbackQueryHandler(admin_panel_handler, pattern="^admin_panel_back$")
