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
PRODUCT, PRICE, NOTES = range(3)

# رسالة الترحيب
WELCOME_MESSAGE = (
    "مرحباً! يمكنك إرسال:\n\n"
    "1️⃣ منتج واحد مع سعره مثل:\n"
    "كولا ٢٣\n\n"
    "2️⃣ أو قائمة منتجات، كل منتج في سطر مثل:\n"
    "كولا ٢٣\n"
    "شيبس ١٩.٥\n"
    "قهوة ٢٦.٥\n\n"
    "3️⃣ أو اسم منتج فقط وسأطلب منك السعر"
)
