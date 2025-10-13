# -*- coding: utf-8 -*-

import datetime
import time
from aiogram import types, Dispatcher

from bot.database.manager import db
# 💡 نستورد متغير وقت البدء من ملفك الرئيسي
# الكود التالي يحاول الاستيراد من main.py وإذا فشل يجرب app.py
try:
    from main import START_TIME 
except ImportError:
    from app import START_TIME

def format_uptime(duration: datetime.timedelta) -> str:
    """يحول مدة زمنية إلى نص مقروء (أيام، ساعات، دقائق)."""
    days = duration.days
    hours, remainder = divmod(duration.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    
    parts = []
    if days > 0:
        parts.append(f"{days} يوم")
    if hours > 0:
        parts.append(f"{hours} ساعة")
    if minutes > 0 or not parts:
        parts.append(f"{minutes} دقيقة")
    
    return " و ".join(parts)

async def show_system_status(call: types.CallbackQuery):
    """
    يجمع معلومات حيوية عن حالة البوت ويعرضها.
    """
    await call.answer("جاري فحص الأنظمة...")

    # --- 1. فحص المؤشرات الحيوية ---
    bot_status_text = await db.get_text("sm_status_operational")
    
    db_ok = await db.ping_database()
    db_status_text = await db.get_text("sm_status_connected") if db_ok else await db.get_text("sm_status_unreachable")
    
    # --- 2. قياس الأداء ---
    uptime_delta = datetime.datetime.now() - START_TIME
    uptime_str = format_uptime(uptime_delta)
    
    start_ping_time = time.time()
    await call.bot.get_me()
    latency_ms = (time.time() - start_ping_time) * 1000
    latency_str = f"{int(latency_ms)} ميلي ثانية"
    
    # --- 3. معلومات النشر ---
    last_update_str = START_TIME.strftime("%Y/%m/%d - %I:%M %p").replace("AM", "صباحاً").replace("PM", "مساءً")

    # --- 4. تجميع الرسالة ---
    title = await db.get_text("sm_title")
    overall_status = await db.get_text("sm_status_ok") if db_ok else await db.get_text("sm_status_degraded")

    status_message = (
        f"{title}\n"
        f"*{overall_status}*\n\n"
        f"**{(await db.get_text('sm_health_checks'))}:**\n"
        f"  - {(await db.get_text('sm_bot_status'))}: `{bot_status_text}`\n"
        f"  - {(await db.get_text('sm_db_status'))}: `{db_status_text}`\n\n"
        f"**{(await db.get_text('sm_performance'))}:**\n"
        f"  - {(await db.get_text('sm_uptime'))}: `{uptime_str}`\n"
        f"  - {(await db.get_text('sm_tg_latency'))}: `{latency_str}`\n\n"
        f"**{(await db.get_text('sm_deploy_info'))}:**\n"
        f"  - {(await db.get_text('sm_last_update'))}: `{last_update_str}`"
    )

    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton(text=await db.get_text("stats_refresh_button"), callback_data="admin:system_monitoring"),
        types.InlineKeyboardButton(text=await db.get_text("ar_back_button"), callback_data="admin:panel:back")
    )
    
    try:
        await call.message.edit_text(status_message, reply_markup=keyboard, parse_mode="Markdown")
    except Exception:
        pass


def register_system_monitoring_handlers(dp: Dispatcher):
    """
    يسجل معالج واجهة مراقبة النظام.
    """
    dp.register_callback_query_handler(show_system_status, text="admin:system_monitoring", is_admin=True, state="*")
