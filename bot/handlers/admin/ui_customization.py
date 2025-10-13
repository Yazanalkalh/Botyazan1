# -*- coding: utf-8 -*-

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from bot.database.manager import db

# --- FSM States ---
class EditText(StatesGroup):
    waiting_for_new_text = State()

class EditTimezone(StatesGroup):
    waiting_for_identifier = State()
    waiting_for_display_name = State()

# --- 1. Main Menu for UI Customization ---
async def show_ui_menu(call: types.CallbackQuery, state: FSMContext):
    """Displays the main menu for UI customization."""
    await state.finish()
    text = await db.get_text("ui_menu_title")
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        types.InlineKeyboardButton(text=await db.get_text("ui_edit_date_button"), callback_data="ui:edit_text:date_button"),
        types.InlineKeyboardButton(text=await db.get_text("ui_edit_time_button"), callback_data="ui:edit_text:time_button"),
        types.InlineKeyboardButton(text=await db.get_text("ui_edit_reminder_button"), callback_data="ui:edit_text:reminder_button"),
        types.InlineKeyboardButton(text=await db.get_text("ui_edit_timezone_button"), callback_data="ui:edit_timezone"),
        types.InlineKeyboardButton(text=await db.get_text("ar_back_button"), callback_data="admin:panel:back")
    )
    await call.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await call.answer()

# --- 2. Edit Text Flow (for buttons) ---
async def edit_text_start(call: types.CallbackQuery, state: FSMContext):
    """Starts the process of editing a text item (like a button label)."""
    text_id = call.data.split(":")[-1]
    item_name_key = f"ui_edit_{text_id}_button" # e.g., ui_edit_date_button_button
    item_name = await db.get_text(item_name_key)
    
    await state.update_data(text_id_to_edit=text_id, item_name=item_name)
    
    current_text = await db.get_text(text_id)
    prompt_text = (await db.get_text("ui_ask_for_new_text")).format(item_name=item_name)
    prompt_text += f"\n\nالنص الحالي: `{current_text}`"

    keyboard = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton(text=await db.get_text("ar_back_button"), callback_data="admin:ui_customization"))
    await call.message.edit_text(prompt_text, reply_markup=keyboard, parse_mode="Markdown")
    await EditText.waiting_for_new_text.set()
    await call.answer()

async def new_text_received(message: types.Message, state: FSMContext):
    """Receives, saves the new text, and confirms."""
    data = await state.get_data()
    text_id = data['text_id_to_edit']
    item_name = data['item_name']
    
    await db.update_text(text_id, message.text)
    await state.finish()
    
    text = (await db.get_text("ui_text_updated_success")).format(item_name=item_name)
    keyboard = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton(text=await db.get_text("ar_back_button"), callback_data="admin:ui_customization"))
    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")

# --- 3. Edit Timezone Flow ---
async def edit_timezone_start(call: types.CallbackQuery, state: FSMContext):
    """Starts the process of editing the timezone."""
    current_tz = await db.get_timezone()
    prompt_text = await db.get_text("ui_ask_for_tz_identifier")
    prompt_text += f"\n\nالمعرّف الحالي: `{current_tz['identifier']}`"

    keyboard = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton(text=await db.get_text("ar_back_button"), callback_data="admin:ui_customization"))
    await call.message.edit_text(prompt_text, reply_markup=keyboard, parse_mode="Markdown")
    await EditTimezone.waiting_for_identifier.set()
    await call.answer()

async def timezone_identifier_received(message: types.Message, state: FSMContext):
    """Receives the timezone identifier and asks for the display name."""
    await state.update_data(identifier=message.text)
    
    current_tz = await db.get_timezone()
    prompt_text = await db.get_text("ui_ask_for_tz_display_name")
    prompt_text += f"\n\nالاسم الحالي: `{current_tz['display_name']}`"
    
    keyboard = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton(text=await db.get_text("ar_back_button"), callback_data="admin:ui_customization"))
    await message.answer(prompt_text, reply_markup=keyboard, parse_mode="Markdown")
    await EditTimezone.next()

async def timezone_display_name_received(message: types.Message, state: FSMContext):
    """Receives the display name, saves everything, and confirms."""
    data = await state.get_data()
    identifier = data['identifier']
    display_name = message.text
    
    await db.set_timezone(identifier=identifier, display_name=display_name)
    await state.finish()
    
    text = await db.get_text("ui_tz_updated_success")
    keyboard = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton(text=await db.get_text("ar_back_button"), callback_data="admin:ui_customization"))
    await message.answer(text, reply_markup=keyboard)

# --- Registration Function ---
def register_ui_customization_handlers(dp: Dispatcher):
    """Registers all handlers for the UI customization feature."""
    dp.register_callback_query_handler(show_ui_menu, text="admin:ui_customization", is_admin=True, state="*")
    
    # Edit text flow
    dp.register_callback_query_handler(edit_text_start, text_startswith="ui:edit_text:", is_admin=True, state="*")
    dp.register_message_handler(new_text_received, state=EditText.waiting_for_new_text, is_admin=True)

    # Edit timezone flow
    dp.register_callback_query_handler(edit_timezone_start, text="ui:edit_timezone", is_admin=True, state="*")
    dp.register_message_handler(timezone_identifier_received, state=EditTimezone.waiting_for_identifier, is_admin=True)
    dp.register_message_handler(timezone_display_name_received, state=EditTimezone.waiting_for_display_name, is_admin=True)
