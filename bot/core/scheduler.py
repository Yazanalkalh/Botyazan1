# -*- coding: utf-8 -*-

import logging
import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot

logger = logging.getLogger(__name__)

# --- وظيفة التنفيذ: هذا ما سيتم تشغيله عندما يحين الوقت ---
async def send_scheduled_post(bot: Bot, job_id: str, message_data: dict, target_channels: list):
    """
    الدالة التي يتم استدعاؤها بواسطة المؤقت لإرسال المنشور.
    """
    from bot.database.manager import db

    logger.info(f"⏰ Executing scheduled job: {job_id}")
    success_count = 0
    failed_count = 0
    
    channels_to_publish = target_channels
    if not channels_to_publish:
        channels_docs = await db.get_all_publishing_channels()
        channels_to_publish = [doc['channel_id'] for doc in channels_docs]

    for channel_id in channels_to_publish:
        try:
            await bot.copy_message(
                chat_id=channel_id,
                from_chat_id=message_data['chat_id'],
                message_id=message_data['message_id']
            )
            success_count += 1
        except Exception as e:
            failed_count += 1
            logger.error(f"Failed to send scheduled post to channel {channel_id}: {e}")
    
    logger.info(f"✅ Job {job_id} finished. Success: {success_count}, Failed: {failed_count}")
    await db.mark_scheduled_post_as_done(job_id)

# --- محرك الجدولة الرئيسي ---
scheduler = AsyncIOScheduler(timezone="Asia/Riyadh")

async def load_pending_jobs(bot: Bot):
    """
    يقرأ كل المهام المعلقة من قاعدة البيانات عند بدء التشغيل ويعيد جدولتها.
    """
    from bot.database.manager import db
    
    logger.info(" re-loading pending scheduled jobs from database...")
    pending_jobs = await db.get_all_pending_scheduled_posts()
    count = 0
    for job_data in pending_jobs:
        try:
            # --- 💡 بداية الإصلاح النهائي لمشكلة المناطق الزمنية 💡 ---
            # الوقت المحفوظ في قاعدة البيانات يكون "غافلاً" (naive), لكنه مخزن بتوقيت UTC.
            # الخطوة 1: نجعله "واعياً" (aware) عن طريق إخباره أن منطقته الزمنية هي UTC.
            run_date_aware = job_data['run_date'].replace(tzinfo=datetime.timezone.utc)
            
            # الخطوة 2: نحصل على الوقت الحالي وهو أيضاً "واعٍ" وبتوقيت UTC.
            now_aware = datetime.datetime.now(datetime.timezone.utc)

            # الخطوة 3: الآن المقارنة آمنة وصحيحة لأن كلا الوقتين يعرفان منطقتهما الزمنية.
            if run_date_aware > now_aware:
                scheduler.add_job(
                    send_scheduled_post,
                    "date",
                    run_date=job_data['run_date'], # الجدولة تستخدم الوقت الأصلي
                    id=job_data['_id'],
                    args=[bot, job_data['_id'], job_data['message_data'], job_data['target_channels']],
                    replace_existing=True
                )
                count += 1
            else:
                # إذا كان الوقت قد مضى، نضع علامة "منفذ" على المهمة لتجنب إرسالها
                await db.mark_scheduled_post_as_done(job_data['_id'])
                logger.warning(f"Skipped expired job: {job_data['_id']}")
            # --- 💡 نهاية الإصلاح النهائي 💡 ---
        except Exception as e:
            logger.error(f"Failed to load job {job_data.get('_id', 'UNKNOWN')}: {e}")

    logger.info(f"✅ Reloaded {count} pending jobs.")
