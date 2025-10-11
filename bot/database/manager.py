# -*- coding: utf-8 -*-

import pymongo
from bson.objectid import ObjectId
import random

from config import MONGO_URI

try:
    client = pymongo.MongoClient(MONGO_URI)
    db = client.get_database("IslamicBotDB")
    
    reminders_collection = db["reminders"]
    settings_collection = db["settings"]
    subscription_channels_collection = db["subscription_channels"]
    approved_channels_collection = db["approved_channels"]
    users_collection = db["users"] # مجموعة جديدة للمستخدمين

    print("تم الاتصال بقاعدة بيانات MongoDB بنجاح.")
except Exception as e:
    print(f"حدث خطأ فادح عند الاتصال بـ MongoDB: {e}")
    db = None

# --- وظيفة جديدة: إدارة المستخدمين ---
def add_or_update_user(user_id, first_name, last_name, username):
    """يضيف مستخدماً جديداً أو يحدث بياناته إذا كان موجوداً."""
    if db is None: return
    users_collection.update_one(
        {"user_id": user_id},
        {"$set": {
            "first_name": first_name,
            "last_name": last_name,
            "username": username
        }},
        upsert=True
    )

# --- (بقية الوظائف تبقى كما هي بدون تغيير) ---
# ... (وظائف التذكيرات، الإعدادات، الاشتراك، القنوات المعتمدة)
def add_reminder(text):
    if db is None: return False
    reminders_collection.insert_one({"text": text})
    return True
def get_all_reminders():
    if db is None: return []
    return list(reminders_collection.find())
def delete_reminder(reminder_id):
    if db is None: return False
    reminders_collection.delete_one({"_id": ObjectId(reminder_id)})
    return True
def get_random_reminder():
    if db is None: return None
    all_reminders = list(reminders_collection.find())
    return random.choice(all_reminders) if all_reminders else None
def set_setting(setting_name, value):
    if db is None: return False
    settings_collection.update_one({"name": setting_name}, {"$set": {"value": value}}, upsert=True)
    return True
def get_setting(setting_name, default=None):
    if db is None: return default
    setting = settings_collection.find_one({"name": setting_name})
    return setting.get("value") if setting else default
def add_subscription_channel(channel_username):
    if db is None: return False
    if subscription_channels_collection.find_one({"username": channel_username}): return False
    subscription_channels_collection.insert_one({"username": channel_username})
    return True
def get_all_subscription_channels():
    if db is None: return []
    return list(subscription_channels_collection.find())
def delete_subscription_channel(channel_id):
    if db is None: return False
    subscription_channels_collection.delete_one({"_id": ObjectId(channel_id)})
    return True
def add_approved_channel(chat_id, chat_title):
    if db is None: return False
    if approved_channels_collection.find_one({"chat_id": chat_id}): return False
    approved_channels_collection.insert_one({"chat_id": chat_id, "title": chat_title})
    return True
def get_all_approved_channels():
    if db is None: return []
    return list(approved_channels_collection.find())
def delete_approved_channel(channel_db_id):
    if db is None: return False
    approved_channels_collection.delete_one({"_id": ObjectId(channel_db_id)})
    return True
def is_channel_approved(chat_id):
    if db is None: return False
    return approved_channels_collection.find_one({"chat_id": chat_id}) is not None
