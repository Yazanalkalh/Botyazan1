# -*- coding: utf-8 -*-

import io
import math
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.callback_data import CallbackData
from aiogram.utils.markdown import escape_md

from bot.database.manager import db

# --- FSM States for adding and importing reminders ---
class AddReminder(StatesGroup):
    waiting_for_content = State()

class ImportReminders(StatesGroup):
    waiting_for_file = State()

# --- CallbackData for pagination and deletion ---
# نستخدم بادئة فريدة (rem) لتجنب التعارض مع الردود التلقائية (ar)
pagination_cb = CallbackData("rem_page", "page")
delete_cb = CallbackData("rem_delete", "id")

# --- 1. Main Menu for Reminders ---
async def show_reminders_menu(call: types.CallbackQuery, state: FSMContext):
    """يعرض القائمة الرئيسية لإدارة التذكيرات."""
    await state.finish()
    text = await db.get_text("rem_menu_title")
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton(text=await db.get_text("rem_add_button"), callback_data="rem:add"),
        types.InlineKeyboardButton(text=await db.get_text("rem_view_button"), callback_data="rem:view"),
        types.InlineKeyboardButton(text=await db.get_text("rem_import_button"), callback_data="rem:import"),
        types.InlineKeyboardButton(text=await db.get_text("ar_back_button"), callback_data="admin:panel:back") # زر العودة مشترك
    )
    await call.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await call.answer()

# --- 2. View All Reminders (with Pagination) ---
async def view_reminders(call: types.CallbackQuery, callback_data: dict = None):
    """يعرض قائمة التذكيرات مع تقسيم الصفحات."""
    page = int(callback_data.get("page", 1)) if callback_data else 1
    
    ITEMS_PER_PAGE = 10
    total_items = await db.get_reminders_count()
    if total_items == 0:
        await call.answer(await db.get_text("rem_no_reminders"), show_alert=True)
        return

    total_pages = math.ceil(total_items / ITEMS_PER_PAGE)
    page_info = (await db.get_text("ar_page_info")).format(current_page=page, total_pages=total_pages)
    
    reminders = await db.get_reminders(page=page, limit=ITEMS_PER_PAGE)
    
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    
    for reminder in reminders:
        # نعرض أول 30 حرفاً من التذكير كمعاينة
        reminder_preview = escape_md(reminder['text'][:30]) + '...'
        keyboard.add(types.InlineKeyboardButton(
            text=f"{await db.get_text('rem_delete_button')} `{reminder_preview}`",
            callback_data=delete_cb.new(id=str(reminder['_id']))
        ))

    pagination_buttons = []
    if page > 1:
        pagination_buttons.append(types.InlineKeyboardButton(
            text=await db.get_text("ar_prev_button"), callback_data=pagination_cb.new(page=page - 1)))
    if page < total_pages:
        pagination_buttons.append(types.InlineKeyboardButton(
            text=await db.get_text("ar_next_button"), callback_data=pagination_cb.new(page=page + 1)))
    
    keyboard.row(*pagination_buttons)
    keyboard.add(types.InlineKeyboardButton(text=await db.get_text("ar_back_button"), callback_data="admin:reminders"))
    
    await call.message.edit_text(f"📖 *قائمة التذكيرات* ({page_info})", reply_markup=keyboard, parse_mode="Markdown")
    await call.answer()

# --- 3. Add New Reminder Flow ---
async def add_reminder_start(call: types.CallbackQuery):
    """يبدأ عملية إضافة تذكير جديد."""
    text = await db.get_text("rem_ask_for_content")
    keyboard = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton(text=await db.get_text("ar_back_button"), callback_data="admin:reminders"))
    await call.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await AddReminder.waiting_for_content.set()
    await call.answer()

async def add_reminder_content_received(message: types.Message, state: FSMContext):
    """يستقبل نص التذكير، يحفظه، ويعرض رسالة النجاح."""
    await db.add_reminder(text=message.text)
    await state.finish()
    
    text = await db.get_text("rem_added_success")
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton(text=await db.get_text("rem_add_another_button"), callback_data="rem:add"),
        types.InlineKeyboardButton(text=await db.get_text("ar_back_button"), callback_data="admin:reminders")
    )
    await message.answer(text, reply_markup=keyboard)

# --- 4. Delete Reminder ---
async def delete_reminder(call: types.CallbackQuery, callback_data: dict):
    """يحذف تذكيراً ويعرض القائمة المحدثة."""
    reminder_id = callback_data['id']
    await db.delete_reminder(reminder_id)
    await call.answer(await db.get_text("rem_deleted_success"), show_alert=False)
    await view_reminders(call) # تحديث القائمة

# --- 5. Import Reminders from File Flow ---
async def import_reminders_start(call: types.CallbackQuery):
    """يبدأ عملية استيراد التذكيرات من ملف."""
    text = await db.get_text("rem_ask_for_file")
    keyboard = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton(text=await db.get_text("ar_back_button"), callback_data="admin:reminders"))
    await call.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await ImportReminders.waiting_for_file.set()
    await call.answer()

async def import_reminders_file_received(message: types.Message, state: FSMContext):
    """يستقبل الملف، يعالجه، ويحفظ التذكيرات."""
    if not message.document or not message.document.file_name.endswith('.txt'):
        await message.answer("خطأ: يرجى إرسال ملف بصيغة .txt")
        return

    file_io = await message.document.download(destination_file=io.BytesIO())
    file_io.seek(0)
    
    success_count = 0
    failed_count = 0

    for line in file_io.read().decode('utf-8').splitlines():
        reminder_text = line.strip()
        if reminder_text:
            await db.add_reminder(text=reminder_text)
            success_count += 1
        else:
            failed_count += 1
    
    await state.finish()
    text = (await db.get_text("rem_import_success")).format(success_count=success_count, failed_count=failed_count)
    keyboard = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton(text=await db.get_text("ar_back_button"), callback_data="admin:reminders"))
    await message.answer(text, reply_markup=keyboard)

# --- Registration Function ---
def register_reminders_handlers(dp: Dispatcher):
    """يسجل جميع معالجات ميزة التذكيرات."""
    # Main menu navigation
    dp.register_callback_query_handler(show_reminders_menu, text="admin:reminders", is_admin=True, state="*")
    
    # View and Pagination
    dp.register_callback_query_handler(view_reminders, text="rem:view", is_admin=True, state="*")
    dp.register_callback_query_handler(view_reminders, pagination_cb.filter(), is_admin=True, state="*")

    # Add flow
    dp.register_callback_query_handler(add_reminder_start, text="rem:add", is_admin=True, state="*")
    dp.register_message_handler(add_reminder_content_received, state=AddReminder.waiting_for_content, is_admin=True)
    
    # Delete flow
    dp.register_callback_query_handler(delete_reminder, delete_cb.filter(), is_admin=True, state="*")

    # Import flow
    dp.register_callback_query_handler(import_reminders_start, text="rem:import", is_admin=True, state="*")
    dp.register_message_handler(import_reminders_file_received, state=ImportReminders.waiting_for_file, is_admin=True, content_types=types.ContentTypes.DOCUMENT)
