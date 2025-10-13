# -*- coding: utf-8 -*-

import math
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.callback_data import CallbackData

from bot.database.manager import db

# --- FSM States ---
class BanUser(StatesGroup):
    waiting_for_user_id = State()

class UnbanUser(StatesGroup):
    waiting_for_user_id = State()

# --- CallbackData ---
bm_pagination_cb = CallbackData("bm_page", "page")
bm_unban_cb = CallbackData("bm_unban", "id")

# --- 1. Main Menu for Ban Management ---
async def show_bm_menu(call: types.CallbackQuery, state: FSMContext):
    await state.finish()
    text = await db.get_text("bm_menu_title")
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton(text=await db.get_text("bm_ban_button"), callback_data="bm:ban"),
        types.InlineKeyboardButton(text=await db.get_text("bm_unban_button"), callback_data="bm:unban"),
        types.InlineKeyboardButton(text=await db.get_text("bm_view_button"), callback_data="bm:view")
    )
    keyboard.add(types.InlineKeyboardButton(text=await db.get_text("ar_back_button"), callback_data="admin:panel:back"))
    await call.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await call.answer()

# --- 2. Ban User Flow ---
async def ban_user_start(call: types.CallbackQuery):
    text = await db.get_text("bm_ask_for_user_id")
    keyboard = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton(text=await db.get_text("ar_back_button"), callback_data="admin:ban_management"))
    await call.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await BanUser.waiting_for_user_id.set()
    await call.answer()

async def ban_user_id_received(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer(await db.get_text("bm_invalid_user_id"))
        return
    
    user_id = int(message.text)
    
    if await db.ban_user(user_id):
        text = (await db.get_text("bm_user_banned_success")).format(user_id=user_id)
    else:
        text = (await db.get_text("bm_user_already_banned")).format(user_id=user_id)
        
    await state.finish()
    keyboard = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton(text=await db.get_text("ar_back_button"), callback_data="admin:ban_management"))
    await message.answer(text, reply_markup=keyboard)

# --- 3. Unban User Flow ---
async def unban_user_start(call: types.CallbackQuery):
    text = await db.get_text("bm_ask_for_unban_user_id")
    keyboard = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton(text=await db.get_text("ar_back_button"), callback_data="admin:ban_management"))
    await call.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await UnbanUser.waiting_for_user_id.set()
    await call.answer()

async def unban_user_id_received(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer(await db.get_text("bm_invalid_user_id"))
        return
        
    user_id = int(message.text)
    
    if await db.unban_user(user_id):
        text = (await db.get_text("bm_user_unbanned_success")).format(user_id=user_id)
    else:
        text = (await db.get_text("bm_user_not_banned")).format(user_id=user_id)
        
    await state.finish()
    keyboard = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton(text=await db.get_text("ar_back_button"), callback_data="admin:ban_management"))
    await message.answer(text, reply_markup=keyboard)

# --- 4. View Banned Users ---
async def view_banned_users(call: types.CallbackQuery, callback_data: dict = None):
    page = int(callback_data.get("page", 1)) if callback_data else 1
    
    USERS_PER_PAGE = 10
    total_users = await db.get_banned_users_count()
    if total_users == 0:
        await call.answer(await db.get_text("bm_no_banned_users"), show_alert=True)
        return

    total_pages = math.ceil(total_users / USERS_PER_PAGE)
    page_info = (await db.get_text("ar_page_info")).format(current_page=page, total_pages=total_pages)
    
    banned_users = await db.get_banned_users(page=page, limit=USERS_PER_PAGE)
    
    keyboard = types.InlineKeyboardMarkup()
    text = f"📖 *قائمة المستخدمين المحظورين* ({page_info})\n\n"
    for user in banned_users:
        user_id = user['_id']
        text += f"- `@{user_id}`\n"
        keyboard.add(types.InlineKeyboardButton(
            text=f"✅ إلغاء حظر @{user_id}",
            callback_data=bm_unban_cb.new(id=user_id)
        ))

    pagination_buttons = []
    if page > 1: pagination_buttons.append(types.InlineKeyboardButton(text=await db.get_text("ar_prev_button"), callback_data=bm_pagination_cb.new(page=page-1)))
    if page < total_pages: pagination_buttons.append(types.InlineKeyboardButton(text=await db.get_text("ar_next_button"), callback_data=bm_pagination_cb.new(page=page+1)))
    
    keyboard.row(*pagination_buttons)
    keyboard.add(types.InlineKeyboardButton(text=await db.get_text("ar_back_button"), callback_data="admin:ban_management"))
    
    await call.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await call.answer()

async def unban_user_from_list(call: types.CallbackQuery, callback_data: dict):
    user_id = int(callback_data['id'])
    await db.unban_user(user_id)
    await call.answer((await db.get_text("bm_user_unbanned_success")).format(user_id=user_id), show_alert=False)
    await view_banned_users(call)

# --- Registration Function ---
def register_ban_management_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(show_bm_menu, text="admin:ban_management", is_admin=True, state="*")
    
    # Ban flow
    dp.register_callback_query_handler(ban_user_start, text="bm:ban", is_admin=True, state="*")
    dp.register_message_handler(ban_user_id_received, state=BanUser.waiting_for_user_id, is_admin=True)

    # Unban flow
    dp.register_callback_query_handler(unban_user_start, text="bm:unban", is_admin=True, state="*")
    dp.register_message_handler(unban_user_id_received, state=UnbanUser.waiting_for_user_id, is_admin=True)

    # View and unban from list flow
    dp.register_callback_query_handler(view_banned_users, text="bm:view", is_admin=True, state="*")
    dp.register_callback_query_handler(view_banned_users, bm_pagination_cb.filter(), is_admin=True, state="*")
    dp.register_callback_query_handler(unban_user_from_list, bm_unban_cb.filter(), is_admin=True, state="*")
