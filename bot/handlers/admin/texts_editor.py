# -*- coding: utf-8 -*-

import math
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.callback_data import CallbackData

from bot.database.manager import db

# --- FSM States ---
class EditSingleText(StatesGroup):
    waiting_for_new_text = State()

# --- CallbackData ---
te_pagination_cb = CallbackData("te_page", "page")
te_edit_cb = CallbackData("te_edit", "id")

# --- 1. Main Menu for Text Editor (Paginated) ---
async def show_texts_menu(call: types.CallbackQuery, state: FSMContext, callback_data: dict = None):
    """Displays a paginated list of all editable texts."""
    await state.finish()
    page = int(callback_data.get("page", 1)) if callback_data else 1
    
    TEXTS_PER_PAGE = 10
    all_texts = await db.get_all_editable_texts()
    
    if not all_texts:
        await call.answer("لا توجد نصوص لعرضها.", show_alert=True)
        return

    total_pages = math.ceil(len(all_texts) / TEXTS_PER_PAGE)
    start_index = (page - 1) * TEXTS_PER_PAGE
    end_index = start_index + TEXTS_PER_PAGE
    texts_to_show = all_texts[start_index:end_index]
    
    page_info = (await db.get_text("ar_page_info")).format(current_page=page, total_pages=total_pages)
    
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for text_id in texts_to_show:
        keyboard.add(types.InlineKeyboardButton(
            text=f"✍️ `{text_id}`",
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

# --- 2. Edit Single Text Flow ---
async def edit_text_start(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    """Starts the process of editing a single text item."""
    text_id = callback_data['id']
    await state.update_data(text_id_to_edit=text_id)
    
    current_text = await db.get_text(text_id)
    
    prompt_text = (await db.get_text("te_ask_for_new_text"))
    prompt_text += f"\n\n*النص المستهدف:* `{text_id}`"
    prompt_text += f"\n*النص الحالي:*\n`{current_text}`"

    keyboard = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton(text=await db.get_text("ar_back_button"), callback_data="admin:texts_editor"))
    await call.message.edit_text(prompt_text, reply_markup=keyboard, parse_mode="Markdown")
    await EditSingleText.waiting_for_new_text.set()
    await call.answer()

async def new_text_received(message: types.Message, state: FSMContext):
    """Receives, saves the new text, and confirms."""
    data = await state.get_data()
    text_id = data['text_id_to_edit']
    
    await db.update_text(text_id, message.text)
    await state.finish()
    
    text = await db.get_text("te_updated_success")
    keyboard = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton(text=await db.get_text("ar_back_button"), callback_data="admin:texts_editor"))
    await message.answer(text, reply_markup=keyboard)


# --- Registration Function ---
def register_texts_editor_handlers(dp: Dispatcher):
    """Registers all handlers for the text editor feature."""
    dp.register_callback_query_handler(show_texts_menu, text="admin:texts_editor", is_admin=True, state="*")
    dp.register_callback_query_handler(show_texts_menu, te_pagination_cb.filter(), is_admin=True, state="*")
    
    dp.register_callback_query_handler(edit_text_start, te_edit_cb.filter(), is_admin=True, state="*")
    dp.register_message_handler(new_text_received, state=EditSingleText.waiting_for_new_text, is_admin=True)
