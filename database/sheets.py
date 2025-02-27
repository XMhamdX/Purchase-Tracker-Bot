"""
التعامل مع قاعدة البيانات (Google Sheets)

هذا الملف يحتوي على الدوال المسؤولة عن التعامل مع Google Sheets.
يستخدم مكتبة gspread للاتصال بـ Google Sheets API.

المتطلبات:
    - ملف credentials.json يحتوي على بيانات اعتماد Google Sheets API
    - ورقة عمل باسم "المشتريات" في Google Sheets
"""
import os
import logging
from typing import Optional, Tuple
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from gspread.exceptions import SpreadsheetNotFound, WorksheetNotFound
import traceback
from functools import lru_cache
from datetime import datetime, timedelta

# إعداد التسجيل
logger = logging.getLogger(__name__)

# اسم ملف جدول البيانات
SPREADSHEET_NAME = "المشتريات"

# حدود السعر
MIN_PRICE = 0.01
MAX_PRICE = 1000000

class SheetsError(Exception):
    """فئة مخصصة للأخطاء المتعلقة بـ Google Sheets"""
    pass

@lru_cache(maxsize=1)
def get_google_sheets_client() -> Tuple[gspread.Client, datetime]:
    """
    الحصول على عميل Google Sheets مع تخزين مؤقت
    """
    scope = ['https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive']
    
    creds_path = os.path.join(os.path.dirname(__file__), '..', 'credentials.json')
    
    if not os.path.exists(creds_path):
        raise SheetsError("ملف الاعتمادات غير موجود")
        
    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
    client = gspread.authorize(creds)
    return client, datetime.now()

def get_worksheet() -> gspread.Worksheet:
    """
    الحصول على ورقة العمل مع التعامل مع الأخطاء
    """
    try:
        client, created_time = get_google_sheets_client()
        
        # إعادة إنشاء العميل إذا مر أكثر من 30 دقيقة
        if datetime.now() - created_time > timedelta(minutes=30):
            get_google_sheets_client.cache_clear()
            client, _ = get_google_sheets_client()
        
        try:
            spreadsheet = client.open(SPREADSHEET_NAME)
            worksheet = spreadsheet.sheet1
            
            # التحقق من رؤوس الأعمدة
            headers = worksheet.row_values(1)
            if not headers or headers != ["التاريخ", "المنتج", "السعر", "ملاحظات"]:
                worksheet.clear()
                worksheet.update('A1:D1', [["التاريخ", "المنتج", "السعر", "ملاحظات"]])
                worksheet.format('A1:D1', {
                    "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9},
                    "horizontalAlignment": "CENTER",
                    "textFormat": {"bold": True}
                })
            
            return worksheet
            
        except SpreadsheetNotFound:
            raise SheetsError(f"جدول البيانات '{SPREADSHEET_NAME}' غير موجود")
            
    except Exception as e:
        logger.error(f"خطأ في الاتصال بـ Google Sheets: {str(e)}")
        logger.error(traceback.format_exc())
        raise SheetsError("حدث خطأ في الاتصال بخدمة Google Sheets")

def validate_product_data(product: str, price: float) -> None:
    """
    التحقق من صحة بيانات المنتج
    """
    if not product or not product.strip():
        raise ValueError("اسم المنتج لا يمكن أن يكون فارغاً")
        
    if not isinstance(price, (int, float)):
        raise ValueError("السعر يجب أن يكون رقماً")
        
    if price < MIN_PRICE or price > MAX_PRICE:
        raise ValueError(f"السعر يجب أن يكون بين {MIN_PRICE} و {MAX_PRICE}")

def format_date(dt: datetime) -> str:
    """
    تنسيق التاريخ بالشكل المطلوب YYYY/MM/DD
    """
    return dt.strftime("%Y/%m/%d")

async def add_to_sheets(product: str, price: float, notes: str = "") -> bool:
    """
    إضافة منتج جديد إلى Google Sheets
    
    المعطيات:
        product (str): اسم المنتج
        price (float): سعر المنتج
        notes (str): ملاحظات إضافية (اختياري)
        
    تعيد:
        bool: True إذا تمت الإضافة بنجاح، False إذا فشلت
    """
    try:
        # تنظيف المدخلات
        product = product.strip()
        notes = notes.strip()
        
        # التحقق من صحة البيانات
        validate_product_data(product, price)
        
        # الحصول على ورقة العمل
        worksheet = get_worksheet()
        
        # إضافة البيانات
        date = format_date(datetime.now())
        worksheet.append_row([date, product, price, notes])
        logger.info(f"تمت إضافة المنتج: {product} بسعر {price}")
        return True
        
    except ValueError as e:
        logger.error(f"خطأ في البيانات: {str(e)}")
        raise
        
    except SheetsError as e:
        logger.error(str(e))
        raise
        
    except Exception as e:
        logger.error(f"خطأ غير متوقع: {str(e)}")
        logger.error(traceback.format_exc())
        raise SheetsError("حدث خطأ غير متوقع")

async def add_multiple_to_sheets(products: list) -> Tuple[int, list]:
    """
    إضافة عدة منتجات دفعة واحدة
    
    المعطيات:
        products: قائمة من الأزواج (المنتج، السعر، الملاحظات)
        
    تعيد:
        عدد المنتجات التي تمت إضافتها بنجاح وقائمة بالأخطاء
    """
    worksheet = get_worksheet()
    success_count = 0
    errors = []
    
    rows_to_add = []
    date = format_date(datetime.now())
    
    for product, price, notes in products:
        try:
            product = product.strip()
            notes = notes.strip() if notes else ""
            validate_product_data(product, price)
            rows_to_add.append([date, product, price, notes])
            success_count += 1
        except ValueError as e:
            errors.append(f"خطأ في المنتج {product}: {str(e)}")
    
    if rows_to_add:
        worksheet.append_rows(rows_to_add)
    
    return success_count, errors

async def get_products(limit: int = 10) -> list:
    """
    الحصول على آخر المنتجات المضافة
    
    المعطيات:
        limit (int): عدد المنتجات التي يجب إرجاعها (افتراضي: 10)
        
    تعيد:
        قائمة بالمنتجات
    """
    try:
        worksheet = get_worksheet()
        
        # الحصول على جميع القيم
        values = worksheet.get_all_values()
        
        # تحويل القيم إلى قائمة من القواميس
        products = []
        # تخطي الصف الأول (العناوين)
        for row in values[-limit:]:
            try:
                products.append({
                    'date': row[0],
                    'name': row[1],
                    'price': float(row[2]),
                    'notes': row[3] if len(row) > 3 else ''
                })
            except (IndexError, ValueError) as e:
                logger.warning(f"خطأ في تحويل الصف {row}: {str(e)}")
                continue
            
        return products
        
    except Exception as e:
        logger.error(f"خطأ في الحصول على المنتجات: {str(e)}")
        return []
