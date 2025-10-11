# -*- coding: utf-8 -*-

from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler
from datetime import datetime
from hijri_converter import Gregorian
import pytz

# --- شرح ---
# هذا هو الملف الذي يقوم بالعمل الحقيقي عند ضغط المستخدم على الأزرار
# كل دالة هنا تقوم بحساب وتنسيق الرد في نفس لحظة الضغط على الزر

# قائمة لأسماء الأيام والشهور باللغة العربية
DAYS_AR = ["الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]
MONTHS_AR = ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو", "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"]

async def user_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    callback_data = query.data

    if callback_data == 'show_date':
        # الحصول على التاريخ الميلادي الحالي
        gregorian_date = datetime.now()
        
        # تحويله إلى هجري
        hijri_date = Gregorian(gregorian_date.year, gregorian_date.month, gregorian_date.day).to_hijri()
        
        # تنسيق التاريخ الميلادي باللغة العربية
        day_name_ar = DAYS_AR[gregorian_date.weekday()]
        month_name_ar = MONTHS_AR[gregorian_date.month - 1]
        gregorian_formatted = f"{day_name_ar}، {gregorian_date.day} {month_name_ar} {gregorian_date.year} م"
        
        # تجميع النص النهائي حسب التنسيق المطلوب
        text = (
            f"<b>اليوم:</b> {hijri_date.day_name()}\n"
            f"<b>التاريخ الهجري:</b> {hijri_date.day} {hijri_date.month_name()} {hijri_date.year} هـ\n"
            f"<b>الموافق:</b> {gregorian_formatted}"
        )
        await query.edit_message_text(text=text, parse_mode='HTML', reply_markup=query.message.reply_markup)

    elif callback_data == 'show_time':
        # تحديد المنطقة الزمنية المطلوبة (سنجعلها قابلة للتغيير لاحقاً)
        timezone_str = "Asia/Sanaa"
        timezone = pytz.timezone(timezone_str)
        
        # الحصول على الوقت الحالي في تلك المنطقة الزمنية
        now = datetime.now(timezone)
        
        # تنسيق الوقت (12 ساعة مع صباحاً/مساءً)
        time_formatted = now.strftime('%I:%M:%S %p')
        
        # استبدال AM/PM باللغة العربية
        time_formatted = time_formatted.replace("AM", "صباحاً").replace("PM", "مساءً")
        
        city_name = timezone_str.split('/')[-1] # للحصول على اسم المدينة "Sanaa"
        
        text = f"⏰ الساعة الآن <b>{time_formatted}</b>\nبتوقيت {city_name}"
        await query.edit_message_text(text=text, parse_mode='HTML', reply_markup=query.message.reply_markup)

    elif callback_data == 'show_reminder':
        text = "📿 أذكار اليوم:\n\n<b>سيتم سحب ذكر عشوائي من قاعدة البيانات هنا قريباً.</b>"
        await query.edit_message_text(text=text, parse_mode='HTML', reply_markup=query.message.reply_markup)

# هذا السطر يخبر البوت أن هذه الدالة مسؤولة عن معالجة الأزرار التي تبدأ بـ "show_"
user_callback_handler = CallbackQueryHandler(user_callback_query, pattern='^show_')
