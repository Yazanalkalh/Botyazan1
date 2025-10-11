# -*- coding: utf-8 -*-

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from functools import wraps
from config import ADMIN_USER_ID

# --- شرح ---
# هذا الملف مسؤول عن عرض لوحة التحكم الرئيسية للمدير
# يحتوي على معالج لزر الرجوع (admin_panel_back_handler)
# ويحتوي على ديكوريتور admin_only لضمان أن المدير فقط هو من يستخدم اللوحة

# --- 1. ديكوريتور للتحقق من أن المستخدم هو المدير ---

def admin_only(func):
    """
    ديكوريتور (مزخرف) للتحقق من أن المستخدم الذي يستدعي الوظيفة هو المدير.
    تم تحديثه ليعمل مع الأوامر (Message) وضغطات الأزرار (CallbackQuery).
    """
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = None
        if update.message:
            user_id = update.message.from_user.id
        elif update.callback_query:
            user_id = update.callback_query.from_user.id
        
        if user_id != ADMIN_USER_ID:
            # يمكن إرسال رسالة هنا إذا أردنا، ولكن التجاهل أفضل لعدم تنبيه الآخرين
            print(f"محاولة وصول غير مصرح بها من قبل المستخدم: {user_id}")
            return
        return await func(update, context, *args, **kwargs)
    return wrapped

# --- 2. الوظيفة الرئيسية لعرض لوحة التحكم ---

@admin_only
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """يعرض لوحة التحكم الرئيسية للمدير."""
    keyboard = [
        [
            InlineKeyboardButton("✍️ الردود التلقائية", callback_data='admin_panel_01'),
            InlineKeyboardButton("🗓️ التذكيرات", callback_data='admin_panel_02')
        ],
        [
            InlineKeyboardButton("📢 منشورات القناة", callback_data='admin_panel_03'),
            InlineKeyboardButton("🔗 القنوات", callback_data='admin_panel_04')
        ],
        [
            InlineKeyboardButton("⚙️ إعدادات القنوات", callback_data='admin_panel_05'),
            InlineKeyboardButton("🚫 إدارة الحظر", callback_data='admin_panel_06')
        ],
        [
            InlineKeyboardButton("📣 نشر للجميع", callback_data='admin_panel_07'),
            InlineKeyboardButton("🎨 تخصيص الواجهة", callback_data='admin_panel_08')
        ],
        [
            InlineKeyboardButton("🛡️ الحماية والأمان", callback_data='admin_panel_09'),
            InlineKeyboardButton("🗑️ إدارة الذاكرة", callback_data='admin_panel_10')
        ],
        [
            InlineKeyboardButton("📊 الإحصائيات", callback_data='admin_panel_11'),
            InlineKeyboardButton("📚 إدارة المكتبة", callback_data='admin_panel_12')
        ],
        [
            InlineKeyboardButton("🔒 اشتراك إجباري", callback_data='admin_panel_13'),
            InlineKeyboardButton("🖥️ مراقبة النظام", callback_data='admin_panel_14')
        ],
        [
            InlineKeyboardButton("✏️ تعديل النصوص", callback_data='admin_panel_15')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # التحقق إذا كان التحديث من أمر أو من زر
    if update.callback_query:
        # إذا كان من زر (مثل زر الرجوع)، قم بتعديل الرسالة
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text="-- لوحة التحكم الرئيسية --\n\nاختر أحد الأقسام:",
            reply_markup=reply_markup
        )
    else:
        # إذا كان من أمر /admin، قم بإرسال رسالة جديدة
        await update.message.reply_text(
            text="-- لوحة التحكم الرئيسية --\n\nاختر أحد الأقسام:",
            reply_markup=reply_markup
        )

# --- 3. المعالجات (Handlers) ---

# هذا المعالج يستجيب لأمر /admin
admin_handler = CommandHandler('admin', admin_panel)

# --- هذا هو الجزء الأهم الذي يحل المشكلة ---
# هذا المعالج يستجيب لضغط زر الرجوع الذي لديه callback_data = 'back_to_main_panel'
admin_panel_back_handler = CallbackQueryHandler(admin_panel, pattern='^back_to_main_panel$')
