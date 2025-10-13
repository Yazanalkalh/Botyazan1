# -*- coding: utf-8 -*-

from aiogram import types
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.dispatcher.handler import CancelHandler

from bot.database.manager import db
from config import ADMIN_USER_ID

class BanMiddleware(BaseMiddleware):
    """
    هذا الوسيط يتحقق من كل تحديث وارد.
    إذا كان المستخدم محظوراً، فإنه يمنع أي معالج آخر من العمل.
    """
    async def on_pre_process_update(self, update: types.Update, data: dict):
        user = None
        if update.message:
            user = update.message.from_user
        elif update.callback_query:
            user = update.callback_query.from_user
        
        # إذا كان هناك مستخدم، وليس هو المدير
        if user and user.id != ADMIN_USER_ID:
            # تحقق مما إذا كان محظوراً
            if await db.is_user_banned(user.id):
                # أوقف كل شيء
                raise CancelHandler()
