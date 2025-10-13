# -*- coding: utf-8 -*-

import asyncio
from aiogram import types, Dispatcher, Bot
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.exceptions import BotBlocked, ChatNotFound, UserDeactivated, TelegramAPIError

from bot.database.manager import db

# --- FSM States ---
class Broadcast(StatesGroup):
    waiting_for_message = State()
    waiting_for_confirmation = State()

# --- 1. Start Broadcast Flow ---
async def broadcast_start(call: types.CallbackQuery, state: FSMContext):
    """Starts the broadcast process by asking for the message."""
    await state.finish()
    text = await db.get_text("bc_ask_for_message")
    keyboard = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton(text=await db.get_text("ar_back_button"), callback_data="admin:panel:back"))
    await call.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await Broadcast.waiting_for_message.set()
    await call.answer()

async def broadcast_message_received(message: types.Message, state: FSMContext):
    """Receives the message and asks for confirmation."""
    # Save message details to state for later use
    await state.update_data(
        message_to_send={'chat_id': message.chat.id, 'message_id': message.message_id}
    )
    
    users_count = len(await db.get_all_users())
    text = (await db.get_text("bc_confirmation")).format(count=users_count)
    
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton(text=await db.get_text("bc_confirm_button"), callback_data="bc:confirm"),
        types.InlineKeyboardButton(text=await db.get_text("bc_cancel_button"), callback_data="bc:cancel")
    )
    
    await message.answer(text, reply_markup=keyboard)
    await Broadcast.next()

# --- 2. Confirmation and Execution ---
async def broadcast_confirmed(call: types.CallbackQuery, state: FSMContext, bot: Bot):
    """Handles the broadcast after admin confirmation."""
    data = await state.get_data()
    await state.finish()

    message_to_send = data.get('message_to_send')
    if not message_to_send:
        await call.message.edit_text("حدث خطأ، يرجى المحاولة مرة أخرى.")
        return

    users = await db.get_all_users()
    total_users = len(users)
    
    await call.message.edit_text(await db.get_text("bc_started"))
    
    success_count = 0
    failed_count = 0
    
    for i, user_id in enumerate(users):
        try:
            await bot.copy_message(
                chat_id=user_id,
                from_chat_id=message_to_send['chat_id'],
                message_id=message_to_send['message_id']
            )
            success_count += 1
        except (BotBlocked, ChatNotFound, UserDeactivated, TelegramAPIError) as e:
            failed_count += 1
            print(f"Failed to send to {user_id}: {e}")
        
        # To avoid hitting Telegram limits and to provide progress updates
        if (i + 1) % 25 == 0:
            progress_text = (await db.get_text("bc_progress")).format(
                success=success_count,
                failed=failed_count,
                remaining=total_users - (i + 1),
                total=total_users
            )
            try:
                await call.message.edit_text(progress_text)
            except TelegramAPIError: # In case the message is not modified
                pass
        
        await asyncio.sleep(0.1)

    final_text = (await db.get_text("bc_finished")).format(success=success_count, failed=failed_count)
    await call.message.answer(final_text)

async def broadcast_cancelled(call: types.CallbackQuery, state: FSMContext):
    """Cancels the broadcast process."""
    await state.finish()
    await call.message.edit_text("❌ تم إلغاء عملية النشر.")
    await call.answer()

# --- Registration Function ---
def register_broadcast_handlers(dp: Dispatcher):
    """Registers all handlers for the broadcast feature."""
    # The callback from the main panel is now a button, not a command.
    # It should be handled by the panel.py file, which then calls this function.
    # For simplicity, we can also register it directly here.
    
    # We will assume the button in `panel.py` has `callback_data="admin:broadcast"`
    dp.register_callback_query_handler(broadcast_start, text="admin:broadcast", is_admin=True, state="*")
    
    dp.register_message_handler(broadcast_message_received, state=Broadcast.waiting_for_message, is_admin=True, content_types=types.ContentTypes.ANY)
    
    dp.register_callback_query_handler(broadcast_confirmed, text="bc:confirm", is_admin=True, state=Broadcast.waiting_for_confirmation)
    dp.register_callback_query_handler(broadcast_cancelled, text="bc:cancel", is_admin=True, state=Broadcast.waiting_for_confirmation)
