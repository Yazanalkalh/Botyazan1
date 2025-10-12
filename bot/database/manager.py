# -*- coding: utf-8 -*-

import motor.motor_asyncio
from pymongo.errors import ConnectionFailure

class DatabaseManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        self.client = None
        self.db = None
        # سيتم تهيئة المجموعات بعد الاتصال
        self.users_collection = None
        self.approved_channels_collection = None
        self.reminders_collection = None
        self.settings_collection = None
        self.subscription_channels_collection = None
        self.texts_collection = None

    async def connect_to_database(self, uri: str):
        try:
            self.client = motor.motor_asyncio.AsyncIOMotorClient(uri)
            await self.client.admin.command('ping')
            self.db = self.client.IslamicBotDB
            # تهيئة المجموعات
            self.users_collection = self.db.users
            self.approved_channels_collection = self.db.approved_channels
            self.reminders_collection = self.db.reminders
            self.settings_collection = self.db.settings
            self.subscription_channels_collection = self.db.subscription_channels
            self.texts_collection = self.db.texts
            print("تم الاتصال بقاعدة بيانات MongoDB بنجاح.")
        except ConnectionFailure as e:
            print(f"لا يمكن تشغيل البوت بسبب فشل الاتصال بقاعدة البيانات: {e}")
            self.client = None
        except Exception as e:
            print(f"حدث خطأ غير متوقع عند الاتصال بقاعدة البيانات: {e}")
            self.client = None

    def is_connected(self):
        return self.client is not None

    # --- وظائف المستخدمين ---
    async def add_user(self, user_id, first_name, username):
        if not self.is_connected(): return
        await self.users_collection.update_one(
            {'_id': user_id},
            {'$set': {'first_name': first_name, 'username': username}},
            upsert=True
        )

    async def get_user_info(self, user_id):
        if not self.is_connected(): return None
        return await self.users_collection.find_one({'_id': user_id})

    # --- وظائف القنوات المعتمدة ---
    async def add_approved_channel(self, channel_id: int, title: str, username: str):
        if not self.is_connected(): return
        await self.approved_channels_collection.update_one(
            {'_id': channel_id},
            {'$set': {'title': title, 'username': username}},
            upsert=True
        )

    async def is_channel_approved(self, channel_id: int) -> bool:
        if not self.is_connected(): return False
        channel = await self.approved_channels_collection.find_one({'_id': channel_id})
        return channel is not None

    # --- وظائف التذكيرات ---
    async def add_reminder(self, text: str):
        if not self.is_connected(): return
        await self.reminders_collection.insert_one({'text': text})

    async def get_reminders_count(self) -> int:
        if not self.is_connected(): return 0
        return await self.reminders_collection.count_documents({})

    async def get_reminders_page(self, page: int, page_size: int):
        if not self.is_connected(): return []
        skip = (page - 1) * page_size
        cursor = self.reminders_collection.find({}).skip(skip).limit(page_size)
        return await cursor.to_list(length=page_size)

    async def delete_reminder(self, reminder_id: str):
        from bson.objectid import ObjectId
        if not self.is_connected(): return
        await self.reminders_collection.delete_one({'_id': ObjectId(reminder_id)})

    async def get_random_reminder(self):
        if not self.is_connected(): return None
        pipeline = [{'$sample': {'size': 1}}]
        async for doc in self.reminders_collection.aggregate(pipeline):
            return doc

    # --- وظائف الإعدادات ---
    async def get_timezone(self) -> str:
        if not self.is_connected(): return "Asia/Riyadh"
        setting = await self.settings_collection.find_one({'_id': 'bot_settings'})
        return setting.get('timezone', "Asia/Riyadh") if setting else "Asia/Riyadh"

    async def set_timezone(self, timezone: str):
        if not self.is_connected(): return
        await self.settings_collection.update_one(
            {'_id': 'bot_settings'},
            {'$set': {'timezone': timezone}},
            upsert=True
        )

    # --- وظائف الاشتراك الإجباري ---
    async def add_subscription_channel(self, channel_id: str, title: str):
        if not self.is_connected(): return
        await self.subscription_channels_collection.update_one(
            {'_id': channel_id},
            {'$set': {'title': title}},
            upsert=True
        )

    async def get_subscription_channels(self):
        if not self.is_connected(): return []
        cursor = self.subscription_channels_collection.find({})
        return await cursor.to_list(length=None)

    async def get_subscription_channels_count(self) -> int:
        if not self.is_connected(): return 0
        return await self.subscription_channels_collection.count_documents({})
    
    async def get_subscription_channels_page(self, page: int, page_size: int):
        if not self.is_connected(): return []
        skip = (page - 1) * page_size
        cursor = self.subscription_channels_collection.find({}).skip(skip).limit(page_size)
        return await cursor.to_list(length=page_size)

    async def delete_subscription_channel(self, channel_id: str):
        if not self.is_connected(): return
        await self.subscription_channels_collection.delete_one({'_id': channel_id})

    # --- وظائف النصوص ---
    async def get_text(self, key: str, default: str) -> str:
        if not self.is_connected(): return default
        doc = await self.texts_collection.find_one({'_id': key})
        return doc['value'] if doc else default

    async def set_text(self, key: str, value: str):
        if not self.is_connected(): return
        await self.texts_collection.update_one(
            {'_id': key},
            {'$set': {'value': value}},
            upsert=True
        )

db = DatabaseManager()
