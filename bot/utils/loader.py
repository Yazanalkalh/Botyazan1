# -*- coding: utf-8 -*-

import pkgutil
import importlib
import logging
from aiogram import Dispatcher

HANDLERS_PATH = "bot.handlers"

def discover_handlers():
    """
    يكتشف كل وحدات المعالجات ويعيدها كقائمة لتسجيلها لاحقاً بالترتيب الصحيح.
    """
    logging.info("🔎 اكتشاف جميع وحدات المعالجات...")
    modules = []
    try:
        handlers_module = importlib.import_module(HANDLERS_PATH)
        for _, module_name, _ in pkgutil.walk_packages(
            path=handlers_module.__path__,
            prefix=handlers_module.__name__ + "."
        ):
            try:
                module = importlib.import_module(module_name)
                modules.append(module)
            except Exception as e:
                logging.error(f"⚠️ فشل تحميل الوحدة {module_name}: {e}")
    except ModuleNotFoundError:
        logging.error(f"❌ لم يتم العثور على مجلد المعالجات: {HANDLERS_PATH}")
    
    logging.info(f"💡 تم اكتشاف {len(modules)} وحدة معالج.")
    return modules
