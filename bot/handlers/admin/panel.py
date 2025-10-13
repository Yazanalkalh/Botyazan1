# -*- coding: utf-8 -*-

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext

# لقد أضفت هذا السطر لتتوافق الدالة مع التحديثات المستقبلية
# ولتجنب أخطاء "state" المحتملة عند استدعائها من أماكن أخرى
from bot.database.manager import db 

async def show_admin_panel(message: types.Message, state: FSMContext, edit_mode: bool = False):
    """
    يعرض لوحة التحكم الرئيسية للمدير مع جميع الأزرار.
    """
    await state.finish() # لإلغاء أي حالة نشطة عند العودة للقائمة الرئيسية
    
    # لقد قمنا بتغيير هذا ليقرأ النص من قاعدة البيانات، مثل بقية البوت
    panel_text = await db.get_text("admin_panel_title")

    keyboard = types.InlineKeyboardMarkup(row_width=2)
    buttons = [
        types.InlineKeyboardButton(text="📝 الردود التلقائية", callback_data="admin:auto_replies"),
        types.InlineKeyboardButton(text="⏰ التذكيرات", callback_data="admin:reminders"),
        types.InlineKeyboardButton(text="📰 منشورات القناة", callback_data="admin:channel_publications"),
        types.InlineKeyboardButton(text="📡 إدارة القنوات", callback_data="admin:channels_management"),
        # types.InlineKeyboardButton(text="⚙️ إعدادات القنوات", callback_data="admin:channels_settings"), # هذا الزر مدمج مع إدارة القنوات
        types.InlineKeyboardButton(text="🚫 إدارة الحظر", callback_data="admin:ban_management"),
        types.InlineKeyboardButton(text="📣 نشر للجميع", callback_data="admin:broadcast"),
        
        # <--- هذا هو السطر الذي تم إصلاحه ---
        types.InlineKeyboardButton(text="🎨 تخصيص الواجهة", callback_data="admin:ui_customization"),
        
        types.InlineKeyboardButton(text="🛡️ الحماية والأمان", callback_data="admin:security"),
        types.InlineKeyboardButton(text="🗑️ إدارة الذاكرة", callback_data="admin:memory_management"),
        types.InlineKeyboardButton(text="📊 الإحصائيات", callback_data="admin:statistics"),
        types.InlineKeyboardButton(text="📚 إدارة المكتبة", callback_data="admin:library_management"),
        types.InlineKeyboardButton(text="🔗 الإشتراك الإجباري", callback_data="admin:force_subscribe"),
        types.InlineKeyboardButton(text="🖥️ مراقبة النظام", callback_data="admin:system_monitoring"),
        types.InlineKeyboardButton(text="✍️ تعديل النصوص", callback_data="admin:texts_editor")
    ]
    keyboard.add(*[btn for btn in buttons if btn]) # إضافة الأزرار وتجاهل أي قيمة None

    if edit_mode:
        try:
            await message.edit_text(panel_text, reply_markup=keyboard)
        except Exception: pass
    else:
        await message.answer(panel_text, reply_markup=keyboard)

async def back_to_panel_handler(call: types.CallbackQuery, state: FSMContext):
    """يعالج العودة إلى لوحة التحكم الرئيسية من القوائم الفرعية."""
    await show_admin_panel(message=call.message, state=state, edit_mode=True)

def register_admin_panel_handlers(dp: Dispatcher):
    """
    يسجل معالجات لوحة التحكم.
    """
    dp.register_message_handler(show_admin_panel, commands=["admin", "panel"], is_admin=True, state="*")
    # إضافة معالج لزر "العودة"
    dp.register_callback_query_handler(back_to_panel_handler, text="admin:panel:back", is_admin=True, state="*")
