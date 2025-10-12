# -*- coding: utf-8 -*-
import asyncio
import logging
from flask import Flask
from bot.database.manager import db
from telegram.ext import Application, CommandHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = "YOUR_BOT_TOKEN"
MONGO_URI = "YOUR_MONGO_URI"

# --- إنشاء تطبيق Flask ---
flask_app = Flask(__name__)

@flask_app.route("/")
def index():
    return "خادم Flask يعمل!"

# --- وظيفة بدء التشغيل للبوت ---
async def startup(application: Application):
    await db.connect_to_database(MONGO_URI)
    logger.info("قاعدة البيانات جاهزة!")

# --- إعداد البوت ---
application = Application.builder().token(BOT_TOKEN).build()

# مثال على أمر /start
async def start_command(update, context):
    await update.message.reply_text("مرحباً! البوت قيد التشغيل.")

application.add_handler(CommandHandler("start", start_command))

# تنفيذ startup بعد تشغيل البوت
application.post_init = startup

# --- تشغيل Flask في مهمة منفصلة ---
async def run_flask():
    from hypercorn.asyncio import serve
    from hypercorn.config import Config

    config = Config()
    config.bind = ["0.0.0.0:10000"]  # بورت Render
    await serve(flask_app, config)

# --- نقطة البداية ---
async def main():
    # تشغيل Flask في مهمة مستقلة
    asyncio.create_task(run_flask())

    # تشغيل البوت
    await application.run_polling()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("تم إيقاف التطبيق.")
