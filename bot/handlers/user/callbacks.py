# -*- coding: utf-8 -*-

from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler
from datetime import datetime
import pytz
from hijri_converter import Gregorian

# استيراد وظائف قاعدة البيانات
from bot.database.manager import get_random_reminder, get_setting

# --- 1. قواميس الترجمة إلى العربية ---

ARABIC_WEEKDAYS = {
    "Saturday": "السبت", "Sunday": "الأحد", "Monday": "الإثنين",
    "Tuesday": "الثلاثاء", "Wednesday": "الأربعاء", "Thursday": "الخميس",
    "Friday": "الجمعة",
}

ARABIC_HIJRI_MONTHS = {
    1: "محرم", 2: "صفر", 3: "ربيع الأول", 4: "ربيع الآخر", 5: "جمادى الأولى",
    6: "جمادى الآخرة", 7: "رجب", 8: "شعبان", 9: "رمضان", 10: "شوال",
    11: "ذو القعدة", 12: "ذو الحجة",
}

# --- 2. وظائف الأزرار ---

async def show_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    today_gregorian = datetime.now()
    hijri_date = Gregorian(today_gregorian.year, today_gregorian.month, today_gregorian.day).to_hijri()
    day_name_english = today_gregorian.strftime("%A")
    day_name_arabic = ARABIC_WEEKDAYS.get(day_name_english, day_name_english)
    hijri_month_name_arabic = ARABIC_HIJRI_MONTHS.get(hijri_date.month, "")

    date_text = (
        f"🗓️\n\n"
        f"اليوم : {day_name_arabic}\n"
        f"التاريخ : {hijri_date.day} {hijri_month_name_arabic} {hijri_date.year} هجري\n"
        f"الموافق : {today_gregorian.day} {today_gregorian.strftime('%B')} {today_gregorian.year} ميلادي"
    )
    
    await query.edit_message_text(text=date_text, reply_markup=query.message.reply_markup)

async def show_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """يعرض الوقت الحالي بناءً على المنطقة الزمنية المحفوظة في قاعدة البيانات."""
    query = update.callback_query
    await query.answer()

    # جلب المنطقة الزمنية من الإعدادات، مع قيمة افتراضية في حال عدم وجودها
    timezone_str = get_setting("timezone", "Asia/Riyadh")
    
    try:
        # تحديد المنطقة الزمنية
        target_tz = pytz.timezone(timezone_str)
        # استخراج اسم المدينة للعرض
        city_name = timezone_str.split('/')[-1]
    except pytz.UnknownTimeZoneError:
        # في حال تم حفظ قيمة خاطئة في قاعدة البيانات، استخدم قيمة افتراضية آمنة
        target_tz = pytz.timezone("Asia/Riyadh")
        city_name = "الرياض"

    time_now = datetime.now(target_tz)
    
    # تنسيق الوقت مع الثواني (H: لساعة 24، I: لساعة 12)
    time_formatted = time_now.strftime("%I:%M:%S %p")
    time_formatted_arabic = time_formatted.replace("AM", "صباحاً").replace("PM", "مساءً")

    time_text = f"⏰\n\nالساعة الآن {time_formatted_arabic} بتوقيت {city_name}"
    
    await query.edit_message_text(text=time_text, reply_markup=query.message.reply_markup)

async def show_daily_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    reminder = get_random_reminder()
    if reminder:
        reminder_text = f"📿\n\n{reminder['text']}"
    else:
        reminder_text = "📿\n\nلم تتم إضافة أي أذكار بعد."
        
    await query.edit_message_text(text=reminder_text, reply_markup=query.message.reply_markup)

# --- 3. تجميع المعالجات (Handlers) ---
date_button_handler = CallbackQueryHandler(show_date, pattern='^show_date$')
time_button_handler = CallbackQueryHandler(show_time, pattern='^show_time$')
daily_reminder_button_handler = CallbackQueryHandler(show_daily_reminder, pattern='^show_daily_reminder$')
