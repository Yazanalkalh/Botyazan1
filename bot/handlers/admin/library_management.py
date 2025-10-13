# -*- coding: utf-8 -*-

import math
from aiogram import types, Dispatcher, Bot
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.callback_data import CallbackData
from aiogram.utils.exceptions import TelegramAPIError

from bot.database.manager import db

# --- FSM States ---
class AddToLibrary(StatesGroup):
    waiting_for_item = State()

# --- CallbackData ---
lib_pagination_cb = CallbackData("lib_page", "page")
lib_delete_cb = CallbackData("lib_delete", "id")

# --- 1. Main Menu for Library Management ---
async def show_lib_menu(call: types.CallbackQuery, state: FSMContext):
    """Displays the main menu for library management."""
    await state.finish()
    text = await db.get_text("lib_menu_title")
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton(text=await db.get_text("lib_add_button"), callback_data="lib:add"),
        types.InlineKeyboardButton(text=await db.get_text("lib_view_button"), callback_data="lib:view")
    )
    keyboard.add(types.InlineKeyboardButton(text=await db.get_text("ar_back_button"), callback_data="admin:panel:back"))
    await call.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await call.answer()

# --- 2. Add New Item to Library Flow ---
async def add_item_start(call: types.CallbackQuery):
    """Starts the process of adding a new item to the library."""
    text = await db.get_text("lib_ask_for_item")
    keyboard = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton(text=await db.get_text("ar_back_button"), callback_data="admin:library_management"))
    await call.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await AddToLibrary.waiting_for_item.set()
    await call.answer()

async def item_received(message: types.Message, state: FSMContext):
    """Receives and saves the item in the library."""
    await db.add_to_library(message.to_python())
    await state.finish()
    
    text = await db.get_text("lib_item_saved")
    keyboard = types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton(text=await db.get_text("ar_back_button"), callback_data="admin:library_management"))
    await message.answer(text, reply_markup=keyboard)

# --- 3. View Library Items (النسخة المصححة) ---
async def view_library_items(call: types.CallbackQuery, callback_data: dict = None):
    """Displays library items one by one with navigation."""
    page = int(callback_data.get("page", 1)) if callback_data else 1
    
    total_items = await db.get_library_items_count()
    if total_items == 0:
        await call.answer(await db.get_text("lib_no_items"), show_alert=True)
        return

    # --- الإصلاح: جلب كائن البوت من السياق ---
    bot = call.bot
    
    # جلب عنصر واحد في كل مرة (رقم الصفحة هو رقم العنصر)
    items = await db.get_library_items(page=page, limit=1)
    if not items:
        await call.answer("لا يوجد المزيد من العناصر.", show_alert=True)
        return

    item = items[0]
    db_id = str(item['_id'])
    
    # حذف رسالة التحكم القديمة قبل إرسال العنصر الجديد
    try:
        await call.message.delete()
    except Exception:
        pass

    # عرض العنصر المحفوظ
    try:
        message_info = item['message']
        from_chat_id = message_info.get('chat', {}).get('id')
        message_id = message_info.get('message_id')

        if from_chat_id and message_id:
            # --- الإصلاح: استخدام bot.copy_message ---
            await bot.copy_message(
                chat_id=call.from_user.id,
                from_chat_id=from_chat_id,
                message_id=message_id
            )
        else:
            raise ValueError("بيانات الرسالة المحفوظة غير صالحة")

    except Exception as e:
        await call.message.answer(f"⚠️ لا يمكن عرض هذا العنصر. قد يكون محذوفاً أو تالفاً.\nالخطأ: {e}")

    # بناء لوحة التحكم الجديدة وإرسالها
    page_info = (await db.get_text("lib_item_info")).format(current_item=page, total_items=total_items)
    
    keyboard = types.InlineKeyboardMarkup()
    pagination_buttons = []
    if page > 1:
        pagination_buttons.append(types.InlineKeyboardButton(text=await db.get_text("ar_prev_button"), callback_data=lib_pagination_cb.new(page=page - 1)))
    if page < total_items:
        pagination_buttons.append(types.InlineKeyboardButton(text=await db.get_text("ar_next_button"), callback_data=lib_pagination_cb.new(page=page + 1)))
    
    keyboard.row(*pagination_buttons)
    keyboard.add(types.InlineKeyboardButton(text=await db.get_text("ar_delete_button"), callback_data=lib_delete_cb.new(id=db_id)))
    keyboard.add(types.InlineKeyboardButton(text=await db.get_text("ar_back_button"), callback_data="admin:library_management"))
    
    await call.message.answer(f"📖 *محتوى المكتبة* ({page_info})", reply_markup=keyboard, parse_mode="Markdown")
    await call.answer()

async def delete_library_item(call: types.CallbackQuery):
    """Deletes an item from the library and its control panel."""
    db_id = call.data.split(":")[-1]
    await db.delete_library_item(db_id)
    await call.answer(await db.get_text("lib_deleted_success"), show_alert=False)
    # حذف لوحة التحكم الخاصة بالعنصر المحذوف
    try:
        await call.message.delete()
    except Exception:
        pass

# --- Registration Function ---
def register_library_management_handlers(dp: Dispatcher):
    """Registers all handlers for the library management feature."""
    dp.register_callback_query_handler(show_lib_menu, text="admin:library_management", is_admin=True, state="*")
    
    # Add flow
    dp.register_callback_query_handler(add_item_start, text="lib:add", is_admin=True, state="*")
    dp.register_message_handler(item_received, state=AddToLibrary.waiting_for_item, is_admin=True, content_types=types.ContentTypes.ANY)
    
    # View and Delete flow
    dp.register_callback_query_handler(view_library_items, text="lib:view", is_admin=True, state="*")
    dp.register_callback_query_handler(view_library_items, lib_pagination_cb.filter(), is_admin=True, state="*")
    dp.register_callback_query_handler(delete_library_item, lib_delete_cb.filter(), is_admin=True, state="*")
