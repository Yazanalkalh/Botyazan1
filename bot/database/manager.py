# -*- coding: utf-8 -*-

import os
import random
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure

class DatabaseManager:
    def __init__(self):
        self.client = None
        self.db = None
        # مجموعات البيانات (Collections)
        self.reminders_collection = None
        self.settings_collection = None
        self.approved_channels_collection = None
        self.subscription_channels_collection = None
        self.texts_collection = None
        self.users_collection = None

    async def connect_to_database(self, uri: str):
        """الاتصال بقاعدة بيانات MongoDB."""
        try:
            self.client = AsyncIOMotorClient(uri)
            # اسم قاعدة البيانات سيكون "TelegramBotDB"
            self.db = self.client["TelegramBotDB"]
            
            # تهيئة مجموعات البيانات
            self.reminders_collection = self.db["reminders"]
            self.settings_collection = self.db["settings"]
            self.approved_channels_collection = self.db["approved_channels"]
            self.subscription_channels_collection = self.db["subscription_channels"]
            self.texts_collection = self.db["texts"]
            self.users_collection = self.db["users"] # <-- تهيئة مجموعة المستخدمين
            
            print("تم الاتصال بقاعدة بيانات MongoDB بنجاح.")
            return True
        except ConnectionFailure as e:
            print(f"لا يمكن الاتصال بقاعدة بيانات MongoDB: {e}")
            return False

    async def close_database_connection(self):
        """إغلاق الاتصال بقاعدة البيانات."""
        if self.client:
            self.client.close()
            print("تم إغلاق الاتصال بقاعدة البيانات.")

    # --- وظيفة إضافة/تحديث المستخدم (الوظيفة المفقودة) ---
    async def add_user(self, user_id: int, first_name: str, username: str):
        """إضافة مستخدم جديد أو تحديث بياناته إذا كان موجوداً."""
        if self.users_collection is not None:
            user_data = {
                'user_id': user_id,
                'first_name': first_name,
                'username': username,
                'last_update_date': datetime.utcnow()
            }
            # upsert=True تعني: إذا لم تجد المستخدم، قم بإضافته. إذا وجدته، قم بتحديث بياناته.
            await self.users_collection.update_one(
                {'user_id': user_id},
                {'$set': user_data},
                upsert=True
            )

    # --- وظائف التذكيرات ---
    async def add_reminder(self, text: str) -> bool:
        if self.reminders_collection is not None:
            await self.reminders_collection.insert_one({'text': text})
            return True
        return False

    async def get_all_reminders(self):
        if self.reminders_collection is not None:
            return await self.reminders_collection.find({}, {'_id': 1, 'text': 1}).to_list(length=None)
        return []

    async def delete_reminder(self, reminder_id) -> bool:
        if self.reminders_collection is not None:
            result = await self.reminders_collection.delete_one({'_id': reminder_id})
            return result.deleted_count > 0
        return False
        
    async def get_random_reminder(self):
        if self.reminders_collection is not None:
            reminders = await self.reminders_collection.find({}, {'text': 1}).to_list(length=None)
            if reminders:
                return random.choice(reminders)['text']
        return None

    async def get_reminders_count(self) -> int:
        if self.reminders_collection is not None:
            return await self.reminders_collection.count_documents({})
        return 0

    async def get_reminders_page(self, page: int, page_size: int):
        if self.reminders_collection is not None:
            skip = (page - 1) * page_size
            return await self.reminders_collection.find({}, {'_id': 1, 'text': 1}).skip(skip).limit(page_size).to_list(length=page_size)
        return []

    # --- وظائف الإعدادات (المنطقة الزمنية) ---
    async def set_timezone(self, timezone: str):
        if self.settings_collection is not None:
            await self.settings_collection.update_one(
                {'_id': 'bot_settings'},
                {'$set': {'timezone': timezone}},
                upsert=True
            )

    async def get_timezone(self) -> str:
        if self.settings_collection is not None:
            settings = await self.settings_collection.find_one({'_id': 'bot_settings'})
            return settings.get('timezone', 'Asia/Riyadh') if settings else 'Asia/Riyadh'

    # --- وظائف القنوات المعتمدة ---
    async def add_approved_channel(self, channel_id: int, channel_title: str):
        if self.approved_channels_collection is not None:
            await self.approved_channels_collection.update_one(
                {'channel_id': channel_id},
                {'$set': {'title': channel_title}},
                upsert=True
            )

    async def is_channel_approved(self, channel_id: int) -> bool:
        if self.approved_channels_collection is not None:
            channel = await self.approved_channels_collection.find_one({'channel_id': channel_id})
            return channel is not None
        return False

    # --- وظائف الاشتراك الإجباري ---
    async def add_subscription_channel(self, channel_id: int, channel_title: str):
        if self.subscription_channels_collection is not None:
            await self.subscription_channels_collection.update_one(
                {'channel_id': channel_id},
                {'$set': {'title': channel_title}},
                upsert=True
            )

    async def get_subscription_channels(self):
        if self.subscription_channels_collection is not None:
            return await self.subscription_channels_collection.find({}, {'channel_id': 1, 'title': 1}).to_list(length=None)
        return []

    async def delete_subscription_channel(self, channel_id) -> bool:
        if self.subscription_channels_collection is not None:
            result = await self.subscription_channels_collection.delete_one({'_id': channel_id})
            return result.deleted_count > 0
        return False

    async def get_subscription_channels_count(self) -> int:
        if self.subscription_channels_collection is not None:
            return await self.subscription_channels_collection.count_documents({})
        return 0

    async def get_subscription_channels_page(self, page: int, page_size: int):
        if self.subscription_channels_collection is not None:
            skip = (page - 1) * page_size
            return await self.subscription_channels_collection.find({}, {'_id': 1, 'title': 1, 'channel_id': 1}).skip(skip).limit(page_size).to_list(length=page_size)
        return []

    # --- وظائف النصوص ---
    async def get_text(self, key: str, default: str = "") -> str:
        if self.texts_collection is not None:
            text_doc = await self.texts_collection.find_one({'_id': key})
            return text_doc.get('value', default) if text_doc else default
        return default

    async def set_text(self, key: str, value: str):
        if self.texts_collection is not None:
            await self.texts_collection.update_one(
                {'_id': key},
                {'$set': {'value': value}},
                upsert=True
            )

# إنشاء نسخة واحدة من مدير قاعدة البيانات لاستخدامها في كل المشروع
db = DatabaseManager()
