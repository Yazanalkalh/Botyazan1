# -*- coding: utf-8 -*-

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler
from config import ADMIN_USER_ID

# --- شرح ---
# قمنا بتحديث هذا الملف لجعل لوحة التحكم أجمل وأكثر تنظيماً
# الآن نستخدم أيقونات ونرتب الأزرار في صفوف (كل صف به زرين)

# قائمة جديدة تحتوي على الأيقونة والنص لكل زر
button_data = [
    ("✍️", "الردود التلقائية"), ("🗓️", "التذكيرات"),
    ("📨", "منشورات القناة"), ("📺", "القنوات"),
    ("⚙️", "إعدادات القنوات"), ("🚫", "إدارة الحظر"),
    ("📢", "نشر للجميع"), ("🎨", "تخصيص الواجهة"),
    ("🛡️", "الحماية والأمان"), ("🗑️", "إدارة الذاكرة"),
    ("📊", "الإحصائيات"), ("📚", "إدارة المكتبة"),
    ("🔗", "الاشتراك الإجباري"), ("🖥️", "مراقبة النظام"),
    ("✏️", "تعديل النصوص")
]

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """عرض لوحة التحكم للمدير بتصميم جديد ومنظم."""
    user_id = update.effective_user.id

    if user_id != ADMIN_USER_ID:
        await update.message.reply_text("⚠️ هذا الأمر مخصص للمدير فقط.")
        return

    keyboard = []
    row = []
    
    # المرور على قائمة الأزرار لإنشاء صفوف ديناميكية
    for i, (icon, text) in enumerate(button_data, 1):
        # callback_data يبقى مرقماً ليسهل علينا برمجته لاحقاً
        callback = f'admin_panel_{str(i).zfill(2)}'
        
        # إنشاء الزر الجديد مع الأيقونة
        button = InlineKeyboardButton(f"{icon} {text}", callback_data=callback)
        row.append(button)
        
        # إذا أصبح الصف يحتوي على زرين، قم بإضافته للوحة التحكم وابدأ صفاً جديداً
        if len(row) == 2:
            keyboard.append(row)
            row = []
    
    # إذا كان عدد الأزرار فردياً، الزر الأخير سيبقى في الصف. قم بإضافته.
    if row:
        keyboard.append(row)
        
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text("أهلاً بك في لوحة تحكم المدير:", reply_markup=reply_markup)

admin_handler = CommandHandler('admin', admin_panel)
