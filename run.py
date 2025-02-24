"""
نقطة بداية تشغيل البوت

هذا الملف هو نقطة البداية لتشغيل البوت. يقوم بما يلي:
1. إضافة المجلد الرئيسي إلى مسار البحث عن الوحدات
2. استيراد وتشغيل الدالة الرئيسية من src.main
"""
import os
import sys
import logging
import traceback
import tempfile
import atexit
from pathlib import Path
from datetime import datetime

print("=== بدء تشغيل البوت ===")

# إنشاء مجلد للسجلات إذا لم يكن موجوداً
logs_dir = Path(__file__).parent / 'logs'
print(f"مجلد السجلات: {logs_dir}")
logs_dir.mkdir(exist_ok=True)
print("تم إنشاء مجلد السجلات")

# إعداد التسجيل
log_file = logs_dir / f"bot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)
logger.info("=== بدء تشغيل البوت ===")

def setup_python_path() -> None:
    """
    إضافة المجلد الرئيسي إلى مسار البحث عن الوحدات
    لضمان استيراد الوحدات بشكل صحيح
    """
    try:
        logger.info("جاري إعداد مسار البحث...")
        root_dir = Path(__file__).parent.resolve()
        if str(root_dir) not in sys.path:
            sys.path.append(str(root_dir))
            logger.info(f"تمت إضافة {root_dir} إلى مسار البحث")
    except Exception as e:
        logger.error(f"خطأ في إعداد مسار البحث: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(1)

def check_credentials() -> None:
    """
    التحقق من وجود ملفات الاعتماد المطلوبة
    """
    try:
        logger.info("جاري التحقق من ملفات الاعتماد...")
        
        # التحقق من وجود ملف .env
        env_file = Path(__file__).parent / '.env'
        logger.info(f"ملف .env: {env_file} ({'موجود' if env_file.exists() else 'غير موجود'})")
        if not env_file.exists():
            raise FileNotFoundError("ملف .env غير موجود")
        
        # التحقق من وجود ملف credentials.json
        creds_file = Path(__file__).parent / 'credentials.json'
        logger.info(f"ملف credentials.json: {creds_file} ({'موجود' if creds_file.exists() else 'غير موجود'})")
        if not creds_file.exists():
            raise FileNotFoundError("ملف credentials.json غير موجود")
            
        logger.info("تم التحقق من وجود ملفات الاعتماد بنجاح")
    except Exception as e:
        logger.error(f"خطأ في التحقق من ملفات الاعتماد: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(1)

def is_bot_running():
    """التحقق مما إذا كان البوت يعمل بالفعل"""
    pid_file = os.path.join(tempfile.gettempdir(), "telegram_sheets_bot.pid")
    
    if os.path.exists(pid_file):
        with open(pid_file, 'r') as f:
            old_pid = int(f.read().strip())
            try:
                # التحقق مما إذا كانت العملية ما زالت موجودة
                os.kill(old_pid, 0)
                return True
            except OSError:
                # العملية لم تعد موجودة
                pass
    
    # كتابة PID الحالي
    with open(pid_file, 'w') as f:
        f.write(str(os.getpid()))
    
    # تسجيل دالة لحذف ملف PID عند إغلاق البوت
    atexit.register(lambda: os.remove(pid_file) if os.path.exists(pid_file) else None)
    return False

def main() -> None:
    """
    الدالة الرئيسية لبدء تشغيل البوت
    """
    if is_bot_running():
        logger.error("هناك نسخة أخرى من البوت قيد التشغيل!")
        sys.exit(1)
        
    try:
        logger.info("\n=== تشغيل البوت ===")
        
        # إعداد مسار البحث
        setup_python_path()
        
        # التحقق من ملفات الاعتماد
        check_credentials()
        
        # استيراد الوحدات
        logger.info("جاري استيراد الوحدات...")
        from src.main import main as bot_main
        logger.info("تم استيراد الوحدات بنجاح")
        
        # تشغيل البوت
        logger.info("جاري تشغيل البوت...")
        bot_main()
        
    except ImportError as e:
        logger.error(f"خطأ في استيراد الوحدات: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(1)
    except Exception as e:
        logger.error(f"خطأ غير متوقع: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == '__main__':
    main()
