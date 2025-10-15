# -*- coding: utf-8 -*-

import math
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.callback_data import CallbackData

from bot.database.manager import db

# --- 💡 القاموس الذكي لترجمة الأسماء البرمجية (النسخة الكاملة) 💡 ---
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
    "cp_schedule_button": "زر 'جدولة منشور'",
    "cp_view_scheduled_button": "زر 'عرض المجدولة'",
    "cp_ask_for_auto_msg": "رسالة طلب محتوى النشر التلقائي",
    "cp_auto_msg_set_success": "رسالة نجاح تعيين النشر التلقائي",
    "cp_no_auto_msg": "رسالة 'لا يوجد منشور تلقائي'",
    "cp_auto_msg_deleted_success": "رسالة نجاح حذف المنشور التلقائي",
    "cp_publish_started": "رسالة 'بدء النشر الآن'",
    "cp_publish_finished": "رسالة 'اكتمال النشر الآن'",
    "cp_error_no_auto_msg_to_publish": "خطأ: لا يوجد منشور لنشره",
    "cp_error_no_channels_to_publish": "خطأ: لا توجد قنوات للنشر",

    # --- إدارة القنوات ---
    "cm_menu_title": "عنوان قائمة 'إدارة القنوات'",
    "cm_add_button": "زر 'إضافة قناة'",
    "cm_view_button": "زر 'عرض القنوات'",
    "cm_ask_for_channel_id": "رسالة طلب معرّف القناة",
    "cm_add_success": "رسالة نجاح إضافة القناة",
    "cm_add_fail_not_admin": "خطأ: البوت ليس مشرفاً",
    "cm_add_fail_invalid_id": "خطأ: معرّف القناة غير صالح",
    "cm_add_fail_already_exists": "خطأ: القناة مضافة بالفعل",
    "cm_no_channels": "رسالة 'لا توجد قنوات'",
    "cm_deleted_success": "رسالة نجاح حذف القناة",
    "cm_test_button": "زر 'تجربة الإرسال للقناة'",
    "cm_test_success": "رسالة نجاح تجربة الإرسال",
    "cm_test_fail": "رسالة فشل تجربة الإرسال",

    # --- إدارة الحظر ---
    "bm_menu_title": "عنوان قائمة 'إدارة الحظر'",
    "bm_ban_button": "زر 'حظر مستخدم'",
    "bm_unban_button": "زر 'إلغاء حظر'",
    "bm_view_button": "زر 'عرض المحظورين'",
    "bm_ask_for_user_id": "رسالة طلب ID للحظر",
    "bm_ask_for_unban_user_id": "رسالة طلب ID لإلغاء الحظر",
    "bm_user_banned_success": "رسالة نجاح حظر المستخدم",
    "bm_user_already_banned": "خطأ: المستخدم محظور بالفعل",
    "bm_user_unbanned_success": "رسالة نجاح إلغاء الحظر",
    "bm_user_not_banned": "خطأ: المستخدم ليس محظوراً",
    "bm_invalid_user_id": "خطأ: ID المستخدم غير صالح",
    "bm_no_banned_users": "رسالة 'لا يوجد محظورين'",

    # --- الحماية والأمان ---
    "sec_menu_title": "عنوان قائمة 'الحماية والأمان'",
    "sec_bot_status_button": "زر 'حالة البوت'",
    "sec_media_filtering_button": "زر 'منع الوسائط'",
    "sec_antiflood_button": "زر 'منع التكرار'",
    "sec_rejection_message_button": "زر 'تعديل رسالة الرفض'",
    "sec_bot_active": "نص 'يعمل' (حالة البوت)",
    "sec_bot_inactive": "نص 'متوقف' (حالة البوت)",
    "security_rejection_message": "رسالة رفض الوسائط الممنوعة",

    # --- جدولة المنشورات ---
    "sch_ask_for_message": "رسالة طلب محتوى المنشور المجدول",
    "sch_ask_for_channels": "رسالة طلب اختيار قنوات الجدولة",
    "sch_all_channels_button": "زر 'كل القنوات' (للجدولة)",
    "sch_ask_for_datetime": "رسالة طلب تاريخ ووقت الجدولة",
    "sch_invalid_datetime": "خطأ: صيغة التاريخ غير صالحة",
    "sch_datetime_in_past": "خطأ: لا يمكن الجدولة في الماضي",
    "sch_add_success": "رسالة نجاح إضافة الجدولة",
    "sch_no_jobs": "رسالة 'لا توجد منشورات مجدولة'",
    "sch_deleted_success": "رسالة نجاح حذف الجدولة",

    # --- منع التكرار (بروتوكول سيربيروس) ---
    "af_menu_title": "عنوان قائمة 'منع التكرار'",
    "af_status_button": "زر 'حالة البروتوكول'",
    "af_enabled": "نص 'مفعل' (لمنع التكرار)",
    "af_disabled": "نص 'معطل' (لمنع التكرار)",
    "af_edit_threshold_button": "زر 'تعديل عتبة الإزعاج'",
    "af_edit_mute_duration_button": "زر 'تعديل مدة التقييد'",
    "af_ask_for_new_value": "رسالة طلب إدخال قيمة جديدة",
    "af_updated_success": "رسالة نجاح تحديث الإعداد",
    "af_mute_notification": "رسالة إشعار المستخدم بالتقييد المؤقت",
    "af_ban_notification": "رسالة إشعار المستخدم بالحظر الدائم",

    # --- الإحصائيات ---
    "stats_title": "عنوان قائمة 'الإحصائيات'",
    "stats_total_users": "نص 'إجمالي المستخدمين'",
    "stats_banned_users": "نص 'المستخدمون المحظورون'",
    "stats_auto_replies": "نص 'الردود التلقائية'",
    "stats_reminders": "نص 'التذكيرات'",
    "stats_refresh_button": "زر 'تحديث' (للإحصائيات)",
    
    # --- العناوين المتبقية ---
    "te_menu_title": "عنوان قائمة 'محرر النصوص'",
}


