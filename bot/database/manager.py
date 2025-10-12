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

    # ... (بقية وظائف قاعدة البيانات بنفس الطريقة) ...

db = DatabaseManager()
