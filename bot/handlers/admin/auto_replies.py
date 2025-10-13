# -*- coding: utf-8 -*-

import io
import math
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.callback_data import CallbackData
from aiogram.utils.markdown import escape_md

from bot.database.manager import db

# --- FSM States for adding and importing replies ---
class AddReply(StatesGroup):
    waiting_for_keyword = State()
    waiting_for_content = State()

class ImportReplies(StatesGroup):
    waiting_for_file = State()

# --- CallbackData for pagination and deletion ---
pagination_cb = CallbackData("ar_page", "page")
delete_cb = CallbackData("ar_delete", "id")

# --- 1. Main Menu for Auto Replies ---
async def show_auto_replies_menu(call: types.CallbackQuery, state: FSMContext):
    """Displays the main menu for managing auto-replies."""
    await state.finish()
    text = await db.get_text("ar_menu_title")
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton(text=await db.get_text("ar_add_button"), callback_data="ar:add"),
        types.InlineKeyboardButton(text=await db.get_text("ar_view_button"), callback_data="ar:view"),
        types.InlineKeyboardButton(text=await db.get_text("ar_import_button"), callback_data="ar:import"),
        types.InlineKeyboardButton(text=await db.get_text("ar_back_button"), callback_data="admin:panel:back")
    )
    await call.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await call.answer()

# --- 2. View All Replies (with Pagination) ---
async def view_replies(call: types.CallbackQuery, callback_data: dict = None):
    """Displays a paginated list of all auto-replies."""
    page = int(callback_data.get("page", 1)) if callback_data else 1
    
    REPLIES_PER_PAGE = 10
    total_replies = await db.get_auto_replies_count()
    if total_replies == 0:
        await call.answer(await db.get_text("ar_no_replies"), show_alert=True)
        return

    total_pages = math.ceil(total_replies / REPLIES_PER_PAGE)
    page_info = (await db.get_text("ar_page_info")).format(current_page=page, total_pages=total_pages)
    
    replies = await db.get_auto_replies(page=page, limit=REPLIES_PER_PAGE)
    
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    
    for reply in replies:
        safe_keyword = escape_md(reply['keyword'])
        keyboard.add(types.InlineKeyboardButton(
            text=f"{await db.get_text('ar_delete_button')} `{safe_keyword}`",
            callback_data=delete_cb.new(id=str(reply['_id']))
        ))

    pagination_buttons = []
    if page > 1:
        pagination_buttons.append(types.InlineKeyboardButton(
            text=await db.get_text("ar_prev_button"),
            callback_data=pagination_cb.new(page=page - 1)
        ))
    if page < total_pages:
        pagination_buttons.append(types.InlineKeyboardButton(
            text=await db.get_text("ar_next_button"),
            callback_data=pagination_cb.new(page=page + 1)
        ))
    
    keyboard.row(*pagination_buttons)
    keyboard.add(types.InlineKeyboardButton(text=await db.get_text("ar_back_button"), callback_data="admin:auto_replies"))
    
    await call.message.edit_text(f"📖 *قائمة الردود التلقائية* ({page_info})", reply_markup=keyboard, parse_mode="Markdown")
    await call.answer()

# --- 3. Add New Reply Flow ---
async def add_reply_start(call: types.CallbackQuery):
    """Starts the process of adding a new auto-reply."""
    text = await db.get_text("ar_ask_for_keyword")
    keyboard = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton(text=await db.get_text("ar_back_button"), callback_data="admin:auto_replies"))
    await call.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await AddReply.waiting_for_keyword.set()
    await call.answer()

async def add_reply_keyword_received(message: types.Message, state: FSMContext):
    """Receives the keyword and asks for the content."""
    await state.update_data(keyword=message.text)
    text = await db.get_text("ar_ask_for_content")
    keyboard = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton(text=await db.get_text("ar_back_button"), callback_data="admin:auto_replies"))
    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
    await AddReply.next()

