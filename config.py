# -*- coding: utf-8 -*-

import os

# --- شرح ---
# هذا الملف يقرأ الإعدادات الحساسة بأمان من متغيرات البيئة في Render.

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")

# تأكد من تحويل المعرف إلى عدد صحيح
ADMIN_USER_ID_STR = os.getenv("ADMIN_USER_ID")
ADMIN_USER_ID = int(ADMIN_USER_ID_STR) if ADMIN_USER_ID_STR and ADMIN_USER_ID_STR.isdigit() else None

# تحقق من وجود المتغيرات الأساسية
if not TELEGRAM_TOKEN or not MONGO_URI or not ADMIN_USER_ID:
    print("خطأ: يرجى التأكد من تعيين متغيرات البيئة التالية في Render:")
    print("TELEGRAM_TOKEN, MONGO_URI, ADMIN_USER_ID")
    exit()
