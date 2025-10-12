# -*- coding: utf-8 -*-

from aiogram import types, Dispatcher

from config import ADMIN_USER_ID
# نستدعي "حارس البوابة" الذي بنيناه للتأكد من اشتراك المستخدم
from bot.handlers.user.start import is_user_subscribed

async def forward_message_to_admin(message: types.Message):
    """
    يعالج أي رسالة من المستخدم (نص، صورة، إلخ).
    يتحقق من الاشتراك ثم يعيد توجيه الرسالة إلى المدير.
    """
    user_id = message.from_user.id
    
    # الخطوة الأولى والأهم: التحقق من الاشتراك
    if not await is_user_subscribed(user_id, message.bot):
        # إذا لم يكن مشتركاً، نتجاهل الرسالة بصمت ولا نزعج المستخدم
        return

    # إذا كان مشتركاً، قم بإعادة توجيه الرسالة كما هي إلى المدير
    try:
        await message.forward(chat_id=ADMIN_USER_ID)
        
        # (اختياري ولكن مفيد جداً) إرسال رسالة نصية منفصلة بمعلومات المستخدم
        # هذا يساعدك في معرفة من المرسل حتى لو لم يكن لديه اسم مستخدم
        user_info = (
            f"رسالة جديدة من:\n"
            f"الاسم: {message.from_user.full_name}\n"
            f"المعرف: `{user_id}`\n"
            f"اسم المستخدم: @{message.from_user.username if message.from_user.username else 'لا يوجد'}"
        )
        await message.bot.send_message(ADMIN_USER_ID, user_info, parse_mode=types.ParseMode.MARKDOWN)

    except Exception as e:
        print(f"فشل في إعادة توجيه الرسالة من المستخدم {user_id}: {e}")


def register_message_handlers(dp: Dispatcher):
    """
    تسجيل معالج الرسائل.
    content_types=types.ContentTypes.ANY تعني أنه سيلتقط كل أنواع الرسائل.
    """
    dp.register_message_handler(forward_message_to_admin, content_types=types.ContentTypes.ANY)
