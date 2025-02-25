"""
ملف الإعدادات والمتغيرات الثابتة
"""
import os
from typing import Final
from dotenv import load_dotenv

# تحميل المتغيرات البيئية
load_dotenv()

# توكن البوت
TOKEN: Final = os.getenv('TELEGRAM_TOKEN')

# حالات المحادثة
PRICE = 1
NOTES = 2

# رسالة الترحيب
WELCOME_MESSAGE = """مرحباً! يمكنك إرسال:

1️⃣ منتج واحد مع سعره مثل:
كولا ٢٣

2️⃣ أو قائمة منتجات، كل منتج في سطر مثل:
كولا ٢٣
شيبس ١٩.٥
قهوة ٢٦.٥

3️⃣ أو اسم منتج فقط وسأطلب منك السعر"""
