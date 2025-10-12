# -*- coding: utf-8 -*-

import pytz
from datetime import datetime
from hijri_converter import Hijri, Gregorian
from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler
from bot.database.manager import db
from bot.handlers.user.start import is_user_subscribed # استيراد حارس الأمن

# --- قاموس الترجمة ---
CITY_NAMES_AR = {
    "Riyadh": "الرياض", "Aden": "عدن", "Cairo": "القاهرة", "Dubai": "دبي",
    "Kuwait": "الكويت", "Qatar": "قطر", "Sanaa": "صنعاء"
}
DAYS_AR = ["الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]
MONTHS_HIJRI_AR = [
    "محرم", "صفر", "ربيع الأول", "ربيع الثاني", "جمادى الأولى", "جمادى الآخرة",
    "رجب", "شعبان", "رمضان", "شوال", "ذو القعدة", "ذو الحجة"
]
MONTHS_GREGORIAN_AR = [
    "يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو",
    "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"
]

async def show_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    today_gregorian = datetime.now()
    hijri_date = Gregorian(today_gregorian.year, today_gregorian.month, today_gregorian.day).to_hijri()

    day_name = DAYS_AR[today_gregorian.weekday()]
    hijri_month_name = MONTHS_HIJRI_AR[hijri_date.month - 1]
    gregorian_month_name = MONTHS_GREGORIAN_AR[today_gregorian.month - 1]

    text = (
        f"اليوم: {day_name}\n"
        f"التاريخ الهجري: {hijri_date.day} {hijri_month_name} {hijri_date.year} هـ\n"
        f"الموافق: {today_gregorian.day} {gregorian_month_name} {today_gregorian.year} م"
    )
    await query.edit_message_text(text, reply_markup=query.message.reply_markup)

async def show_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    timezone_str = await db.get_timezone()
    user_timezone = pytz.timezone(timezone_str)
    now = datetime.now(user_timezone)

    time_str = now.strftime("%I:%M:%S %p")
    time_str_ar = time_str.replace("AM", "صباحاً").replace("PM", "مساءً")

    city_name_en = timezone_str.split('/')[-1]
    if city_name_en == "Aden": city_name_en = "Sanaa" # استبدال خاص
    
    city_name_ar = CITY_NAMES_AR.get(city_name_en, city_name_en)

    text = f"الساعة الآن: {time_str_ar}\nبتوقيت: {city_name_ar}"
    await query.edit_message_text(text, reply_markup=query.message.reply_markup)

async def show_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    reminder = await db.get_random_reminder()
    text = reminder['text'] if reminder else "لا توجد أذكار مضافة حالياً."
    
    await query.edit_message_text(text, reply_markup=query.message.reply_markup)

async def contact_admin_handler_func(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    # التحقق من الاشتراك قبل السماح بالتواصل
    if not await is_user_subscribed(query.effective_user.id, context):
        await query.answer("عذراً، يجب عليك الاشتراك في القنوات أولاً.", show_alert=True)
        return
        
    text = await db.get_text('contact_prompt', "تفضل بإرسال رسالتك الآن (نص، صورة، ملصق...) وسيتم توصيلها إلى الإدارة.")
    await query.edit_message_text(text)


show_date_handler = CallbackQueryHandler(show_date, pattern="^show_date$")
show_time_handler = CallbackQueryHandler(show_time, pattern="^show_time$")
show_reminder_handler = CallbackQueryHandler(show_reminder, pattern="^show_reminder$")
contact_admin_handler = CallbackQueryHandler(contact_admin_handler_func, pattern="^contact_admin$")
