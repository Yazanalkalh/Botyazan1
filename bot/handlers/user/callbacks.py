# -*- coding: utf-8 -*-

import pytz
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler
from hijri_converter import Hijri, Gregorian

from bot.database.manager import db

# --- قاموس لترجمة أسماء المدن إلى العربية ---
city_names_ar = {
    "Riyadh": "الرياض",
    "Aden": "عدن", # سيبقى هذا موجوداً كمرجع احتياطي
    "Sanaa": "صنعاء", # الاسم الذي سيتم عرضه
    "Dubai": "دبي",
    "Cairo": "القاهرة",
    "Baghdad": "بغداد",
    "Kuwait": "الكويت",
    "Qatar": "قطر",
    "Bahrain": "البحرين",
    "Muscat": "مسقط",
    "Amman": "عمان",
    "Damascus": "دمشق",
    "Beirut": "بيروت",
    "Jerusalem": "القدس",
}

# --- قواميس لترجمة التواريخ ---
arabic_months = {
    1: "محرم", 2: "صفر", 3: "ربيع الأول", 4: "ربيع الثاني",
    5: "جمادى الأولى", 6: "جمادى الآخرة", 7: "رجب", 8: "شعبان",
    9: "رمضان", 10: "شوال", 11: "ذو القعدة", 12: "ذو الحجة"
}
arabic_days = {
    "Saturday": "السبت", "Sunday": "الأحد", "Monday": "الإثنين",
    "Tuesday": "الثلاثاء", "Wednesday": "الأربعاء", "Thursday": "الخميس",
    "Friday": "الجمعة"
}

async def check_subscription_before_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """وظيفة للتحقق من اشتراك المستخدم قبل تنفيذ أي إجراء."""
    user_id = update.effective_user.id
    channels = await db.get_subscription_channels()
    if not channels:
        return True

    text_configs = await db.get_text_configs()
    not_subscribed_message = text_configs.get(
        'not_subscribed_message',
        "عذراً، يجب عليك الاشتراك في القنوات التالية لاستخدام البوت:"
    )

    subscribed = True
    channels_to_join = []
    for channel in channels:
        try:
            member = await context.bot.get_chat_member(chat_id=channel['channel_id'], user_id=user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                subscribed = False
                channels_to_join.append(f"https://t.me/{channel['channel_username']}")
        except Exception as e:
            print(f"Error checking subscription for channel {channel['channel_id']}: {e}")
            subscribed = False
            channels_to_join.append(f"https://t.me/{channel['channel_username']}")
    
    if not subscribed:
        full_message = f"{not_subscribed_message}\n\n" + "\n".join(channels_to_join)
        
        # نستخدم query.message.reply_text بدلاً من query.edit_message_text
        # لإرسال رسالة جديدة وعدم تعديل الرسالة القديمة
        await update.callback_query.message.reply_text(full_message)

    return subscribed

async def show_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """يعرض التاريخ الهجري والميلادي باللغة العربية."""
    query = update.callback_query
    await query.answer()

    if not await check_subscription_before_action(update, context):
        return

    today = datetime.now()
    # تحويل التاريخ الميلادي إلى صيغة قابلة للتحويل
    gregorian_date = Gregorian(today.year, today.month, today.day)
    hijri_date = gregorian_date.to_hijri()

    day_name_en = today.strftime('%A')
    day_name_ar = arabic_days.get(day_name_en, day_name_en)
    
    hijri_month_ar = arabic_months.get(hijri_date.month, str(hijri_date.month))
    gregorian_month_name = today.strftime('%B') # اسم الشهر الميلادي بالانجليزية

    date_message = (
        f"اليوم : {day_name_ar}\n"
        f"التاريخ : {hijri_date.day} {hijri_month_ar} {hijri_date.year} هـ\n"
        f"الموافق : {today.day} / {today.month} / {today.year} م"
    )

    await query.edit_message_text(text=date_message, reply_markup=query.message.reply_markup)

async def show_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """يعرض الوقت الحالي باللغة العربية مع اسم المدينة المترجم."""
    query = update.callback_query
    await query.answer()

    if not await check_subscription_before_action(update, context):
        return

    timezone_str = await db.get_timezone()
    
    try:
        tz = pytz.timezone(timezone_str)
        now = datetime.now(tz)
        
        # تنسيق الوقت واستبدال AM/PM بالعربية
        time_str_en = now.strftime("%I:%M:%S %p")
        time_str_ar = time_str_en.replace("AM", "صباحاً").replace("PM", "مساءً")
        
        # --- السطر السحري ---
        # استخراج اسم المدينة وتغييره إذا كان "Aden"
        city_en = timezone_str.split('/')[-1]
        if city_en == "Aden":
            city_en = "Sanaa" # هنا يتم التغيير
        # --------------------

        city_ar = city_names_ar.get(city_en, city_en)
        
        message = f"الساعة الآن {time_str_ar} بتوقيت {city_ar}"
        
    except pytz.UnknownTimeZoneError:
        message = "حدث خطأ في تحديد المنطقة الزمنية. يرجى مراجعة الإعدادات."
    except Exception as e:
        print(f"Error in show_time: {e}")
        message = "حدث خطأ ما."

    await query.edit_message_text(text=message, reply_markup=query.message.reply_markup)

async def show_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """يعرض ذكراً عشوائياً من قاعدة البيانات."""
    query = update.callback_query
    await query.answer()

    if not await check_subscription_before_action(update, context):
        return

    reminder = await db.get_random_reminder()
    text_configs = await db.get_text_configs()
    
    if reminder:
        await query.edit_message_text(text=reminder, reply_markup=query.message.reply_markup)
    else:
        no_reminders_text = text_configs.get('no_reminders_message', "لم تتم إضافة أي أذكار بعد.")
        await query.edit_message_text(text=no_reminders_text, reply_markup=query.message.reply_markup)

# --- المعالجات ---
show_date_handler = CallbackQueryHandler(show_date, pattern="^show_date$")
show_time_handler = CallbackQueryHandler(show_time, pattern="^show_time$")
show_reminder_handler = CallbackQueryHandler(show_reminder, pattern="^show_reminder$")
