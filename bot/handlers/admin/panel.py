# -*- coding: utf-8 -*-

from aiogram import types, Dispatcher
from config import ADMIN_USER_ID

async def show_admin_panel(message: types.Message):
    """
    يعرض لوحة التحكم الرئيسية للمدير مع جميع الأزرار.
    """
    # هذا هو النص الذي سيظهر فوق الأزرار
    panel_text = "أهلاً بك في لوحة التحكم الخاصة بالبوت. اختر أحد الخيارات أدناه:"

    # إنشاء لوحة المفاتيح
    keyboard = types.InlineKeyboardMarkup(row_width=2)

    # إضافة الأزرار بالترتيب المطلوب
    buttons = [
        types.InlineKeyboardButton(text="📝 الردود التلقائية", callback_data="admin:auto_replies"),
        types.InlineKeyboardButton(text="⏰ التذكيرات", callback_data="admin:reminders"),
        types.InlineKeyboardButton(text="📢 منشورات القناة", callback_data="admin:channel_publications"),
        types.InlineKeyboardButton(text="📺 القنوات", callback_data="admin:channels_management"),
        types.InlineKeyboardButton(text="⚙️ إعدادات القنوات", callback_data="admin:channels_settings"),
        types.InlineKeyboardButton(text="🚫 إدارة الحظر", callback_data="admin:ban_management"),
        types.InlineKeyboardButton(text="📣 نشر للجميع", callback_data="admin:broadcast"),
        types.InlineKeyboardButton(text="🎨 تخصيص الواجهة", callback_data="admin:bot_customization"),
        types.InlineKeyboardButton(text="🛡️ الحماية والأمان", callback_data="admin:security"),
        types.InlineKeyboardButton(text="🗑️ إدارة الذاكرة", callback_data="admin:memory_management"),
        types.InlineKeyboardButton(text="📊 الإحصائيات", callback_data="admin:statistics"),
        types.InlineKeyboardButton(text="📚 إدارة المكتبة", callback_data="admin:library_management"),
        types.InlineKeyboardButton(text="🔗 الإشتراك الإجباري", callback_data="admin:force_subscribe"),
        types.InlineKeyboardButton(text="🖥️ مراقبة النظام", callback_data="admin:system_monitoring"),
        types.InlineKeyboardButton(text="✍️ تعديل النصوص", callback_data="admin:texts_editor")
    ]
    
    keyboard.add(*buttons)

    await message.answer(panel_text, reply_markup=keyboard)


def register_admin_panel_handlers(dp: Dispatcher):
    """
    يسجل معالجات لوحة التحكم.
    يتم استخدام الفلتر المخصص is_admin=True لضمان أن المدير فقط يمكنه استدعاء هذا الأمر.
    """
    dp.register_message_handler(show_admin_panel, commands=["admin", "panel"], is_admin=True)
