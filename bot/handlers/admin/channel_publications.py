# -*- coding: utf-8 -*-

import asyncio
import datetime
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.exceptions import TelegramAPIError
from aiogram.utils.callback_data import CallbackData
import math

from bot.database.manager import db
from bot.core.scheduler import scheduler, send_scheduled_post

# --- FSM States ---
class SetAutoMessage(StatesGroup):
    waiting_for_message = State()

class SchedulePost(StatesGroup):
    waiting_for_message = State()
    waiting_for_channels = State()
    waiting_for_datetime = State()

# --- CallbackData ---
sch_pagination_cb = CallbackData("sch_page", "page")
sch_delete_cb = CallbackData("sch_delete", "id")

# --- 1. Main Menu for Channel Publications ---
async def show_cp_menu(call: types.CallbackQuery, state: FSMContext):
    await state.finish()
    text = await db.get_text("cp_menu_title")
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton(text=await db.get_text("cp_set_auto_msg_button"), callback_data="cp:set_msg"),
        types.InlineKeyboardButton(text=await db.get_text("cp_view_auto_msg_button"), callback_data="cp:view_msg"),
        types.InlineKeyboardButton(text=await db.get_text("cp_publish_now_button"), callback_data="cp:publish_now"),
        types.InlineKeyboardButton(text=await db.get_text("cp_schedule_button"), callback_data="cp:schedule"),
        types.InlineKeyboardButton(text=await db.get_text("cp_view_scheduled_button"), callback_data="cp:view_scheduled")
    )
    keyboard.add(types.InlineKeyboardButton(text=await db.get_text("ar_back_button"), callback_data="admin:panel:back"))
    await call.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await call.answer()

# --- (الوظائف القديمة للنشر الفوري تبقى كما هي) ---
async def set_auto_msg_start(call: types.CallbackQuery):
    text = await db.get_text("cp_ask_for_auto_msg")
    keyboard = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton(text=await db.get_text("ar_back_button"), callback_data="admin:channel_publications"))
    await call.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await SetAutoMessage.waiting_for_message.set()
    await call.answer()

async def set_auto_msg_received(message: types.Message, state: FSMContext):
    saved_message_data = {'chat_id': message.chat.id, 'message_id': message.message_id}
    await db.set_auto_publication_message(saved_message_data)
    await state.finish()
    text = await db.get_text("cp_auto_msg_set_success")
    keyboard = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton(text=await db.get_text("ar_back_button"), callback_data="admin:channel_publications"))
    await message.answer(text, reply_markup=keyboard)

async def view_auto_msg(call: types.CallbackQuery):
    auto_message_data = await db.get_auto_publication_message()
    if not auto_message_data:
        await call.answer(await db.get_text("cp_no_auto_msg"), show_alert=True)
        return
    await call.message.answer(await db.get_text("cp_view_auto_msg_button") + ":")
    keyboard = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton(text=await db.get_text("rem_delete_button"), callback_data="cp:delete_msg"))
    try:
        await call.bot.copy_message(chat_id=call.from_user.id, from_chat_id=auto_message_data['chat_id'], message_id=auto_message_data['message_id'], reply_markup=keyboard)
    except TelegramAPIError as e:
        await call.message.answer(f"خطأ في عرض الرسالة: {e}")
    await call.answer()

async def delete_auto_msg(call: types.CallbackQuery):
    await db.delete_auto_publication_message()
    await call.answer(await db.get_text("cp_auto_msg_deleted_success"), show_alert=True)
    await call.message.delete()

async def publish_now(call: types.CallbackQuery):
    auto_message_data = await db.get_auto_publication_message()
    if not auto_message_data:
        await call.answer(await db.get_text("cp_error_no_auto_msg_to_publish"), show_alert=True)
        return
    channels = await db.get_all_publishing_channels()
    if not channels:
        await call.answer(await db.get_text("cp_error_no_channels_to_publish"), show_alert=True)
        return
    status_msg = await call.message.edit_text((await db.get_text("cp_publish_started")).format(count=len(channels)))
    success_count, failed_count = 0, 0
    for channel in channels:
        try:
            await call.bot.copy_message(chat_id=channel['channel_id'], from_chat_id=auto_message_data['chat_id'], message_id=auto_message_data['message_id'])
            success_count += 1
        except TelegramAPIError as e:
            failed_count += 1
        await asyncio.sleep(0.5)
    final_text = (await db.get_text("cp_publish_finished")).format(success=success_count, failed=failed_count)
    await status_msg.edit_text(final_text)

# --- وظائف الجدولة ---
async def schedule_post_start(call: types.CallbackQuery, state: FSMContext):
    await state.finish()
    text = await db.get_text("sch_ask_for_message")
    await call.message.edit_text(text, parse_mode="Markdown")
    await SchedulePost.waiting_for_message.set()

async def schedule_message_received(message: types.Message, state: FSMContext):
    await state.update_data(message_data={'chat_id': message.chat.id, 'message_id': message.message_id})
    channels = await db.get_all_publishing_channels()
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text=await db.get_text("sch_all_channels_button"), callback_data="sch_chan:all"))
    for channel in channels:
        keyboard.add(types.InlineKeyboardButton(text=channel['title'], callback_data=f"sch_chan:{channel['channel_id']}"))
    await message.answer(await db.get_text("sch_ask_for_channels"), reply_markup=keyboard)
    await SchedulePost.next()

