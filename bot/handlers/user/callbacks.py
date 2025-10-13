# -*- coding: utf-8 -*-

from aiogram import types, Dispatcher
from datetime import datetime
import pytz
from hijri_converter import Gregorian
from babel.dates import format_date

from bot.database.manager import db
# نستدعي وظيفة القائمة الرئيسية من ملف البدء لنتمكن من العودة إليها
from bot.handlers.user.start import show_main_menu

# --- قاموس لترجمة أسماء المدن والمناطق الزمنية ---
CITY_TRANSLATIONS = {
    "Riyadh": "الرياض", "Aden": "صنعاء",
    "Cairo": "القاهرة", "Dubai": "دبي", "Kuwait": "الكويت", "Qatar": "قطر",
}

# --- قائمة بأسماء الشهور الهجرية باللغة العربية ---
HIJRI_MONTHS = (
    "محرم", "صفر", "ربيع الأول", "ربيع الثاني", "جمادى الأولى", "جمادى الآخرة",
    "رجب", "شعبان", "رمضان", "شوال", "ذو القعدة", "ذو الحجة"
)

async def show_date(call: types.CallbackQuery):
    """يعدل الرسالة لعرض التاريخ الهجري والميلادي."""
    await call.answer() # لإخفاء علامة التحميل

    today = datetime.now()
    hijri_date = Gregorian(today.year, today.month, today.day).to_hijri()

    day_name = format_date(today, "EEEE", locale="ar")
    hijri_month_name = HIJRI_MONTHS[hijri_date.month - 1]
    hijri_str = f"{hijri_date.day} {hijri_month_name} {hijri_date.year} هجري"
    
    gregorian_month_name = format_date(today, "MMMM", locale="ar")
    gregorian_str = f"{today.day} {gregorian_month_name} {today.year} ميلادي"

    date_text = (
        f"**اليوم :** {day_name}\n"
        f"**التاريخ :** {hijri_str}\n"
        f"**الموافق :** {gregorian_str}"
    )
    
    # بناء زر العودة
    back_button = types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="back_to_main_menu")
    )
    
    await call.message.edit_text(date_text, reply_markup=back_button, parse_mode=types.ParseMode.MARKDOWN)


async def show_time(call: types.CallbackQuery):
    """يعدل الرسالة لعرض الوقت الحالي."""
    await call.answer()
    
    timezone_str = await db.get_timezone()
    try:
        tz = pytz.timezone(timezone_str)
        now = datetime.now(tz)
        
        city_en = timezone_str.split('/')[-1]
        city_ar = CITY_TRANSLATIONS.get(city_en, city_en)

        time_str = now.strftime("%I:%M:%S %p").replace("AM", "صباحاً").replace("PM", "مساءً")
        time_text = f"⏳ **الساعة الآن**\n{time_str} بتوقيت {city_ar}"
        
        back_button = types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="back_to_main_menu")
        )
        await call.message.edit_text(time_text, reply_markup=back_button, parse_mode=types.ParseMode.MARKDOWN)

    except pytz.UnknownTimeZoneError:
        await call.answer("خطأ: المنطقة الزمنية المحددة غير صالحة.", show_alert=True)


async def show_reminder(call: types.CallbackQuery):
    """يعدل الرسالة لعرض ذكر عشوائي."""
    await call.answer()
    reminder_text = await db.get_random_reminder()
    
    full_text = f"📿 **تذكير اليوم:**\n\n{reminder_text}"
    
    back_button = types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="back_to_main_menu")
    )
    await call.message.edit_text(full_text, reply_markup=back_button, parse_mode=types.ParseMode.MARKDOWN)


async def back_to_main_menu_handler(call: types.CallbackQuery):
    """يعالج ضغطة زر "العودة" ويعيد المستخدم إلى القائمة الرئيسية."""
    await call.answer()
    # استدعاء وظيفة عرض القائمة الرئيسية من ملف البدء لتعديل الرسالة
    await show_main_menu(message=call.message, edit_mode=True)


def register_callback_handlers(dp: Dispatcher):
    """وظيفة التسجيل التلقائي لهذه الوحدة."""
    dp.register_callback_query_handler(show_date, text="show_date")
    dp.register_callback_query_handler(show_time, text="show_time")
    dp.register_callback_query_handler(show_reminder, text="show_reminder")
    dp.register_callback_query_handler(back_to_main_menu_handler, text="back_to_main_menu")
