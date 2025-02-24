"""
معالجات الأوامر
"""
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from src.config import WELCOME_MESSAGE as welcome_message
from database.sheets import add_to_sheets

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالج أمر /start"""
    await update.message.reply_text(welcome_message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالج أمر /help"""
    await update.message.reply_text(welcome_message)

async def skip_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """معالج أمر /skip لتخطي الملاحظات"""
    if 'product' in context.user_data and 'price' in context.user_data:
        product = context.user_data['product']
        price = context.user_data['price']
        add_to_sheets(product, price)
        await update.message.reply_text(f"تم إضافة {product} بسعر {price} بنجاح!")
        await update.message.reply_text(welcome_message)
        return ConversationHandler.END
    else:
        await update.message.reply_text("لا يمكن استخدام هذا الأمر الآن")
        return ConversationHandler.END
