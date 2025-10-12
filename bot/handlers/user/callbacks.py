# -*- coding: utf-8 -*-

from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler
from datetime import datetime
import pytz
from hijri_converter import Gregorian

from bot.database.manager import get_random_reminder, get_timezone
from .start import check_subscription

# --- شرح ---
# هذا الملف مسؤول عن وظائف الأزرار الرئيسية: التاريخ، الساعة، والأذكار.
# كل وظيفة تتحقق من الاشتراك أولاً قبل تنفيذ الأمر.

ARABIC_DAYS = {
    "Saturday": "السبت", "Sunday": "الأحد", "Monday": "الإثنين", 
    "Tuesday": "الثلاثاء", "Wednesday": "الأربعاء", "Thursday": "الخميس", "Friday": "الجمعة"
}
ARABIC_MONTHS_HIJRI = {
    1: "محرم", 2: "صفر", 3: "ربيع الأول", 4: "ربيع الثاني", 5: "جمادى الأولى",
    6: "جمادى الآخرة", 7: "رجب", 8: "شعبان", 9: "رمضان", 10: "شوال",
    11: "ذو القعدة", 12: "ذو الحجة"
}
ARABIC_MONTHS_GREGORIAN = {
    1: "يناير", 2: "فبراير", 3: "مارس", 4: "أبريل", 5: "مايو", 6: "يونيو",
    7: "يوليو", 8: "أغسطس", 9: "سبتمبر", 10: "أكتوبر", 11: "نوفمبر", 12: "ديسمبر"
}

async def show_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """يعرض التاريخ الهجري والميلادي باللغة العربية."""
    query = update.callback_query
    await query.answer()

    if not await check_subscription(update, context):
        return

    now = datetime.now()
    
    # التحويل إلى هجري
    hijri = Gregorian(now.year, now.month, now.day).to_hijri()
    day_name_en = now.strftime('%A')
    day_name_ar = ARABIC_DAYS.get(day_name_en, day_name_en)

    hijri_month_name = ARABIC_MONTHS_HIJRI.get(hijri.month, "")
    gregorian_month_name = ARABIC_MONTHS_GREGORIAN.get(now.month, "")

    date_text = (
        f"اليوم: {day_name_ar}\n"
        f"التاريخ الهجري: {hijri.day} {hijri_month_name} {hijri.year} هـ\n"
        f"التاريخ الميلادي: {now.day} {gregorian_month_name} {now.year} م"
    )
    await query.edit_message_text(text=date_text, reply_markup=query.message.reply_markup)

async def show_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """يعرض الوقت الحالي بناءً على المنطقة الزمنية المحددة من المدير."""
    query = update.callback_query
    await query.answer()

    if not await check_subscription(update, context):
        return

    selected_timezone = await get_timezone()
    try:
        tz = pytz.timezone(selected_timezone)
        now = datetime.now(tz)
        # استخراج اسم المدينة من المنطقة الزمنية
        city_name = selected_timezone.split('/')[-1].replace('_', ' ')
        time_text = f"الساعة الآن: {now.strftime('%I:%M:%S %p')}\nبتوقيت: {city_name}"
    except pytz.UnknownTimeZoneError:
        time_text = "خطأ: المنطقة الزمنية المحددة غير صالحة. يرجى مراجعة مدير البوت."
    
    await query.edit_message_text(text=time_text, reply_markup=query.message.reply_markup)

async def show_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """يعرض ذكراً عشوائياً من قاعدة البيانات."""
    query = update.callback_query
    await query.answer()

    if not await check_subscription(update, context):
        return

    reminder = await get_random_reminder()
    if reminder:
        await query.edit_message_text(text=reminder['text'], reply_markup=query.message.reply_markup)
    else:
        no_reminders_text = await get_text("no_reminders_available", "لا توجد أذكار متاحة حالياً.")
        await query.edit_message_text(text=no_reminders_text, reply_markup=query.message.reply_markup)

show_date_handler = CallbackQueryHandler(show_date, pattern="^show_date$")
show_time_handler = CallbackQueryHandler(show_time, pattern="^show_time$")
show_reminder_handler = CallbackQueryHandler(show_reminder, pattern="^show_reminder$")
