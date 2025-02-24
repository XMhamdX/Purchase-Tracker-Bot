"""
معالجات المحادثة
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from src.config import WELCOME_MESSAGE, PRICE, NOTES
from utils.number_converter import convert_to_english_numbers
from database.sheets import add_to_sheets
import traceback

# إعداد التسجيل
logger = logging.getLogger(__name__)

async def handle_any_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    معالج أي رسالة - يتم استدعاؤه عند استلام أي رسالة من المستخدم
    يدعم ثلاث طرق لإدخال المنتجات:
    1. منتج واحد مع سعره (مثل: كولا ٢٣)
    2. قائمة منتجات مع أسعارها (كل منتج في سطر)
    3. اسم منتج فقط (سيطلب السعر لاحقاً)
    """
    try:
        message_text = update.message.text.strip()
        
        # تجاهل الرسائل الفارغة
        if not message_text:
            await update.message.reply_text("❌ الرجاء إدخال نص صحيح")
            return ConversationHandler.END
            
        # التحقق من وجود عدة منتجات (كل منتج في سطر)
        if "\n" in message_text:
            success_count = 0
            error_count = 0
            lines = message_text.split("\n")
            
            for line in lines:
                try:
                    if not line.strip():
                        continue
                        
                    # تحويل الأرقام العربية إلى إنجليزية
                    line = convert_to_english_numbers(line)
                    
                    # محاولة فصل المنتج عن السعر
                    parts = line.strip().split()
                    if len(parts) < 2:
                        error_count += 1
                        continue
                        
                    product = " ".join(parts[:-1])
                    try:
                        price = float(parts[-1])
                        if add_to_sheets(product, price, ""):
                            success_count += 1
                        else:
                            error_count += 1
                    except ValueError:
                        error_count += 1
                        continue
                        
                except Exception as e:
                    logger.error(f"خطأ في معالجة السطر {line}: {str(e)}")
                    error_count += 1
                    continue
            
            # إرسال ملخص النتائج
            summary = []
            if success_count > 0:
                summary.append(f"✅ تم إضافة {success_count} منتج بنجاح")
            if error_count > 0:
                summary.append(f"❌ فشل إضافة {error_count} منتج")
            
            await update.message.reply_text("\n".join(summary))
            await update.message.reply_text(WELCOME_MESSAGE)
            return ConversationHandler.END
            
        # محاولة فصل المنتج عن السعر
        parts = message_text.split()
        if len(parts) >= 2:
            try:
                # تحويل الأرقام العربية إلى إنجليزية
                last_part = convert_to_english_numbers(parts[-1])
                price = float(last_part)
                product = " ".join(parts[:-1])
                
                # محاولة إضافة المنتج للجدول
                if add_to_sheets(product, price, ""):
                    await update.message.reply_text(f"✅ تم إضافة {product} بسعر {price} بنجاح!")
                    await update.message.reply_text(WELCOME_MESSAGE)
                    return ConversationHandler.END
                else:
                    # إذا فشلت الإضافة، نطلب من المستخدم المحاولة مرة أخرى
                    await update.message.reply_text("❌ حدث خطأ في إضافة المنتج. الرجاء المحاولة مرة أخرى.")
                    return ConversationHandler.END
                
            except ValueError:
                # إذا لم يكن آخر جزء رقماً، نعتبر الكل اسم منتج
                pass
                
        # إذا وصلنا هنا، نعتبر النص كله اسم منتج
        context.user_data['product'] = message_text
        await update.message.reply_text("💰 أدخل سعر المنتج (رقم فقط):")
        return PRICE
        
    except Exception as e:
        logger.error(f"خطأ غير متوقع: {str(e)}")
        await update.message.reply_text("❌ حدث خطأ غير متوقع. الرجاء المحاولة مرة أخرى.")
        return ConversationHandler.END

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """معالج إدخال السعر"""
    try:
        # تحويل الأرقام العربية إلى إنجليزية قبل التحويل
        price_text = convert_to_english_numbers(update.message.text)
        price = float(price_text)
        context.user_data['price'] = price
        await update.message.reply_text(
            '📝 أدخل ملاحظات إضافية\n'
            'يمكنك تخطي الملاحظات عن طريق:\n'
            '- إرسال "." (نقطة)\n'
            '- إرسال "لا"\n'
            '- استخدام الأمر /skip'
        )
        return NOTES
    except ValueError:
        logger.warning(f"قيمة غير صحيحة للسعر: {update.message.text}")
        await update.message.reply_text(
            '❌ الرجاء إدخال رقم صحيح للسعر'
        )
        return PRICE

async def notes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """معالج إدخال الملاحظات"""
    try:
        # التحقق من وجود البيانات السابقة
        if 'product' not in context.user_data or 'price' not in context.user_data:
            logger.error("لم يتم العثور على بيانات المنتج أو السعر")
            await update.message.reply_text("❌ حدث خطأ: لم يتم العثور على بيانات المنتج. الرجاء البدء من جديد.")
            context.user_data.clear()
            return ConversationHandler.END

        notes_text = update.message.text
        product = context.user_data['product']
        price = context.user_data['price']
        
        logger.info(f"محاولة إضافة منتج: {product} بسعر {price} وملاحظات: {notes_text}")
        
        # التحقق من رغبة المستخدم في تخطي الملاحظات
        if notes_text in [".", "لا", "/skip"]:
            notes_text = ""
            logger.info(f"تم تخطي الملاحظات للمنتج: {product}")
        
        # محاولة إضافة البيانات إلى الجدول
        success = add_to_sheets(product, price, notes_text)
        if success:
            logger.info(f"تم إضافة المنتج بنجاح: {product}")
            await update.message.reply_text(
                f"✅ تم إضافة المنتج بنجاح!\n"
                f"المنتج: {product}\n"
                f"السعر: {price}\n"
                f"الملاحظات: {notes_text if notes_text else 'لا يوجد'}"
            )
        else:
            logger.error(f"فشل في إضافة المنتج: {product}")
            await update.message.reply_text("❌ حدث خطأ أثناء إضافة المنتج. الرجاء المحاولة مرة أخرى.")
            
        # مسح بيانات المستخدم
        context.user_data.clear()
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"خطأ في معالجة الملاحظات: {str(e)}")
        logger.error(traceback.format_exc())
        await update.message.reply_text("❌ عذراً، حدث خطأ أثناء معالجة طلبك. الرجاء المحاولة مرة أخرى.")
        context.user_data.clear()
        return ConversationHandler.END
