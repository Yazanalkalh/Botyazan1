# -*- coding: utf-8 -*-

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from bot.database.manager import db

# --- FSM States ---
class EditAntiFlood(StatesGroup):
    waiting_for_value = State()

# --- 1. Main Menu ---
async def show_antiflood_menu(call: types.CallbackQuery, state: FSMContext):
    """Displays the main menu for the anti-flood system."""
    await state.finish()
    
    settings = await db.get_antiflood_settings()
    is_enabled = settings.get("enabled", True)
    status_text = await db.get_text("af_enabled") if is_enabled else await db.get_text("af_disabled")
    
    text = await db.get_text("af_menu_title")
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        types.InlineKeyboardButton(
            text=f'{(await db.get_text("af_status_button"))}: {status_text}',
            callback_data="af:toggle_status"
        ),
        types.InlineKeyboardButton(text=await db.get_text("af_edit_threshold_button"), callback_data="af:edit:rate_limit"),
        types.InlineKeyboardButton(text=await db.get_text("af_edit_mute_duration_button"), callback_data="af:edit:mute_duration"),
        types.InlineKeyboardButton(text=await db.get_text("ar_back_button"), callback_data="admin:security")
    )
    await call.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await call.answer()

async def toggle_antiflood_status(call: types.CallbackQuery, state: FSMContext):
    """Toggles the anti-flood system on/off."""
    settings = await db.get_antiflood_settings()
    current_status = settings.get("enabled", True)
    await db.update_antiflood_setting("enabled", not current_status)
    await show_antiflood_menu(call, state)

# --- 2. Edit Settings Flow ---
async def edit_setting_start(call: types.CallbackQuery, state: FSMContext):
    """Starts the process of editing an anti-flood setting."""
    setting_key = call.data.split(":")[-1]
    
    settings = await db.get_antiflood_settings()
    current_value = settings.get(setting_key)
    
    await state.update_data(setting_key=setting_key)
    
    prompt_text = await db.get_text("af_ask_for_new_value")
    prompt_text += f"\n\nالقيمة الحالية: `{current_value}`"
    
    keyboard = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton(text=await db.get_text("ar_back_button"), callback_data="sec:antiflood_menu"))
    await call.message.edit_text(prompt_text, reply_markup=keyboard, parse_mode="Markdown")
    await EditAntiFlood.waiting_for_value.set()
    await call.answer()

async def new_value_received(message: types.Message, state: FSMContext):
    """Receives and saves the new setting value."""
    if not message.text.isdigit():
        await message.answer("الرجاء إرسال رقم صحيح فقط.")
        return
        
    data = await state.get_data()
    setting_key = data['setting_key']
    new_value = int(message.text)
    
    await db.update_antiflood_setting(setting_key, new_value)
    await state.finish()
    
    text = await db.get_text("af_updated_success")
    # Redirect back to the anti-flood menu
    temp_call = types.CallbackQuery(id="temp", from_user=message.from_user, chat=message.chat, message=message)
    await show_antiflood_menu(temp_call, state)
    await message.answer(text)


# --- Registration Function ---
def register_antiflood_handlers(dp: Dispatcher):
    # This handler should be called from the main security menu
    dp.register_callback_query_handler(show_antiflood_menu, text="sec:antiflood_menu", is_admin=True, state="*")
    dp.register_callback_query_handler(toggle_antiflood_status, text="af:toggle_status", is_admin=True, state="*")
    
    dp.register_callback_query_handler(edit_setting_start, text_startswith="af:edit:", is_admin=True, state="*")
    dp.register_message_handler(new_value_received, state=EditAntiFlood.waiting_for_value, is_admin=True)
