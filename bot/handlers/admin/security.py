# -*- coding: utf-8 -*-

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from bot.database.manager import db

# --- FSM States ---
class EditRejectionMessage(StatesGroup):
    waiting_for_message = State()

# --- 1. Main Menu for Security (النسخة المصححة) ---
async def show_security_menu(call: types.CallbackQuery, state: FSMContext):
    """Displays the main security menu."""
    await state.finish()
    
    settings = await db.get_security_settings()
    bot_status = settings.get("bot_status", "active")
    
    status_text = await db.get_text("sec_bot_active") if bot_status == "active" else await db.get_text("sec_bot_inactive")
    
    text = await db.get_text("sec_menu_title")
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        types.InlineKeyboardButton(
            text=f'{(await db.get_text("sec_bot_status_button"))}: {status_text}',
            callback_data="sec:toggle_status"
        ),
        types.InlineKeyboardButton(text=await db.get_text("sec_media_filtering_button"), callback_data="sec:media_menu"),
        
        # --- 💡 الإضافة الجديدة: الزر المفقود 💡 ---
        types.InlineKeyboardButton(text=await db.get_text("sec_antiflood_button"), callback_data="sec:antiflood_menu"),
        
        types.InlineKeyboardButton(text=await db.get_text("sec_rejection_message_button"), callback_data="sec:edit_rejection_msg"),
        types.InlineKeyboardButton(text=await db.get_text("ar_back_button"), callback_data="admin:panel:back")
    )
    await call.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await call.answer()

async def toggle_bot_status(call: types.CallbackQuery, state: FSMContext):
    """Toggles the bot's global active/inactive status."""
    await db.toggle_bot_status()
    await show_security_menu(call, state) # Refresh the menu to show the new status

# --- 2. Media Filtering Menu ---
async def show_media_menu(call: types.CallbackQuery):
    """Displays the media filtering sub-menu."""
    settings = await db.get_security_settings()
    blocked_media = settings.get("blocked_media", {})
    
    async def get_button(media_type: str):
        is_blocked = blocked_media.get(media_type, False)
        status_text = await db.get_text("sec_blocked") if is_blocked else await db.get_text("sec_allowed")
        button_text = await db.get_text(f"sec_media_{media_type}")
        return types.InlineKeyboardButton(
            text=f"{button_text}: {status_text}",
            callback_data=f"sec:toggle_media:{media_type}"
        )

    text = await db.get_text("sec_media_menu_title")
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        await get_button("photo"), await get_button("video"),
        await get_button("link"), await get_button("sticker"),
        await get_button("document"), await get_button("audio"),
        await get_button("voice")
    )
    keyboard.add(types.InlineKeyboardButton(text=await db.get_text("ar_back_button"), callback_data="admin:security"))
    
    await call.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await call.answer()
    
async def toggle_media_blocking(call: types.CallbackQuery):
    """Toggles blocking for a specific media type."""
    media_type = call.data.split(":")[-1]
    await db.toggle_media_blocking(media_type)
    await show_media_menu(call) # Refresh the menu

# --- 3. Edit Rejection Message Flow ---
async def edit_rejection_msg_start(call: types.CallbackQuery, state: FSMContext):
    """Starts the process of editing the rejection message."""
    current_msg = await db.get_text("security_rejection_message")
    prompt_text = await db.get_text("sec_rejection_msg_ask")
    prompt_text += f"\n\nالرسالة الحالية: `{current_msg}`"
    
    keyboard = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton(text=await db.get_text("ar_back_button"), callback_data="admin:security"))
    await call.message.edit_text(prompt_text, reply_markup=keyboard, parse_mode="Markdown")
    await EditRejectionMessage.waiting_for_message.set()
    await call.answer()

async def rejection_msg_received(message: types.Message, state: FSMContext):
    """Receives and saves the new rejection message."""
    await db.update_text("security_rejection_message", message.text)
    await state.finish()
    
    text = await db.get_text("sec_rejection_msg_updated")
    keyboard = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton(text=await db.get_text("ar_back_button"), callback_data="admin:security"))
    await message.answer(text, reply_markup=keyboard)

# --- Registration Function ---
def register_security_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(show_security_menu, text="admin:security", is_admin=True, state="*")
    dp.register_callback_query_handler(toggle_bot_status, text="sec:toggle_status", is_admin=True, state="*")
    
    # Media filtering
    dp.register_callback_query_handler(show_media_menu, text="sec:media_menu", is_admin=True, state="*")
    dp.register_callback_query_handler(toggle_media_blocking, text_startswith="sec:toggle_media:", is_admin=True, state="*")
    
    # Rejection message
    dp.register_callback_query_handler(edit_rejection_msg_start, text="sec:edit_rejection_msg", is_admin=True, state="*")
    dp.register_message_handler(rejection_msg_received, state=EditRejectionMessage.waiting_for_message, is_admin=True)
