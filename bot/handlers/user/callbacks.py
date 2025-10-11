# -*- coding: utf-8 -*-

from telegram import Update
from telegram.ext import CallbackQueryHandler, ContextTypes
from hijri_converter import Hijri, Gregorian
import pytz
from datetime import datetime

from bot.database.manager import get_random_reminder, get_setting
from .start import check_subscription

DAYS = {"Saturday": "السبت", "Sunday": "الأحد", "Monday": "الاثنين", "Tuesday": "الثلاثاء", "Wednesday": "الأربعاء", "Thursday": "الخميس", "Friday": "الجمعة"}
MONTHS = {"Muharram": "محرّم", "Safar": "صفر", "Rabi' al-awwal": "ربيع الأول", "Rabi' al-thani": "ربيع الثاني", "Jumada al-ula": "جمادى الأولى", "Jumada al-thani": "جمادى الآخرة", "Rajab": "رجب", "Sha'ban": "شعبان", "Ramadan": "رمضان", "Shawwal": "شوال", "Dhu al-Qi'dah": "ذو القعدة", "Dhu al-Hijjah": "ذو الحجة"}
GREG_MONTHS = {"January": "يناير", "February": "فبراير", "March": "مارس", "April": "أبريل", "May": "مايو", "June": "يونيو", "July": "يوليو", "August": "أغسطس", "September": "سبتمبر", "October": "أكتوبر", "November": "نوفمبر", "December": "ديسمبر"}

async def show_date_func(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_subscription(update, context): return

    today_greg = datetime.now()
    hijri_date = Gregorian(today_greg.year, today_greg.month, today_greg.day).to_hijri()

    day_name = DAYS.get(today_greg.strftime('%A'), "")
    month_name = MONTHS.get(hijri_date.month_name(), "")
    greg_month_name = GREG_MONTHS.get(today_greg.strftime('%B'), "")

    formatted_date = (
        f"اليوم : {day_name}\n"
        f"التاريخ : {hijri_date.day} {month_name} {hijri_date.year} هـ\n"
        f"الموافق : {today_greg.day} {greg_month_name} {today_greg.year} م"
    )
    await update.callback_query.answer(formatted_date, show_alert=True)

async def show_time_func(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_subscription(update, context): return

    timezone_str = get_setting("TIMEZONE", "Asia/Riyadh")
    try:
        user_timezone = pytz.timezone(timezone_str)
    except pytz.UnknownTimeZoneError:
        user_timezone = pytz.timezone("Asia/Riyadh")
        timezone_str = "Asia/Riyadh (افتراضي)"

    now = datetime.now(user_timezone)
    city_name = timezone_str.split('/')[-1].replace('_', ' ')
    
    formatted_time = f"الساعة الآن {now.strftime('%H:%M:%S')} بتوقيت {city_name}"
    await update.callback_query.answer(formatted_time, show_alert=True)

async def show_reminder_func(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_subscription(update, context): return

    reminder = get_random_reminder()
    if reminder and 'text' in reminder:
        await update.callback_query.answer(reminder['text'], show_alert=True)
    else:
        await update.callback_query.answer("لا توجد أذكار مضافة حالياً.", show_alert=True)

show_date = CallbackQueryHandler(show_date_func, pattern='^show_date$')
show_time = CallbackQueryHandler(show_time_func, pattern='^show_time$')
show_reminder = CallbackQueryHandler(show_reminder_func, pattern='^show_reminder$')
