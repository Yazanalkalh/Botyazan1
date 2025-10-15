# -*- coding: utf-8 -*-

import math
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.callback_data import CallbackData

from bot.database.manager import db

# --- 💡 القاموس الذكي لترجمة الأسماء البرمجية 💡 ---
TEXT_ID_DESCRIPTIONS = {
    # --- الواجهة العامة والبدء ---
    "admin_panel_title": "عنوان لوحة التحكم الرئيسية",
    "welcome_message": "رسالة الترحيب (/start)",
    "date_button": "نص زر 'التاريخ' الرئيسي",
    "time_button": "نص زر 'الساعة' الرئيسي",
    "reminder_button": "نص زر 'الأذكار' الرئيسي",
    "ar_back_button": "زر 'عودة' العام",
    "ar_page_info": "نص معلومات الصفحة (مثال: صفحة 1/5)",
    "ar_next_button": "زر 'التالي'",
    "ar_prev_button": "زر 'السابق'",
    "ar_delete_button": "زر 'حذف' العام",
    
    # --- 💡 الإضافة الجديدة: وصف نص رسالة التأكيد 💡 ---
    "user_message_received": "رسالة تأكيد استلام رسالة المستخدم",

    # --- الردود التلقائية ---
    "ar_menu_title": "عنوان قائمة 'الردود التلقائية'",
    "ar_add_button": "زر 'إضافة رد جديد'",
    "ar_view_button": "زر 'عرض كل الردود'",
    "ar_import_button": "زر 'استيراد من ملف' (للردود)",
    "ar_ask_for_keyword": "رسالة طلب الكلمة المفتاحية",
    "ar_ask_for_content": "رسالة طلب محتوى الرد",
    "ar_added_success": "رسالة نجاح إضافة الرد",
    "ar_add_another_button": "زر 'إضافة رد آخر'",
    "ar_ask_for_file": "رسالة طلب ملف الاستيراد (للردود)",
    "ar_import_success": "رسالة نجاح الاستيراد (للردود)",
    "ar_no_replies": "رسالة 'لا توجد ردود'",
    "ar_deleted_success": "رسالة نجاح الحذف (للردود)",
    
    # --- التذكيرات ---
    "rem_menu_title": "عنوان قائمة 'التذكيرات'",
    "rem_add_button": "زر 'إضافة تذكير'",
    "rem_view_button": "زر 'عرض التذكيرات'",
    "rem_import_button": "زر 'استيراد تذكيرات'",
    "rem_ask_for_content": "رسالة طلب نص التذكير",
    "rem_added_success": "رسالة نجاح إضافة التذكير",
    "rem_add_another_button": "زر 'إضافة تذكير آخر'",
    "rem_ask_for_file": "رسالة طلب ملف الاستيراد (للتذكيرات)",
    "rem_import_success": "رسالة نجاح الاستيراد (للتذكيرات)",
    "rem_no_reminders": "رسالة 'لا توجد تذكيرات'",
    "rem_deleted_success": "رسالة نجاح الحذف (للتذكيرات)",
    "rem_delete_button": "زر 'حذف' (للتذكيرات)",

    # --- منشورات القناة ---
    "cp_menu_title": "عنوان قائمة 'منشورات القناة'",
    "cp_set_auto_msg_button": "زر 'تعيين رسالة النشر'",
    "cp_view_auto_msg_button": "زر 'عرض رسالة النشر'",
    "cp_publish_now_button": "زر 'نشر الآن'",

    # --- إدارة القنوات ---
    "cm_menu_title": "عنوان قائمة 'إدارة القنوات'",
    "cm_add_button": "زر 'إضافة قناة'",
    "cm_view_button": "زر 'عرض القنوات'",

    # --- إدارة الحظر ---
    "bm_menu_title": "عنوان قائمة 'إدارة الحظر'",
    "bm_ban_button": "زر 'حظر مستخدم'",
    "bm_unban_button": "زر 'إلغاء حظر'",

    # --- نشر للجميع ---
    "bc_ask_for_message": "رسالة طلب محتوى 'النشر للجميع'",

    # --- تخصيص الواجهة ---
    "ui_menu_title": "عنوان قائمة 'تخصيص الواجهة'",

    # --- الحماية والأمان ---
    "sec_menu_title": "عنوان قائمة 'الحماية والأمان'",
    "security_rejection_message": "رسالة رفض الوسائط الممنوعة",

    # --- بقية الأقسام ---
    "mm_menu_title": "عنوان قائمة 'إدارة الذاكرة'",
    "stats_title": "عنوان قائمة 'الإحصائيات'",
    "lib_menu_title": "عنوان قائمة 'المكتبة'",
    "fs_menu_title": "عنوان قائمة 'الاشتراك الإجباري'",
    "sm_title": "عنوان قائمة 'مراقبة النظام'",
    "te_menu_title": "عنوان قائمة 'محرر النصوص'",
}


