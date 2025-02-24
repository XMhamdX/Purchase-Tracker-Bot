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
from typing import Optional
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from gspread.exceptions import SpreadsheetNotFound, WorksheetNotFound
import traceback

# إعداد التسجيل
logger = logging.getLogger(__name__)

# اسم ملف جدول البيانات
SPREADSHEET_NAME = "المشتريات"

def setup_google_sheets() -> Optional[gspread.Worksheet]:
    """
    إعداد اتصال Google Sheets
    """
    try:
        logger.info("جاري إعداد الاتصال بـ Google Sheets...")
        
        # إعداد نطاق الوصول
        scope = ['https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive']
        
        # تحميل بيانات الاعتماد
        creds_path = os.path.join(os.path.dirname(__file__), '..', 'credentials.json')
        
        if not os.path.exists(creds_path):
            logger.error(f"لم يتم العثور على ملف الاعتمادات في: {creds_path}")
            return None
            
        try:
            creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
            client = gspread.authorize(creds)
            logger.info("تم الاتصال بنجاح")
            
            try:
                # محاولة فتح الجدول
                spreadsheet = client.open(SPREADSHEET_NAME)
                worksheet = spreadsheet.sheet1
                logger.info(f"تم العثور على الجدول: {SPREADSHEET_NAME}")
                
                # التحقق من رؤوس الأعمدة
                headers = worksheet.row_values(1)
                logger.info(f"رؤوس الأعمدة الحالية: {headers}")
                
                if not headers or headers != ["التاريخ", "المنتج", "السعر", "ملاحظات"]:
                    logger.info("جاري إعادة تهيئة رؤوس الأعمدة...")
                    worksheet.clear()
                    worksheet.update('A1:D1', [["التاريخ", "المنتج", "السعر", "ملاحظات"]])
                    worksheet.format('A1:D1', {
                        "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9},
                        "horizontalAlignment": "CENTER",
                        "textFormat": {"bold": True}
                    })
                    logger.info("تم إعادة تهيئة رؤوس الأعمدة")
                
                return worksheet
                
            except SpreadsheetNotFound:
                logger.error(f"لم يتم العثور على الجدول: {SPREADSHEET_NAME}")
                return None
                
        except Exception as e:
            logger.error(f"خطأ في الاتصال: {str(e)}")
            logger.error(traceback.format_exc())
            return None
            
    except Exception as e:
        logger.error(f"خطأ في إعداد Google Sheets: {str(e)}")
        logger.error(traceback.format_exc())
        return None

def add_to_sheets(product: str, price: float, notes: str = "") -> bool:
    """
    إضافة منتج جديد إلى Google Sheets
    """
    try:
        from datetime import datetime
        
        logger.info(f"جاري إضافة المنتج: {product} بسعر {price}")
        
        # التحقق من صحة البيانات
        if not product or not isinstance(product, str):
            logger.error("اسم المنتج غير صالح")
            return False
            
        if not isinstance(price, (int, float)) or price < 0:
            logger.error("السعر غير صالح")
            return False
            
        if not isinstance(notes, str):
            notes = ""
            
        # الحصول على التاريخ الحالي
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M")
            
        # محاولة الاتصال بالجدول
        try:
            sheet = setup_google_sheets()
        except Exception as e:
            logger.error(f"خطأ في الاتصال بالجدول: {str(e)}")
            logger.error(traceback.format_exc())
            return False
            
        if not sheet:
            logger.error("فشل الاتصال بجدول البيانات")
            return False
            
        # إضافة البيانات في الأعمدة الصحيحة
        try:
            sheet.append_row([current_date, product, price, notes])
            logger.info(f"تمت إضافة {product} بنجاح")
            return True
        except Exception as e:
            logger.error(f"خطأ في إضافة البيانات إلى الجدول: {str(e)}")
            logger.error(traceback.format_exc())
            return False
            
    except Exception as e:
        logger.error(f"خطأ في إضافة البيانات: {str(e)}")
        logger.error(traceback.format_exc())
        return False