async def schedule_channels_received(call: types.CallbackQuery, state: FSMContext):
    target = call.data.split(":")[-1]
    target_channels = [] if target == "all" else [int(target)]
    await state.update_data(target_channels=target_channels)
    await call.message.edit_text(await db.get_text("sch_ask_for_datetime"), parse_mode="Markdown")
    await SchedulePost.next()

async def schedule_datetime_received(message: types.Message, state: FSMContext):
    bot = message.bot
    try:
        run_date = datetime.datetime.strptime(message.text, "%Y-%m-%d %H:%M")
        if run_date < datetime.datetime.now():
            await message.answer(await db.get_text("sch_datetime_in_past"))
            return
    except ValueError:
        await message.answer(await db.get_text("sch_invalid_datetime"))
        return
        
    data = await state.get_data()
    job_id = f"post_{int(datetime.datetime.now().timestamp())}"
    
    await db.add_scheduled_post(
        job_id=job_id,
        message_data=data['message_data'],
        target_channels=data['target_channels'],
        run_date=run_date
    )
    
    scheduler.add_job(
        send_scheduled_post,
        "date",
        run_date=run_date,
        id=job_id,
        args=[bot, job_id, data['message_data'], data['target_channels']],
        replace_existing=True
    )
    
    await state.finish()
    await message.answer((await db.get_text("sch_add_success")).format(run_date=run_date.strftime("%Y-%m-%d %H:%M")))

async def view_scheduled_posts(call: types.CallbackQuery, callback_data: dict = None):
    page = int(callback_data.get("page", 1)) if callback_data else 1
    POSTS_PER_PAGE = 5
    total_posts = await db.get_scheduled_posts_count()
    if total_posts == 0:
        await call.answer(await db.get_text("sch_no_jobs"), show_alert=True)
        return
    total_pages = math.ceil(total_posts / POSTS_PER_PAGE)
    posts = await db.get_scheduled_posts(page=page, limit=POSTS_PER_PAGE)
    keyboard = types.InlineKeyboardMarkup()
    text = f"🗓️ *المنشورات المجدولة* (صفحة {page}/{total_pages}):\n\n"
    for post in posts:
        run_date_str = post['run_date'].strftime("%Y-%m-%d %H:%M")
        text += f"- سيتم النشر في: `{run_date_str}`\n"
        keyboard.add(types.InlineKeyboardButton(text=f"🗑️ حذف موعد: {run_date_str}", callback_data=sch_delete_cb.new(id=post['_id'])))
    pagination_buttons = []
    if page > 1: pagination_buttons.append(types.InlineKeyboardButton(text=await db.get_text("ar_prev_button"), callback_data=sch_pagination_cb.new(page=page - 1)))
    if page < total_pages: pagination_buttons.append(types.InlineKeyboardButton(text=await db.get_text("ar_next_button"), callback_data=sch_pagination_cb.new(page=page + 1)))
    keyboard.row(*pagination_buttons)
    keyboard.add(types.InlineKeyboardButton(text=await db.get_text("ar_back_button"), callback_data="admin:channel_publications"))
    await call.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

# --- 💡 تم إصلاح هذه الدالة 💡 ---
async def delete_scheduled_post(call: types.CallbackQuery, callback_data: dict):
    """
    يحذف منشوراً مجدولاً بأمان.
    """
    job_id = callback_data['id']
    await db.delete_scheduled_post(job_id)
    
    # الإصلاح: التحقق من وجود المهمة قبل محاولة حذفها
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
        
    await call.answer(await db.get_text("sch_deleted_success"), show_alert=False)
    await view_scheduled_posts(call)

# --- Registration Function ---
def register_channel_publications_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(show_cp_menu, text="admin:channel_publications", is_admin=True, state="*")
    dp.register_callback_query_handler(set_auto_msg_start, text="cp:set_msg", is_admin=True, state="*")
    dp.register_message_handler(set_auto_msg_received, state=SetAutoMessage.waiting_for_message, is_admin=True, content_types=types.ContentTypes.ANY)
    dp.register_callback_query_handler(view_auto_msg, text="cp:view_msg", is_admin=True, state="*")
    dp.register_callback_query_handler(delete_auto_msg, text="cp:delete_msg", is_admin=True, state="*")
    dp.register_callback_query_handler(publish_now, text="cp:publish_now", is_admin=True, state="*")
    dp.register_callback_query_handler(schedule_post_start, text="cp:schedule", is_admin=True, state="*")
    dp.register_message_handler(schedule_message_received, state=SchedulePost.waiting_for_message, is_admin=True, content_types=types.ContentTypes.ANY)
    dp.register_callback_query_handler(schedule_channels_received, text_startswith="sch_chan:", is_admin=True, state=SchedulePost.waiting_for_channels)
    dp.register_message_handler(schedule_datetime_received, state=SchedulePost.waiting_for_datetime, is_admin=True)
    dp.register_callback_query_handler(view_scheduled_posts, text="cp:view_scheduled", is_admin=True, state="*")
    dp.register_callback_query_handler(view_scheduled_posts, sch_pagination_cb.filter(), is_admin=True, state="*")
    dp.register_callback_query_handler(delete_scheduled_post, sch_delete_cb.filter(), is_admin=True, state="*")
