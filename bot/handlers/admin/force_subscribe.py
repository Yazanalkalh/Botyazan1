# -*- coding: utf-8 -*-

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.callback_data import CallbackData
from aiogram.utils.exceptions import ChatNotFound, TelegramAPIError

from bot.database.manager import db

# --- FSM States ---
class AddFSChannel(StatesGroup):
    waiting_for_channel_id = State()

# --- CallbackData ---
fs_delete_cb = CallbackData("fs_delete", "id")

# --- 1. Main Menu for Force Subscribe ---
async def show_fs_menu(call: types.CallbackQuery, state: FSMContext):
    """Displays the main menu for force subscribe management."""
    await state.finish()
    
    is_enabled = await db.get_force_subscribe_status()
    status_text = await db.get_text("fs_enabled") if is_enabled else await db.get_text("fs_disabled")
    
    text = await db.get_text("fs_menu_title")
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        types.InlineKeyboardButton(
            text=f'{(await db.get_text("fs_status_button"))}: {status_text}',
            callback_data="fs:toggle_status"
        ),
        types.InlineKeyboardButton(text=await db.get_text("fs_add_button"), callback_data="fs:add"),
        types.InlineKeyboardButton(text=await db.get_text("fs_view_button"), callback_data="fs:view"),
        types.InlineKeyboardButton(text=await db.get_text("ar_back_button"), callback_data="admin:panel:back")
    )
    await call.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await call.answer()

async def toggle_fs_status(call: types.CallbackQuery, state: FSMContext):
    """Toggles the force subscribe feature on/off."""
    await db.toggle_force_subscribe_status()
    await show_fs_menu(call, state) # Refresh the menu to show the new status

# --- 2. Add New Channel Flow ---
async def add_channel_start(call: types.CallbackQuery):
    """Starts the process of adding a new channel."""
    text = await db.get_text("fs_ask_for_channel_id")
    keyboard = types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton(text=await db.get_text("ar_back_button"), callback_data="admin:force_subscribe"))
    await call.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await AddFSChannel.waiting_for_channel_id.set()
    await call.answer()

# --- 💡 تم إصلاح هذه الدالة 💡 ---
async def add_channel_id_received(message: types.Message, state: FSMContext):
    """Receives the channel ID, verifies it, and saves it."""
    channel_id_str = message.text.strip()
    # الإصلاح: نحصل على كائن البوت من الرسالة نفسها
    bot = message.bot
    
    try:
        chat = await bot.get_chat(channel_id_str)
        if not chat.username:
            await message.answer("خطأ: لا يمكن إضافة قنوات خاصة، يجب أن يكون للقناة معرّف عام (`@username`).")
            return

        bot_member = await bot.get_chat_member(chat.id, bot.id)
        if not bot_member.is_chat_admin():
            await message.answer(await db.get_text("fs_add_fail_not_admin"))
            return
        
        await db.add_subscription_channel(channel_id=chat.id, channel_title=chat.title, username=chat.username)
        await state.finish()
        
        text = (await db.get_text("fs_add_success")).format(title=chat.title)
        keyboard = types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton(text=await db.get_text("ar_back_button"), callback_data="admin:force_subscribe"))
        await message.answer(text, reply_markup=keyboard)

    except (ChatNotFound, TelegramAPIError):
        await message.answer(await db.get_text("cm_add_fail_invalid_id"))

# --- 3. View and Delete Channels ---
async def view_channels(call: types.CallbackQuery):
    """Displays a list of all force subscribe channels."""
    channels = await db.get_all_subscription_channels_docs()
    if not channels:
        await call.answer(await db.get_text("fs_no_channels"), show_alert=True)
        return

    keyboard = types.InlineKeyboardMarkup(row_width=1)
    text = "📖 *قائمة قنوات الاشتراك الإجباري:*\n\n"
    for channel in channels:
        db_id = str(channel['_id'])
        # التأكد من وجود اسم المستخدم قبل عرضه لتجنب الأخطاء
        username = channel.get('username', 'N/A')
        text += f"- {channel.get('title', 'N/A')} (`@{username}`)\n"
        keyboard.add(types.InlineKeyboardButton(
            text=f"🗑️ حذف `@{username}`",
            callback_data=fs_delete_cb.new(id=db_id)
        ))
    
    keyboard.add(types.InlineKeyboardButton(text=await db.get_text("ar_back_button"), callback_data="admin:force_subscribe"))
    
    await call.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await call.answer()

async def delete_channel(call: types.CallbackQuery, callback_data: dict):
    """Deletes a channel from the list."""
    await db.delete_subscription_channel(callback_data['id'])
    await call.answer(await db.get_text("fs_deleted_success"), show_alert=False)
    await view_channels(call) # Refresh the list

# --- Registration Function ---
def register_force_subscribe_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(show_fs_menu, text="admin:force_subscribe", is_admin=True, state="*")
    dp.register_callback_query_handler(toggle_fs_status, text="fs:toggle_status", is_admin=True, state="*")
    
    # Add flow
    dp.register_callback_query_handler(add_channel_start, text="fs:add", is_admin=True, state="*")
    dp.register_message_handler(add_channel_id_received, state=AddFSChannel.waiting_for_channel_id, is_admin=True)

    # View and Delete flow
    dp.register_callback_query_handler(view_channels, text="fs:view", is_admin=True, state="*")
    dp.register_callback_query_handler(delete_channel, fs_delete_cb.filter(), is_admin=True, state="*")
