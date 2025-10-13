# -*- coding: utf-8 -*-

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from bot.database.manager import db

# --- FSM States ---
class ClearMemory(StatesGroup):
    waiting_for_user_id = State()

# --- 1. Main Menu for Memory Management ---
async def show_mm_menu(call: types.CallbackQuery, state: FSMContext):
    """Displays the main menu for memory management."""
    await state.finish()
    text = await db.get_text("mm_menu_title")
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        types.InlineKeyboardButton(text=await db.get_text("mm_clear_user_state_button"), callback_data="mm:clear_user"),
        types.InlineKeyboardButton(text=await db.get_text("ar_back_button"), callback_data="admin:panel:back")
    )
    await call.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await call.answer()

# --- 2. Clear User State Flow ---
async def clear_memory_start(call: types.CallbackQuery):
    """Starts the process of clearing a user's FSM state."""
    text = await db.get_text("mm_ask_for_user_id")
    keyboard = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton(text=await db.get_text("ar_back_button"), callback_data="admin:memory_management"))
    await call.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await ClearMemory.waiting_for_user_id.set()
    await call.answer()

async def clear_memory_user_id_received(message: types.Message, state: FSMContext):
    """Receives the user ID and clears their state and data from storage."""
    if not message.text.isdigit():
        await message.answer(await db.get_text("bm_invalid_user_id"))
        return
    
    user_id = int(message.text)
    
    # FSMContext لديه وصول مباشر إلى وحدة التخزين (storage)
    # يمكننا استخدامه لحذف حالة وبيانات أي مستخدم
    
    # أولاً، نتحقق مما إذا كان للمستخدم حالة أصلاً
    user_state = await state.storage.get_state(chat=user_id, user=user_id)
    
    if user_state is not None:
        # with_data=True يضمن حذف كل من الحالة والبيانات المخزنة
        await state.storage.reset_state(chat=user_id, user=user_id, with_data=True)
        response_text = (await db.get_text("mm_state_cleared_success")).format(user_id=user_id)
    else:
        response_text = (await db.get_text("mm_state_not_found")).format(user_id=user_id)
        
    await state.finish()
    keyboard = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton(text=await db.get_text("ar_back_button"), callback_data="admin:memory_management"))
    await message.answer(response_text, reply_markup=keyboard)


# --- Registration Function ---
def register_memory_management_handlers(dp: Dispatcher):
    """Registers all handlers for the memory management feature."""
    dp.register_callback_query_handler(show_mm_menu, text="admin:memory_management", is_admin=True, state="*")
    
    dp.register_callback_query_handler(clear_memory_start, text="mm:clear_user", is_admin=True, state="*")
    dp.register_message_handler(clear_memory_user_id_received, state=ClearMemory.waiting_for_user_id, is_admin=True)
