# -*- coding: utf-8 -*-

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from config import MONGO_URI
from bson.objectid import ObjectId

# --- شرح ---
# هذا هو "أمين المكتبة" المركزي. أي جزء من الكود يريد التحدث مع قاعدة البيانات
# يجب أن يتحدث مع هذا الملف. يحتوي على كل الوظائف اللازمة لإدارة بيانات البوت.

db_connection = None
try:
    client = MongoClient(MONGO_URI)
    client.admin.command('ping') # التحقق من الاتصال
    db_connection = client.get_database("IslamicBotDB")
    print("تم الاتصال بقاعدة بيانات MongoDB بنجاح.")
except ConnectionFailure as e:
    print(f"فشل الاتصال بقاعدة البيانات: {e}")
except Exception as e:
    print(f"حدث خطأ غير متوقع عند الاتصال بـ MongoDB: {e}")

# --- مجموعات البيانات (Collections) ---
# هنا التصحيح: نتحقق باستخدام 'is not None'
if db_connection is not None:
    users_collection = db_connection["users"]
    reminders_collection = db_connection["reminders"]
    approved_channels_collection = db_connection["approved_channels"]
    subscription_channels_collection = db_connection["subscription_channels"]
    settings_collection = db_connection["settings"]
    texts_collection = db_connection["texts"]
else:
    # إذا فشل الاتصال، كل المجموعات ستكون None
    users_collection = reminders_collection = approved_channels_collection = None
    subscription_channels_collection = settings_collection = texts_collection = None

# --- وظائف إدارة المستخدمين ---
async def add_user(user_id, full_name, username):
    """إضافة أو تحديث مستخدم في قاعدة البيانات."""
    if users_collection is None: return
    user_data = {
        "full_name": full_name,
        "username": username
    }
    users_collection.update_one({"_id": user_id}, {"$set": user_data}, upsert=True)

# --- وظائف إدارة التذكيرات ---
async def add_reminder(text):
    if reminders_collection is None: return
    reminders_collection.insert_one({"text": text})

async def get_all_reminders():
    if reminders_collection is None: return []
    return list(reminders_collection.find({}, {"_id": 1, "text": 1}))

async def delete_reminder(reminder_id):
    if reminders_collection is None: return
    reminders_collection.delete_one({"_id": ObjectId(reminder_id)})

async def get_random_reminder():
    if reminders_collection is None: return None
    pipeline = [{"$sample": {"size": 1}}]
    random_reminders = list(reminders_collection.aggregate(pipeline))
    return random_reminders[0] if random_reminders else None

# --- وظائف إدارة الإعدادات (المنطقة الزمنية) ---
async def set_timezone(timezone_str):
    if settings_collection is None: return
    settings_collection.update_one({"_id": "bot_settings"}, {"$set": {"timezone": timezone_str}}, upsert=True)

async def get_timezone():
    if settings_collection is None: return "Asia/Riyadh"
    settings = settings_collection.find_one({"_id": "bot_settings"})
    return settings.get("timezone", "Asia/Riyadh") if settings else "Asia/Riyadh"

# --- وظائف إدارة النصوص المخصصة ---
async def set_text(text_id, new_text):
    if texts_collection is None: return
    texts_collection.update_one({"_id": text_id}, {"$set": {"text": new_text}}, upsert=True)

async def get_text(text_id, default_text=""):
    if texts_collection is None: return default_text
    text_doc = texts_collection.find_one({"_id": text_id})
    return text_doc.get("text", default_text) if text_doc else default_text

# --- وظائف إدارة قنوات النشر (المعتمدة) ---
async def add_approved_channel(channel_id, title):
    if approved_channels_collection is None: return
    approved_channels_collection.update_one({"_id": channel_id}, {"$set": {"title": title}}, upsert=True)

async def is_channel_approved(channel_id):
    if approved_channels_collection is None: return False
    return approved_channels_collection.count_documents({"_id": channel_id}) > 0

# --- وظائف إدارة قنوات الاشتراك الإجباري ---
async def add_subscription_channel(channel_id, title, link):
    if subscription_channels_collection is None: return
    subscription_channels_collection.update_one({"_id": channel_id}, {"$set": {"title": title, "link": link}}, upsert=True)

async def get_subscription_channels():
    if subscription_channels_collection is None: return []
    return list(subscription_channels_collection.find({}, {"_id": 1, "title": 1, "link": 1}))

async def delete_subscription_channel(channel_id):
    if subscription_channels_collection is None: return
    subscription_channels_collection.delete_one({"_id": channel_id})
