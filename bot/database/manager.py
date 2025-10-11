# -*- coding: utf-8 -*-

from pymongo import MongoClient
from bson import ObjectId
import random
from config import MONGO_URI

# --- شرح ---
# هذا الملف مسؤول عن إنشاء الاتصال بقاعدة البيانات وإدارة كل عملياتها

try:
    client = MongoClient(MONGO_URI)
    db = client.get_database("IslamicBotDB")
    
    # تعريف "الأقسام" أو الـ Collections التي سنتعامل معها
    reminders_collection = db["reminders_collection"] # استخدمنا اسماً فريداً
    
    print("تم الاتصال بقاعدة بيانات MongoDB بنجاح.")
except Exception as e:
    print(f"فشل الاتصال بقاعدة البيانات: {e}")
    db = None
    reminders_collection = None

# --- الوظائف الجديدة الخاصة بالتذكيرات ---

def add_reminder(text: str) -> bool:
    """يضيف تذكيراً جديداً إلى قاعدة البيانات."""
    if reminders_collection is not None:
        reminders_collection.insert_one({"text": text})
        return True
    return False

def get_all_reminders() -> list:
    """يجلب كل التذكيرات المحفوظة."""
    if reminders_collection is not None:
        return list(reminders_collection.find())
    return []

def delete_reminder(reminder_id: str) -> bool:
    """يحذف تذكيراً باستخدام الـ ID الخاص به."""
    if reminders_collection is not None:
        try:
            result = reminders_collection.delete_one({"_id": ObjectId(reminder_id)})
            return result.deleted_count > 0
        except:
            return False
    return False

def get_random_reminder() -> dict | None:
    """يختار تذكيراً واحداً بشكل عشوائي."""
    if reminders_collection is not None:
        # هذه الطريقة أسرع في MongoDB لجلب عنصر عشوائي
        pipeline = [{"$sample": {"size": 1}}]
        try:
            random_docs = list(reminders_collection.aggregate(pipeline))
            if random_docs:
                return random_docs[0]
        except:
            return None
    return None
