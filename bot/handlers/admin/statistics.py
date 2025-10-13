# -*- coding: utf-8 -*-

from aiogram import types, Dispatcher

from bot.database.manager import db

async def show_statistics(call: types.CallbackQuery):
    """
    يجلب الإحصائيات من قاعدة البيانات ويعرضها للمدير.
    """
    await call.answer() # لإخفاء علامة التحميل بسرعة

    # جلب جميع الإحصائيات في استدعاء واحد فعال
    stats = await db.get_bot_statistics()

    # جلب النصوص اللازمة من قاعدة البيانات
    title = await db.get_text("stats_title")
    total_users_text = await db.get_text("stats_total_users")
    banned_users_text = await db.get_text("stats_banned_users")
    auto_replies_text = await db.get_text("stats_auto_replies")
    reminders_text = await db.get_text("stats_reminders")

    # تنسيق رسالة الإحصائيات
    stats_message = (
        f"{title}\n\n"
        f"{total_users_text}: `{stats['total_users']}`\n"
        f"{banned_users_text}: `{stats['banned_users']}`\n"
        f"{auto_replies_text}: `{stats['auto_replies']}`\n"
        f"{reminders_text}: `{stats['reminders']}`"
    )

    # إنشاء الأزرار (تحديث + عودة)
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton(text=await db.get_text("stats_refresh_button"), callback_data="admin:statistics"),
        types.InlineKeyboardButton(text=await db.get_text("ar_back_button"), callback_data="admin:panel:back")
    )

    try:
        await call.message.edit_text(stats_message, reply_markup=keyboard, parse_mode="Markdown")
    except Exception:
        # في حال لم تتغير الرسالة (عند الضغط على تحديث ولم تتغير الأرقام)
        pass


def register_statistics_handlers(dp: Dispatcher):
    """
    يسجل معالج واجهة الإحصائيات.
    """
    dp.register_callback_query_handler(show_statistics, text="admin:statistics", is_admin=True, state="*")