async def add_reply_content_received(message: types.Message, state: FSMContext):
    """Receives the content, saves the reply, and shows success message."""
    user_data = await state.get_data()
    keyword = user_data['keyword']
    message_data = message.to_python()
    
    await db.add_auto_reply(keyword=keyword, message=message_data)
    await state.finish()
    
    text = await db.get_text("ar_added_success")
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton(text=await db.get_text("ar_add_another_button"), callback_data="ar:add"),
        types.InlineKeyboardButton(text=await db.get_text("ar_back_button"), callback_data="admin:auto_replies")
    )
    await message.answer(text, reply_markup=keyboard)

# --- 4. Delete Reply ---
async def delete_reply(call: types.CallbackQuery, callback_data: dict):
    """Deletes an auto-reply and refreshes the list."""
    reply_id = callback_data['id']
    await db.delete_auto_reply(reply_id)
    await call.answer(await db.get_text("ar_deleted_success"), show_alert=False)
    # Refresh list from page 1 to avoid pagination errors
    await view_replies(call)

# --- 5. Import Replies from File Flow ---
async def import_replies_start(call: types.CallbackQuery):
    """Starts the process of importing replies from a .txt file."""
    text = await db.get_text("ar_ask_for_file")
    keyboard = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton(text=await db.get_text("ar_back_button"), callback_data="admin:auto_replies"))
    await call.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await ImportReplies.waiting_for_file.set()
    await call.answer()

async def import_replies_file_received(message: types.Message, state: FSMContext):
    """Receives the file, processes it, and saves the replies."""
    if not message.document or not message.document.file_name.endswith('.txt'):
        await message.answer("خطأ: الملف غير صالح. يرجى إرسال ملف بصيغة .txt")
        return

    file_io = await message.document.download(destination_file=io.BytesIO())
    file_io.seek(0)
    
    success_count = 0
    failed_count = 0

    for line in file_io.read().decode('utf-8').splitlines():
        if '===' in line:
            parts = line.split('===', 1)
            keyword = parts[0].strip()
            content = parts[1].strip()
            if keyword and content:
                # --- هذا هو التعديل الصحيح والاحترافي ---
                message_data = types.Message(text=content).to_python()
                await db.add_auto_reply(keyword=keyword, message=message_data)
                success_count += 1
            else:
                failed_count += 1
        else:
            failed_count += 1
    
    await state.finish()
    text = (await db.get_text("ar_import_success")).format(success_count=success_count, failed_count=failed_count)
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text=await db.get_text("ar_back_button"), callback_data="admin:auto_replies"))
    await message.answer(text, reply_markup=keyboard)

# --- Registration Function ---
def register_auto_replies_handlers(dp: Dispatcher):
    """Registers all handlers for the auto-replies feature."""
    # Main menu navigation
    dp.register_callback_query_handler(show_auto_replies_menu, text="admin:auto_replies", is_admin=True, state="*")
    
    # View and Pagination
    dp.register_callback_query_handler(view_replies, text="ar:view", is_admin=True, state="*")
    dp.register_callback_query_handler(view_replies, pagination_cb.filter(), is_admin=True, state="*")

    # Add flow
    dp.register_callback_query_handler(add_reply_start, text="ar:add", is_admin=True, state="*")
    dp.register_message_handler(add_reply_keyword_received, state=AddReply.waiting_for_keyword, is_admin=True)
    dp.register_message_handler(add_reply_content_received, state=AddReply.waiting_for_content, is_admin=True, content_types=types.ContentTypes.ANY)
    
    # Delete flow
    dp.register_callback_query_handler(delete_reply, delete_cb.filter(), is_admin=True, state="*")

    # Import flow
    dp.register_callback_query_handler(import_replies_start, text="ar:import", is_admin=True, state="*")
    dp.register_message_handler(import_replies_file_received, state=ImportReplies.waiting_for_file, is_admin=True, content_types=types.ContentTypes.DOCUMENT)
