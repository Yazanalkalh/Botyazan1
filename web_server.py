# -*- coding: utf-8 -*-

import os
from flask import Flask

# --- إعداد خادم الويب Flask ---
app = Flask(__name__)

@app.route('/')
def home():
    """صفحة بسيطة لإبقاء الخدمة نشطة."""
    return "Bot server is running and healthy."

def run_flask():
    """
    تشغيل خادم فلاسك.
    Render توفر متغير PORT تلقائياً. القيمة 8080 هي للاختبار المحلي.
    """
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
