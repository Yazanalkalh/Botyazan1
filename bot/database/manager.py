# -*- coding: utf-8 -*-

import pymongo
from bson.objectid import ObjectId
import random

from config import MONGO_URI

# --- شرح ---
# هذا الملف هو "أمين المكتبة" وهو المسؤول الوحيد عن التحدث مع قاعدة بيانات MongoDB.
# تم إصلاح خطأ "الاستيراد الدائري" الذي كان موجوداً فيه.

try:
    client = pymongo.MongoClient(MONGO_URI)
    db = client.get_database("IslamicBotDB") 
    
    # --- تعريف المجموعات (Collections) ---
    reminders_collection = db["reminders"]
    settings_collection = db["settings"] 

    print("تم الاتصال بقاعدة بيانات MongoDB بنجاح.")
except pymongo.errors.ConnectionFailure as e:
    print(f"فشل الاتصال بقاعدة بيانات MongoDB: {e}")
    db = None
except Exception as e:
    print(f"حدث خطأ غير متوقع عند الاتصال بـ MongoDB: {e}")
    db = None

# --- 1. وظائف التذكيرات (Reminders) ---

def add_reminder(text):
    """يضيف تذكيراً جديداً إلى قاعدة البيانات."""
    if db is None: return False
    try:
        reminders_collection.insert_one({"text": text})
        return True
    except Exception as e:
        print(f"خطأ في إضافة تذكير: {e}")
        return False

def get_all_reminders():
    """يجلب كل التذكيرات من قاعدة البيانات."""
    if db is None: return []
    try:
        return list(reminders_collection.find())
    except Exception as e:
        print(f"خطأ في جلب التذكيرات: {e}")
        return []

def delete_reminder(reminder_id):
    """يحذف تذكيراً محدداً باستخدام ID الخاص به."""
    if db is None: return False
    try:
        reminders_collection.delete_one({"_id": ObjectId(reminder_id)})
        return True
    except Exception as e:
        print(f"خطأ في حذف تذكير: {e}")
        return False
        
def get_random_reminder():
    """يجلب تذكيراً عشوائياً من قاعدة البيانات."""
    if db is None: return None
    try:
        all_reminders = list(reminders_collection.find())
        if all_reminders:
            return random.choice(all_reminders)
        return None
    except Exception as e:
        print(f"خطأ في جلب تذكير عشوائي: {e}")
        return None

# --- 2. وظائف الإعدادات (Settings) ---

def set_setting(setting_name, value):
    """يحفظ أو يحدّث قيمة إعداد معين في قاعدة البيانات."""
    if db is None: return False
    try:
        settings_collection.update_one(
            {"name": setting_name},
            {"$set": {"value": value}},
            upsert=True
        )
        return True
    except Exception as e:
        print(f"خطأ في حفظ الإعداد {setting_name}: {e}")
        return False

def get_setting(setting_name, default=None):
    """يجلب قيمة إعداد معين من قاعدة البيانات، أو يعيد القيمة الافتراضية."""
    if db is None: return default
    try:
        setting = settings_collection.find_one({"name": setting_name})
        if setting:
            return setting.get("value")
        return default
    except Exception as e:
        print(f"خطأ في جلب الإعداد {setting_name}: {e}")
        return default
