# -*- coding: utf-8 -*-

import asyncio
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.exceptions import TelegramAPIError

from bot.database.manager import db

# --- FSM States ---
class SetAutoMessage(StatesGroup):
    waiting_for_message = State()

# --- 1. Main Menu for Channel Publications ---
async def show_cp_menu(call: types.CallbackQuery, state: FSMContext):
    await state.finish()
    text = await db.get_text("cp_menu_title")
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton(text=await db.get_text("cp_set_auto_msg_button"), callback_data="cp:set_msg"),
        types.InlineKeyboardButton(text=await db.get_text("cp_view_auto_msg_button"), callback_data="cp:view_msg"),
    )
    keyboard.add(
        types.InlineKeyboardButton(text=await db.get_text("cp_publish_now_button"), callback_data="cp:publish_now")
    )
    keyboard.add(
        types.InlineKeyboardButton(text=await db.get_text("ar_back_button"), callback_data="admin:panel:back")
    )
    await call.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await call.answer()

# --- 2. Set Auto Publication Message Flow ---
async def set_auto_msg_start(call: types.CallbackQuery):
    text = await db.get_text("cp_ask_for_auto_msg")
    keyboard = types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton(text=await db.get_text("ar_back_button"), callback_data="admin:channel_publications"))
    await call.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await SetAutoMessage.waiting_for_message.set()
    await call.answer()

async def set_auto_msg_received(message: types.Message, state: FSMContext):
    saved_message_data = {'chat_id': message.chat.id, 'message_id': message.message_id}
    await db.set_auto_publication_message(saved_message_data)
    await state.finish()
    text = await db.get_text("cp_auto_msg_set_success")
    keyboard = types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton(text=await db.get_text("ar_back_button"), callback_data="admin:channel_publications"))
    await message.answer(text, reply_markup=keyboard)

# --- 3. View and Delete Auto Publication Message ---
async def view_auto_msg(call: types.CallbackQuery):
    auto_message_data = await db.get_auto_publication_message()
    bot = call.bot # <--- الإصلاح هنا
    if not auto_message_data:
        await call.answer(await db.get_text("cp_no_auto_msg"), show_alert=True)
        return
    await call.message.answer_chat_action(action="typing")
    await call.message.answer(await db.get_text("cp_view_auto_msg_button") + ":")
    keyboard = types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton(text=await db.get_text("rem_delete_button"), callback_data="cp:delete_msg"))
    try:
        await bot.copy_message(
            chat_id=call.from_user.id,
            from_chat_id=auto_message_data['chat_id'],
            message_id=auto_message_data['message_id'],
            reply_markup=keyboard
        )
    except TelegramAPIError as e:
        await call.message.answer(f"خطأ في عرض الرسالة: {e}\n\nقد تكون الرسالة الأصلية قد حُذفت.")
    await call.answer()

async def delete_auto_msg(call: types.CallbackQuery):
    await db.delete_auto_publication_message()
    await call.answer(await db.get_text("cp_auto_msg_deleted_success"), show_alert=True)
    await call.message.delete()

# --- 4. Publish Now Flow ---
async def publish_now(call: types.CallbackQuery):
    auto_message_data = await db.get_auto_publication_message()
    bot = call.bot # <--- الإصلاح هنا
    if not auto_message_data:
        await call.answer(await db.get_text("cp_error_no_auto_msg_to_publish"), show_alert=True)
        return

    channels = await db.get_all_publishing_channels()
    if not channels:
        await call.answer(await db.get_text("cp_error_no_channels_to_publish"), show_alert=True)
        return
    
    await call.answer()
    status_msg = await call.message.edit_text((await db.get_text("cp_publish_started")).format(count=len(channels)))
    
    success_count = 0
    failed_count = 0
    
    for channel in channels:
        try:
            await bot.copy_message(
                chat_id=channel['channel_id'],
                from_chat_id=auto_message_data['chat_id'],
                message_id=auto_message_data['message_id']
            )
            success_count += 1
        except TelegramAPIError as e:
            failed_count += 1
            print(f"Failed to send to {channel['title']}: {e}")
        await asyncio.sleep(0.5)

    final_text = (await db.get_text("cp_publish_finished")).format(success=success_count, failed=failed_count)
    await status_msg.edit_text(final_text)

# --- Registration Function ---
def register_channel_publications_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(show_cp_menu, text="admin:channel_publications", is_admin=True, state="*")
    dp.register_callback_query_handler(set_auto_msg_start, text="cp:set_msg", is_admin=True, state="*")
    dp.register_message_handler(set_auto_msg_received, state=SetAutoMessage.waiting_for_message, is_admin=True, content_types=types.ContentTypes.ANY)
    dp.register_callback_query_handler(view_auto_msg, text="cp:view_msg", is_admin=True, state="*")
    dp.register_callback_query_handler(delete_auto_msg, text="cp:delete_msg", is_admin=True, state="*")
    dp.register_callback_query_handler(publish_now, text="cp:publish_now", is_admin=True, state="*")
