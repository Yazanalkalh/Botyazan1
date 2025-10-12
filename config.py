# -*- coding: utf-8 -*-
import os
from dotenv import load_dotenv

# تحميل المتغيرات من ملف .env (للتشغيل المحلي)
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", 0))

# التأكد من وجود المتغيرات الأساسية
if not TELEGRAM_TOKEN or not MONGO_URI or not ADMIN_USER_ID:
    print("خطأ فادح: أحد متغيرات البيئة الأساسية (TELEGRAM_TOKEN, MONGO_URI, ADMIN_USER_ID) غير موجود.")
    exit()
