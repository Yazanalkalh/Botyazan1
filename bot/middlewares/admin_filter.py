# -*- coding: utf-8 -*-

from aiogram import types
from aiogram.dispatcher.filters import BoundFilter
from config import ADMIN_USER_ID

class IsAdminFilter(BoundFilter):
    """
    فلتر مخصص للتحقق مما إذا كان المستخدم هو المدير.
    """
    key = 'is_admin'

    def __init__(self, is_admin: bool):
        self.is_admin = is_admin

    async def check(self, obj: types.base.TelegramObject) -> bool:
        user = getattr(obj, 'from_user', None)
        if not user:
            return False
        
        # التحقق من أن هوية المستخدم تطابق هوية المدير من ملف الإعدادات
        return user.id == ADMIN_USER_ID
