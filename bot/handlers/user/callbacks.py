# -*- coding: utf-8 -*-

from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler
from datetime import datetime
from hijri_converter import Gregorian
import pytz

# استيراد وظيفة جلب التذكير العشوائي من مدير قاعدة البيانات
from bot.database.manager import get_random_reminder

# قائمة لأسماء الأيام والشهور باللغة العربية
DAYS_AR = ["الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]
MONTHS_AR = ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو", "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"]

async def user_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    callback_data = query.data

    if callback_data == 'show_date':
        gregorian_date = datetime.now()
        hijri_date = Gregorian(gregorian_date.year, gregorian_date.month, gregororian_date.day).to_hijri()
        
        day_name_ar = DAYS_AR[gregorian_date.weekday()]
        month_name_ar = MONTHS_AR[gregorian_date.month - 1]
        gregorian_formatted = f"{day_name_ar}، {gregorian_date.day} {month_name_ar} {gregorian_date.year} م"
        
        text = (
            f"<b>اليوم:</b> {hijri_date.day_name()}\n"
            f"<b>التاريخ الهجري:</b> {hijri_date.day} {hijri_date.month_name()} {hijri_date.year} هـ\n"
            f"<b>الموافق:</b> {gregorian_formatted}"
        )
        await query.edit_message_text(text=text, parse_mode='HTML', reply_markup=query.message.reply_markup)

    elif callback_data == 'show_time':
        timezone_str = "Asia/Sanaa"
        timezone = pytz.timezone(timezone_str)
        now = datetime.now(timezone)
        time_formatted = now.strftime('%I:%M:%S %p').replace("AM", "صباحاً").replace("PM", "مساءً")
        city_name = timezone_str.split('/')[-1]
        
        text = f"⏰ الساعة الآن <b>{time_formatted}</b>\nبتوقيت {city_name}"
        await query.edit_message_text(text=text, parse_mode='HTML', reply_markup=query.message.reply_markup)

    elif callback_data == 'show_reminder':
        # --- هذا هو الجزء المحدث ---
        random_reminder = get_random_reminder()
        
        if random_reminder:
            text = f"📿 أذكار اليوم:\n\n<b>{random_reminder['text']}</b>"
        else:
            text = "📿 لم يقم المدير بإضافة أي أذكار بعد."
            
        await query.edit_message_text(text=text, parse_mode='HTML', reply_markup=query.message.reply_markup)

user_callback_handler = CallbackQueryHandler(user_callback_query, pattern='^show_')
