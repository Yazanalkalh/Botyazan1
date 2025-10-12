# -*- coding: utf-8 -*-

import pkgutil
import importlib
import logging
from aiogram import Dispatcher

# المسار الأساسي لمجلد المعالجات
HANDLERS_PATH = "bot.handlers"

def auto_register_handlers(dp: Dispatcher):
    """
    يقوم بالبحث العميق (Recursive) في مجلد المعالجات وجميع مجلداته الفرعية،
    ويستدعي أي وظيفة تبدأ بـ "register_" لتسجيلها.
    """
    logging.info("🚀 بدء التحميل التلقائي لجميع المعالجات...")

    try:
        handlers_module = importlib.import_module(HANDLERS_PATH)
    except ModuleNotFoundError:
        logging.error(f"❌ لم يتم العثور على مجلد المعالجات الرئيسي: {HANDLERS_PATH}")
        return

    # --- السحر يحدث هنا: walk_packages يستعرض كل شيء ---
    # هو يدخل تلقائياً في المجلدات الفرعية مثل user و admin
    for finder, module_name, is_pkg in pkgutil.walk_packages(
        path=handlers_module.__path__,
        prefix=handlers_module.__name__ + "."
    ):
        try:
            # استيراد كل ملف يجده في طريقه
            module = importlib.import_module(module_name)
            logging.debug(f"📦 فحص الملف: {module_name}")

            # البحث عن وظائف التسجيل داخل الملف
            for attr_name in dir(module):
                if attr_name.startswith("register_"):
                    register_func = getattr(module, attr_name)
                    if callable(register_func):
                        logging.info(f"🔗 تفعيل '{attr_name}' من {module_name}")
                        register_func(dp) # تفعيل المعالج
        except Exception as e:
            logging.error(f"⚠️ فشل تحميل المعالج من {module_name}: {e}")

    logging.info("✅ اكتمل التحميل التلقائي بنجاح.")