class EditSingleText(StatesGroup):
    waiting_for_new_text = State()

te_pagination_cb = CallbackData("te_page", "page")
te_edit_cb = CallbackData("te_edit", "id")

async def show_texts_menu(call: types.CallbackQuery, state: FSMContext, callback_data: dict = None):
    """يعرض قائمة بالنصوص القابلة للتعديل مع أوصاف عربية."""
    await state.finish()
    page = int(callback_data.get("page", 1)) if callback_data else 1
    
    TEXTS_PER_PAGE = 15 # تم زيادة العدد لعرض المزيد من الخيارات في الصفحة الواحدة
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
        # إذا لم نجد ترجمة، نعرض الاسم البرمجي كما هو
        display_name = TEXT_ID_DESCRIPTIONS.get(text_id, f"{text_id} (لا يوجد وصف)")
        keyboard.add(types.InlineKeyboardButton(
            text=f"✍️ {display_name}",
            callback_data=te_edit_cb.new(id=text_id)
        ))

    pagination_buttons = []
    if page > 1:
        pagination_buttons.append(types.InlineKeyboardButton(text=await db.get_text("ar_prev_button"), callback_data=te_pagination_cb.new(page=page - 1)))
    if page < total_pages:
        pagination_buttons.append(types.InlineKeyboardButton(text=await db.get_text("ar_next_button"), callback_data=te_pagination_cb.new(page=page + 1)))
    
    if pagination_buttons:
        keyboard.row(*pagination_buttons)
        
    keyboard.add(types.InlineKeyboardButton(text=await db.get_text("ar_back_button"), callback_data="admin:panel:back"))
    
    menu_title = await db.get_text('te_menu_title')
    await call.message.edit_text(f"{menu_title}\n\n({page_info})", reply_markup=keyboard, parse_mode="Markdown")
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
