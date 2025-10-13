# -*- coding: utf-8 -*-

import math
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.callback_data import CallbackData
from aiogram.utils.exceptions import ChatNotFound, TelegramAPIError

from bot.database.manager import db

# --- FSM States ---
class AddChannel(StatesGroup):
    waiting_for_channel_id = State()

# --- CallbackData ---
cm_pagination_cb = CallbackData("cm_page", "page")
cm_delete_cb = CallbackData("cm_delete", "id")
cm_test_cb = CallbackData("cm_test", "id")

# --- 1. Main Menu for Channels Management ---
async def show_cm_menu(call: types.CallbackQuery, state: FSMContext):
    await state.finish()
    text = await db.get_text("cm_menu_title")
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton(text=await db.get_text("cm_add_button"), callback_data="cm:add"),
        types.InlineKeyboardButton(text=await db.get_text("cm_view_button"), callback_data="cm:view")
    )
    keyboard.add(types.InlineKeyboardButton(text=await db.get_text("ar_back_button"), callback_data="admin:panel:back"))
    await call.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await call.answer()

# --- 2. Add New Channel Flow ---
async def add_channel_start(call: types.CallbackQuery):
    text = await db.get_text("cm_ask_for_channel_id")
    keyboard = types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton(text=await db.get_text("ar_back_button"), callback_data="admin:channels_management"))
    await call.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await AddChannel.waiting_for_channel_id.set()
    await call.answer()

async def add_channel_id_received(message: types.Message, state: FSMContext):
    channel_id_str = message.text.strip()
    bot = message.bot # <--- الإصلاح هنا
    
    try:
        chat = await bot.get_chat(channel_id_str)
        bot_member = await bot.get_chat_member(chat.id, bot.id) # <--- الإصلاح هنا
        
        if not (bot_member.is_chat_admin() and bot_member.can_post_messages):
            await message.answer(await db.get_text("cm_add_fail_not_admin"))
            return
        
        await db.add_publishing_channel(channel_id=chat.id, channel_title=chat.title)
        await state.finish()
        
        text = (await db.get_text("cm_add_success")).format(title=chat.title)
        keyboard = types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton(text=await db.get_text("ar_back_button"), callback_data="admin:channels_management"))
        await message.answer(text, reply_markup=keyboard)

    except (ChatNotFound, TelegramAPIError) as e:
        print(f"Error adding channel: {e}")
        await message.answer(await db.get_text("cm_add_fail_invalid_id"))

# --- 3. View, Delete, and Test Channels ---
async def view_channels(call: types.CallbackQuery, callback_data: dict = None):
    page = int(callback_data.get("page", 1)) if callback_data else 1
    
    CHANNELS_PER_PAGE = 5
    total_channels = await db.get_publishing_channels_count()
    if total_channels == 0:
        await call.answer(await db.get_text("cm_no_channels"), show_alert=True)
        return

    total_pages = math.ceil(total_channels / CHANNELS_PER_PAGE)
    page_info = (await db.get_text("ar_page_info")).format(current_page=page, total_pages=total_pages)
    
    channels = await db.get_publishing_channels(page=page, limit=CHANNELS_PER_PAGE)
    
    keyboard = types.InlineKeyboardMarkup()
    for channel in channels:
        db_id = str(channel['_id'])
        keyboard.add(types.InlineKeyboardButton(text=f"📢 {channel['title']}", callback_data="noop"))
        keyboard.row(
            types.InlineKeyboardButton(text=await db.get_text("cm_test_button"), callback_data=cm_test_cb.new(id=db_id)),
            types.InlineKeyboardButton(text=await db.get_text("ar_delete_button"), callback_data=cm_delete_cb.new(id=db_id))
        )
    
    pagination_buttons = []
    if page > 1: pagination_buttons.append(types.InlineKeyboardButton(text=await db.get_text("ar_prev_button"), callback_data=cm_pagination_cb.new(page=page - 1)))
    if page < total_pages: pagination_buttons.append(types.InlineKeyboardButton(text=await db.get_text("ar_next_button"), callback_data=cm_pagination_cb.new(page=page + 1)))
    
    keyboard.row(*pagination_buttons)
    keyboard.add(types.InlineKeyboardButton(text=await db.get_text("ar_back_button"), callback_data="admin:channels_management"))
    
    await call.message.edit_text(f"📖 *قائمة القنوات* ({page_info})", reply_markup=keyboard, parse_mode="Markdown")
    await call.answer()

async def delete_channel(call: types.CallbackQuery, callback_data: dict):
    await db.delete_publishing_channel(callback_data['id'])
    await call.answer(await db.get_text("cm_deleted_success"), show_alert=False)
    await view_channels(call)

async def test_channel(call: types.CallbackQuery, callback_data: dict):
    db_id = callback_data['id']
    bot = call.bot # <--- الإصلاح هنا
    channels = await db.get_all_publishing_channels()
    target_channel = next((ch for ch in channels if str(ch['_id']) == db_id), None)

    if not target_channel:
        await call.answer("Channel not found.", show_alert=True)
        return

    try:
        await bot.send_message(target_channel['channel_id'], "🔬 رسالة تجريبية من البوت.")
        await call.answer((await db.get_text("cm_test_success")).format(title=target_channel['title']), show_alert=True)
    except Exception as e:
        print(f"Test failed for {target_channel['title']}: {e}")
        await call.answer((await db.get_text("cm_test_fail")).format(title=target_channel['title']), show_alert=True)

# --- Registration Function ---
def register_channels_management_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(show_cm_menu, text="admin:channels_management", is_admin=True, state="*")
    dp.register_callback_query_handler(add_channel_start, text="cm:add", is_admin=True, state="*")
    dp.register_message_handler(add_channel_id_received, state=AddChannel.waiting_for_channel_id, is_admin=True)
    dp.register_callback_query_handler(view_channels, text="cm:view", is_admin=True, state="*")
    dp.register_callback_query_handler(view_channels, cm_pagination_cb.filter(), is_admin=True, state="*")
    dp.register_callback_query_handler(delete_channel, cm_delete_cb.filter(), is_admin=True, state="*")
    dp.register_callback_query_handler(test_channel, cm_test_cb.filter(), is_admin=True, state="*")
