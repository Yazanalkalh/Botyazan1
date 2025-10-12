# -*- coding: utf-8 -*-

import pytz
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler
from hijri_converter import Gregorian
from bot.database.manager import db

# --- قاموس لترجمة أسماء المدن والكلمات ---
TRANSLATIONS = {
    # أيام الأسبوع
    "Saturday": "السبت", "Sunday": "الأحد", "Monday": "الإثنين", 
    "Tuesday": "الثلاثاء", "Wednesday": "الأربعاء", "Thursday": "الخميس", "Friday": "الجمعة",
    # الشهور الهجرية
    1: "محرم", 2: "صفر", 3: "ربيع الأول", 4: "ربيع الآخر",
    5: "جمادى الأولى", 6: "جمادى الآخرة", 7: "رجب", 8: "شعبان",
    9: "رمضان", 10: "شوال", 11: "ذو القعدة", 12: "ذو الحجة",
    # الشهور الميلادية
    "January": "يناير", "February": "فبراير", "March": "مارس", "April": "أبريل",
    "May": "مايو", "June": "يونيو", "July": "يوليو", "August": "أغسطس",
    "September": "سبتمبر", "October": "أكتوبر", "November": "نوفمبر", "December": "ديسمبر",
    # المدن
    "Aden": "صنعاء",  # عرض صنعاء بدلاً من عدن
    "Riyadh": "الرياض",
    "Cairo": "القاهرة",
    "Dubai": "دبي",
    # AM/PM
    "AM": "صباحاً",
    "PM": "مساءً"
}

# --- وظائف الأزرار ---

async def show_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """يعرض التاريخ الهجري والميلادي باللغة العربية."""
    query = update.callback_query
    await query.answer()
    
    today = datetime.now()
    # تحويل التاريخ الميلادي إلى هجري
    hijri_date = Gregorian(today.year, today.month, today.day).to_hijri()
    
    # ترجمة الأسماء
    day_name_en = today.strftime("%A")
    month_name_en = today.strftime("%B")
    
    day_name_ar = TRANSLATIONS.get(day_name_en, day_name_en)
    hijri_month_ar = TRANSLATIONS.get(hijri_date.month, str(hijri_date.month))
    gregorian_month_ar = TRANSLATIONS.get(month_name_en, month_name_en)

    date_text = (
        f"اليوم: {day_name_ar}\n"
        f"التاريخ: {hijri_date.day} {hijri_month_ar} {hijri_date.year} هـ\n"
        f"الموافق: {today.day} {gregorian_month_ar} {today.year} م"
    )
    
    await query.edit_message_text(text=date_text, reply_markup=query.message.reply_markup)

async def show_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """يعرض الوقت الحالي حسب المنطقة الزمنية المحددة."""
    query = update.callback_query
    await query.answer()

    timezone_str = await db.get_timezone()
    city_name_en = timezone_str.split('/')[-1]
    
    # استبدال عدن بصنعاء للعرض فقط
    display_city_en = "Sanaa" if city_name_en == "Aden" else city_name_en
    city_name_ar = TRANSLATIONS.get(display_city_en, display_city_en)
    
    timezone = pytz.timezone(timezone_str)
    current_time = datetime.now(timezone)
    
    # تنسيق الوقت مع صباحاً/مساءً
    time_str_en = current_time.strftime("%I:%M:%S %p")
    time_str_ar = time_str_en.replace("AM", TRANSLATIONS["AM"]).replace("PM", TRANSLATIONS["PM"])
    
    time_text = f"الساعة الآن: {time_str_ar} بتوقيت {city_name_ar}"
    
    await query.edit_message_text(text=time_text, reply_markup=query.message.reply_markup)

async def show_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """يعرض ذكراً عشوائياً من قاعدة البيانات."""
    query = update.callback_query
    await query.answer()
    
    reminder = await db.get_random_reminder()
    if reminder:
        await query.edit_message_text(text=reminder, reply_markup=query.message.reply_markup)
    else:
        await query.edit_message_text(text="لم يتم إضافة أي أذكار بعد.", reply_markup=query.message.reply_markup)

# --- الوظيفة المفقودة التي سببت الخطأ ---
async def contact_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """يستجيب لزر التواصل مع الإدارة ويطلب من المستخدم إرسال رسالته."""
    query = update.callback_query
    await query.answer()
    
    contact_prompt_text = await db.get_text(
        "contact_prompt", 
        "تفضل بإرسال رسالتك الآن. سيتم توصيلها مباشرة إلى الإدارة."
    )
    # ملاحظة: نستخدم reply_text هنا لأننا نريد أن يتمكن المستخدم من إرسال رسالة جديدة
    await query.message.reply_text(text=contact_prompt_text)
    # نحذف الرسالة القديمة التي تحتوي على الأزرار لتنظيف الواجهة
    await query.message.delete()

# --- إنشاء المعالجات ---
show_date_handler = CallbackQueryHandler(show_date, pattern="^show_date$")
show_time_handler = CallbackQueryHandler(show_time, pattern="^show_time$")
show_reminder_handler = CallbackQueryHandler(show_reminder, pattern="^show_reminder$")
contact_admin_handler = CallbackQueryHandler(contact_admin, pattern="^contact_admin$") # <-- تعريف المعالج