# --- (بقية الكود يبقى كما هو دون أي تغيير) ---
class EditSingleText(StatesGroup):
    waiting_for_new_text = State()

te_pagination_cb = CallbackData("te_page", "page")
te_edit_cb = CallbackData("te_edit", "id")

async def show_texts_menu(call: types.CallbackQuery, state: FSMContext, callback_data: dict = None):
    """يعرض قائمة بالنصوص القابلة للتعديل مع أوصاف عربية."""
    await state.finish()
    page = int(callback_data.get("page", 1)) if callback_data else 1
    
    TEXTS_PER_PAGE = 10
    all_texts_ids = await db.get_all_editable_texts()
    
    if not all_texts_ids:
        await call.answer("لا توجد نصوص لعرضها.", show_alert=True)
        return

    total_pages = math.ceil(len(all_texts_ids) / TEXTS_PER_PAGE)
    start_index = (page - 1) * TEXTS_PER_PAGE
    end_index = start_index + TEXTS_PER_PAGE
    texts_to_show = all_texts_ids[start_index:end_index]
    
    page_info = (await db.get_text("ar_page_info")).format(current_page=page, total_pages=total_pages)
    
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for text_id in texts_to_show:
        display_name = TEXT_ID_DESCRIPTIONS.get(text_id, text_id)
        keyboard.add(types.InlineKeyboardButton(
            text=f"✍️ {display_name}",
            callback_data=te_edit_cb.new(id=text_id)
        ))

    pagination_buttons = []
    if page > 1:
        pagination_buttons.append(types.InlineKeyboardButton(text=await db.get_text("ar_prev_button"), callback_data=te_pagination_cb.new(page=page - 1)))
    if page < total_pages:
        pagination_buttons.append(types.InlineKeyboardButton(text=await db.get_text("ar_next_button"), callback_data=te_pagination_cb.new(page=page + 1)))
    
    keyboard.row(*pagination_buttons)
    keyboard.add(types.InlineKeyboardButton(text=await db.get_text("ar_back_button"), callback_data="admin:panel:back"))
    
    await call.message.edit_text(f"{(await db.get_text('te_menu_title'))}\n\n({page_info})", reply_markup=keyboard, parse_mode="Markdown")
    await call.answer()

async def edit_text_start(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    """يبدأ عملية تعديل نص معين."""
    text_id = callback_data['id']
    await state.update_data(text_id_to_edit=text_id)
    
    current_text = await db.get_text(text_id)
    display_name = TEXT_ID_DESCRIPTIONS.get(text_id, text_id)
    
    prompt_text = (await db.get_text("te_ask_for_new_text"))
    prompt_text += f"\n\n*النص المستهدف:* {display_name}"
    prompt_text += f"\n*النص الحالي:*\n`{current_text}`"

    keyboard = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton(text=await db.get_text("ar_back_button"), callback_data="admin:texts_editor"))
    await call.message.edit_text(prompt_text, reply_markup=keyboard, parse_mode="Markdown")
    await EditSingleText.waiting_for_new_text.set()
    await call.answer()

async def new_text_received(message: types.Message, state: FSMContext):
    """يستلم النص الجديد ويحفظه."""
    data = await state.get_data()
    text_id = data['text_id_to_edit']
    
    await db.update_text(text_id, message.text)
    await state.finish()
    
    text = await db.get_text("te_updated_success")
    keyboard = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton(text=await db.get_text("ar_back_button"), callback_data="admin:texts_editor"))
    await message.answer(text, reply_markup=keyboard)


def register_texts_editor_handlers(dp: Dispatcher):
    """يسجل كل معالجات محرر النصوص."""
    dp.register_callback_query_handler(show_texts_menu, text="admin:texts_editor", is_admin=True, state="*")
    dp.register_callback_query_handler(show_texts_menu, te_pagination_cb.filter(), is_admin=True, state="*")
    
    dp.register_callback_query_handler(edit_text_start, te_edit_cb.filter(), is_admin=True, state="*")
    dp.register_message_handler(new_text_received, state=EditSingleText.waiting_for_new_text, is_admin=True)
