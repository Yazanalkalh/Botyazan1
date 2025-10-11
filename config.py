# -*- coding: utf-8 -*-

import os
from dotenv import load_dotenv

# --- شرح ---
# هذا الملف يقرأ المتغيرات السرية (التوكن، رابط القاعدة) من بيئة العمل
# هذا يضمن أن معلوماتك الحساسة لا تكون مكتوبة مباشرة في الكود
load_dotenv()

# قراءة توكن البوت من متغيرات البيئة
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# قراءة معرّف المدير من متغيرات البيئة
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", 0))

# قراءة رابط الاتصال بقاعدة بيانات MongoDB
MONGO_URI = os.getenv("MONGO_URI")

# هذا الكود يتأكد من أنك لم تنسَ وضع أي من المتغيرات المطلوبة
if not TELEGRAM_TOKEN or not MONGO_URI or not ADMIN_USER_ID:
    raise ValueError(
        "خطأ: يرجى التأكد من تعيين المتغيرات التالية في بيئة العمل: "
        "TELEGRAM_TOKEN, ADMIN_USER_ID, MONGO_URI"
    )
