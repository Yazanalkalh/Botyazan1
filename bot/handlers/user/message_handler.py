# -*- coding: utf-8 -*-

from telegram import Update
from telegram.ext import MessageHandler, filters, ContextTypes

from config import ADMIN_USER_ID
from .start import check_subscription

# --- شرح ---
# هذا هو "ساعي البريد". وظيفته هي أخذ أي رسالة من المستخدم وإعادة توجيهها إلى المدير.

async def forward_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """يعيد توجيه رسالة المستخدم إلى المدير بعد التحقق من الاشتراك."""
    # لا نعيد توجيه الرسائل من المدير نفسه
    if update.effective_user.id == ADMIN_USER_ID:
        return

    # أولاً، تحقق من الاشتراك الإجباري
    is_subscribed = await check_subscription(update, context)
    if not is_subscribed:
        return

    user = update.effective_user
    message = update.message

    # رسالة تعريفية بالمرسل
    user_info = (
        f"📩 رسالة جديدة من المستخدم:\n\n"
        f"👤 **الاسم:** {user.full_name}\n"
        f"🆔 **المعرف:** `{user.id}`"
    )
    if user.username:
        user_info += f"\n🔗 **اليوزر:** @{user.username}"

    await context.bot.send_message(chat_id=ADMIN_USER_ID, text=user_info, parse_mode='Markdown')
    
    # إعادة توجيه الرسالة الأصلية للمدير
    await message.forward(chat_id=ADMIN_USER_ID)

# المعالج يستمع لجميع أنواع الرسائل التي ليست أوامر
message_forwarder_handler = MessageHandler(filters.ALL & ~filters.COMMAND, forward_to_admin)
