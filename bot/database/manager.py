# -*- coding: utf-8 -*-

from pymongo import MongoClient
from config import MONGO_URI

# --- شرح ---
# هذا الملف مسؤول عن إنشاء الاتصال بقاعدة البيانات مرة واحدة فقط عند بدء تشغيل البوت
try:
    client = MongoClient(MONGO_URI)
    db = client.get_database("IslamicBotDB")
    print("تم الاتصال بقاعدة بيانات MongoDB بنجاح.")
except Exception as e:
    print(f"فشل الاتصال بقاعدة البيانات: {e}")
    db = None
