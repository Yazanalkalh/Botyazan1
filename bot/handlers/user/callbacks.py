# -*- coding: utf-8 -*-

from aiogram import types, Dispatcher
from datetime import datetime
import pytz
from hijri_converter import Gregorian
from babel.dates import format_date

from bot.database.manager import db

# --- قاموس لترجمة أسماء المدن والمناطق الزمنية ---
CITY_TRANSLATIONS = {
    "Riyadh": "الرياض", "Aden": "عدن", "Cairo": "القاهرة",
    "Dubai": "دبي", "Kuwait": "الكويت", "Qatar": "قطر",
}

async def show_date(call: types.CallbackQuery):
    """يعرض التاريخ الهجري والميلادي."""
    await call.answer(cache_time=5) # لمنع ظهور علامة التحميل

    today = datetime.now()
    hijri_date = Gregorian(today.year, today.month, today.day).to_hijri()

    # --- التنسيق باللغة العربية ---
    day_name = format_date(today, "EEEE", locale="ar")
    hijri_month_name = format_date(hijri_date.to_gregorian(), "MMMM", locale="ar_SA")
    gregorian_month_name = format_date(today, "MMMM", locale="ar")

    hijri_str = f"{hijri_date.day} {hijri_month_name} {hijri_date.year} هـ"
    gregorian_str = f"{today.day} {gregorian_month_name} {today.year} م"

    date_text = (
        f"🗓️ **التاريخ اليوم**\n\n"
        f"**اليوم:** {day_name}\n"
        f"**التاريخ الهجري:** {hijri_str}\n"
        f"**الموافق:** {gregorian_str}"
    )
    await call.message.answer(date_text, parse_mode=types.ParseMode.MARKDOWN)


async def show_time(call: types.CallbackQuery):
    """يعرض الوقت الحالي بناءً على المنطقة الزمنية المحددة."""
    await call.answer(cache_time=5)

    timezone_str = await db.get_timezone()
    try:
        # التعامل مع "صنعاء" كحالة خاصة
        display_timezone_str = timezone_str
        if timezone_str == "Asia/Aden":
            display_timezone_str = "Asia/Sanaa" # للاسم فقط

        tz = pytz.timezone(display_timezone_str)
        now = datetime.now(tz)
        
        # ترجمة المدينة
        city_en = display_timezone_str.split('/')[-1]
        city_ar = CITY_TRANSLATIONS.get(city_en, city_en)

        # ترجمة صباحاً/مساءً
        time_str = now.strftime("%I:%M:%S %p").replace("AM", "صباحاً").replace("PM", "مساءً")

        await call.message.answer(f"⏳ الساعة الآن {time_str} بتوقيت {city_ar}")

    except pytz.UnknownTimeZoneError:
        await call.message.answer("خطأ: المنطقة الزمنية المحددة غير صالحة.")


async def show_reminder(call: types.CallbackQuery):
    """يعرض ذكراً عشوائياً."""
    await call.answer()
    reminder_text = await db.get_random_reminder()
    await call.message.answer(f"📿 **تذكير اليوم:**\n\n{reminder_text}", parse_mode=types.ParseMode.MARKDOWN)


async def contact_admin(call: types.CallbackQuery):
    """يطلب من المستخدم إرسال رسالته."""
    await call.answer()
    await call.message.answer("تفضل بإرسال رسالتك الآن، وسيتم توصيلها إلى الإدارة.")


def register_callback_handlers(dp: Dispatcher):
    """تسجيل معالجات الأزرار."""
    dp.register_callback_query_handler(show_date, text="show_date")
    dp.register_callback_query_handler(show_time, text="show_time")
    dp.register_callback_query_handler(show_reminder, text="show_reminder")
    dp.register_callback_query_handler(contact_admin, text="contact_admin")
