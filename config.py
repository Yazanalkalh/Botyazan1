# -*- coding: utf-8 -*-

import os
from dotenv import load_dotenv

# تحميل متغيرات البيئة من ملف .env (للتشغيل المحلي)
load_dotenv()

# --- المتغيرات الأساسية ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")

# --- متغيرات المدير ---
# تحويل ADMIN_USER_ID إلى رقم صحيح (int) للتعامل معه بسهولة
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", 0))

# تأكد من أن المتغيرات الأساسية موجودة
if not TELEGRAM_TOKEN or not MONGO_URI or not ADMIN_USER_ID:
    print("خطأ فادح: أحد متغيرات البيئة الأساسية (TELEGRAM_TOKEN, MONGO_URI, ADMIN_USER_ID) غير موجود.")
    exit()
