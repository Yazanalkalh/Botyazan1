# -*- coding: utf-8 -*-

from aiogram import types
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.dispatcher.handler import CancelHandler

from bot.database.manager import db
from config import ADMIN_USER_ID

class SecurityMiddleware(BaseMiddleware):
    """
    جدار حماية شامل لتطبيق قواعد الأمان على رسائل المستخدمين.
    """
    async def on_pre_process_update(self, update: types.Update, data: dict):
        # نحاول الحصول على كائن المستخدم من أي نوع من التحديثات
        user = getattr(update, 'from_user', None)
        if not user:
            # إذا لم نتمكن من تحديد المستخدم، نتجاهل التحديث
            return

        # المدير معفى من جميع القيود
        if user.id == ADMIN_USER_ID:
            return

        # --- 1. التحقق من حالة البوت العامة ---
        settings = await db.get_security_settings()
        if settings.get("bot_status") == "inactive":
            raise CancelHandler() # إيقاف كل شيء إذا كان البوت متوقفاً

        # --- 2. التحقق من الوسائط الممنوعة (فقط للرسائل) ---
        if update.message:
            message = update.message
            blocked_media = settings.get("blocked_media", {})
            rejection_message = await db.get_text("security_rejection_message")
            
            # قائمة بالأنواع الممنوعة وحالاتها
            checks = {
                "photo": message.photo and blocked_media.get("photo"),
                "video": message.video and blocked_media.get("video"),
                "sticker": message.sticker and blocked_media.get("sticker"),
                "document": message.document and blocked_media.get("document"),
                "audio": message.audio and blocked_media.get("audio"),
                "voice": message.voice and blocked_media.get("voice"),
                # التحقق الذكي من الروابط
                "link": (message.entities and any(e.type in ['url', 'text_link'] for e in message.entities)) and blocked_media.get("link"),
            }
            
            # إذا كان أي من الشروط صحيحاً، نرفض الرسالة
            if any(checks.values()):
                try:
                    await message.reply(rejection_message)
                except Exception:
                    pass # نتجاهل الأخطاء في حال لم يتمكن البوت من الرد
                raise CancelHandler()
