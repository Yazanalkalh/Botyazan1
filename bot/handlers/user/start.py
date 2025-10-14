# -*- coding: utf-8 -*-

# --- 💡 التحسين رقم 1: استيراد asyncio 💡 ---
# هذه هي الأداة التي سنستخدمها لتنفيذ كل شيء بالتوازي.
import asyncio

from aiogram import types, Dispatcher, Bot
from aiogram.utils.exceptions import ChatNotFound, BadRequest

from bot.database.manager import db
from config import ADMIN_USER_ID

async def notify_admin_of_new_user(user: types.User, bot: Bot):
    """(لا تغيير هنا) يرسل إشعاراً للمدير عند دخول مستخدم جديد."""
    try:
        user_link = f'<a href="tg://user?id={user.id}">{user.full_name}</a>'
        username = f"@{user.username}" if user.username else "لا يوجد"
        
        notification_text = (
            f"👤 <b>دخل شخص جديد إلى البوت</b>\n\n"
            f"🗣️ <b>اسمه:</b> {user_link}\n"
            f"🌀 <b>معرفه:</b> {username}\n"
            f"🆔 <b>ايديه:</b> <code>{user.id}</code>"
        )
        
        await bot.send_message(
            chat_id=ADMIN_USER_ID,
            text=notification_text,
            parse_mode=types.ParseMode.HTML
        )
    except Exception as e:
        print(f"فشل إرسال إشعار المستخدم الجديد: {e}")

async def is_user_subscribed(user_id: int, bot: Bot) -> bool:
    """
    💡 التحسين رقم 2: دالة التحقق من الاشتراك فائقة السرعة.
    بدلاً من التحقق من كل قناة على حدة، يتم الآن التحقق منها كلها في نفس الوقت.
    """
    # الخطوة 1: نقرأ من الذاكرة المؤقتة، هذه العملية فورية.
    is_enabled = await db.get_force_subscribe_status()
    if not is_enabled:
        return True 

    required_channels = await db.get_subscription_channels()
    if not required_channels:
        return True

    # إنشاء قائمة بمهام التحقق (بدون تنفيذها بعد)
    check_tasks = [
        bot.get_chat_member(chat_id=f"@{channel_username}", user_id=user_id)
        for channel_username in required_channels
    ]

    # تنفيذ جميع مهام التحقق بالتوازي وفي نفس الوقت
    results = await asyncio.gather(*check_tasks, return_exceptions=True)

    # التحقق من النتائج
    for result in results:
        # إذا حدث خطأ (مثل قناة غير موجودة)، نتجاهله ونكمل
        if isinstance(result, Exception):
            # يمكنك تسجيل الخطأ هنا إذا أردت
            # print(f"خطأ أثناء التحقق من قناة: {result}")
            continue
        
        # إذا لم يكن المستخدم عضواً في أي قناة، نرجِع False فوراً
        if result.status not in ["creator", "administrator", "member"]:
            return False
            
    # إذا نجح في كل القنوات، فهو مشترك
    return True

async def show_main_menu(message: types.Message, user: types.User, edit_mode: bool = False):
    """
    💡 التحسين رقم 3: جلب جميع النصوص دفعة واحدة.
    على الرغم من أن النصوص تأتي من الذاكرة المؤقتة السريعة،
    إلا أن هذا الأسلوب يضمن أفضل أداء ممكن دائماً.
    """
    # إنشاء مهام جلب النصوص
    text_tasks = {
        "date": db.get_text("date_button"),
        "time": db.get_text("time_button"),
        "reminder": db.get_text("reminder_button"),
        "welcome": db.get_text("welcome_message"),
    }
    
    # تنفيذ المهام بالتوازي
    results = await asyncio.gather(*text_tasks.values())
    
    # ربط النتائج بالأسماء
    texts = dict(zip(text_tasks.keys(), results))

    keyboard = types.InlineKeyboardMarkup(row_width=3)
    keyboard.add(
        types.InlineKeyboardButton(text=texts["date"], callback_data="show_date"),
        types.InlineKeyboardButton(text=texts["time"], callback_data="show_time"),
        types.InlineKeyboardButton(text=texts["reminder"], callback_data="show_reminder")
    )

    template = texts["welcome"]
    # (بقية الكود لمعالجة النص كما هو)
    name_user_mention = user.get_mention(as_html=True)
    username_mention = f"@{user.username}" if user.username else "لا يوجد"
    processed_text = template.replace("#name_user", name_user_mention).replace("#username", f"@{user.username}" if user.username else "لا يوجد").replace("#name", user.first_name).replace("#id", str(user.id))
    
    # (إرسال الرسالة كما هو)
    if edit_mode:
        try:
            await message.edit_text(text=processed_text, reply_markup=keyboard, parse_mode=types.ParseMode.HTML)
        except Exception: pass
    else:
        await message.answer(text=processed_text, reply_markup=keyboard, parse_mode=types.ParseMode.HTML)

async def show_subscription_message(message: types.Message):
    """(لا تغيير هنا) يعرض رسالة وقنوات الاشتراك الإجباري."""
    channels = await db.get_subscription_channels()
    keyboard = types.InlineKeyboardMarkup()
    text = "🛑 <b>عذراً، يجب عليك الاشتراك في القنوات التالية أولاً لاستخدام البوت:</b>\n\n"
    for username in channels:
        text += f"▪️ @{username}\n"
        keyboard.add(types.InlineKeyboardButton(text=f"الانضمام إلى @{username}", url=f"https://t.me/{username}"))
    keyboard.add(types.InlineKeyboardButton(text="✅ لقد اشتركت، تحقق الآن", callback_data="check_subscription"))
    await message.answer(text, reply_markup=keyboard, parse_mode=types.ParseMode.HTML)

async def start_command(message: types.Message):
    """
    💡 التحسين رقم 4: المعالج الرئيسي فائق السرعة.
    يقوم بإضافة المستخدم والتحقق من اشتراكه في نفس الوقت،
    ويرسل إشعار المدير في الخلفية دون أن ينتظره المستخدم.
    """
    user = message.from_user

    # تنفيذ مهمتي إضافة المستخدم والتحقق من الاشتراك بالتوازي
    is_new, is_subscribed = await asyncio.gather(
        db.add_user(user),
        is_user_subscribed(user.id, message.bot)
    )

    # إذا كان مستخدماً جديداً، أرسل الإشعار في الخلفية (لا تنتظر)
    if is_new:
        asyncio.create_task(notify_admin_of_new_user(user, message.bot))
    
    # الآن، بناءً على النتائج التي حصلنا عليها، أظهر القائمة المناسبة
    if is_subscribed:
        await show_main_menu(message, user=user)
    else:
        await show_subscription_message(message)

async def check_subscription_callback(call: types.CallbackQuery):
    """
    (لا يوجد تغيير مباشر هنا) يستفيد هذا المعالج تلقائياً
    من سرعة دالة `is_user_subscribed` المُحسَّنة.
    """
    await call.answer(text="جاري التحقق من اشتراكك...", show_alert=False)
    user = call.from_user
    if await is_user_subscribed(user.id, call.bot):
        await show_main_menu(call.message, user=user, edit_mode=True)
    else:
        await call.answer(text="عذراً، لم تشترك في جميع القنوات بعد. يرجى المحاولة مرة أخرى.", show_alert=True)

def register_start_handlers(dp: Dispatcher):
    """(لا تغيير هنا) وظيفة التسجيل التلقائي لهذه الوحدة."""
    dp.register_message_handler(start_command, commands=["start"])
    dp.register_callback_query_handler(check_subscription_callback, text="check_subscription")
