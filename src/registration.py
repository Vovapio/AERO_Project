from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from database import get_or_create_user

# Состояния для регистрации
LAST_NAME, FIRST_NAME, GROUP, BIRTH_DATE = range(4)

async def register_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало регистрации"""
    await update.message.reply_text(
        "Для начала работы нужно зарегистрироваться.\n"
        "Введите вашу фамилию:"
    )
    return LAST_NAME

async def last_name_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка фамилии"""
    context.user_data['last_name'] = update.message.text.strip()
    await update.message.reply_text("Введите ваше имя:")
    return FIRST_NAME

async def first_name_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка имени"""
    context.user_data['first_name'] = update.message.text.strip()
    await update.message.reply_text("Введите вашу учебную группу:")
    return GROUP

async def group_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка группы"""
    context.user_data['group'] = update.message.text.strip()
    await update.message.reply_text(
        "Введите вашу дату рождения в формате ДД.ММ.ГГГГ\n"
        "Например: 01.01.2000"
    )
    return BIRTH_DATE

async def birth_date_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка даты рождения"""
    try:
        birth_date = datetime.strptime(update.message.text.strip(), "%d.%m.%Y")
        user = update.effective_user
        
        # Создаем пользователя в базе данных
        db_user = get_or_create_user(
            telegram_id=user.id,
            first_name=context.user_data['first_name'],
            last_name=context.user_data['last_name'],
            group=context.user_data['group'],
            birth_date=birth_date
        )
        
        await update.message.reply_text(
            f"Регистрация успешно завершена!\n"
            f"ФИО: {db_user.last_name} {db_user.first_name}\n"
            f"Группа: {db_user.group}\n"
            f"Дата рождения: {db_user.birth_date.strftime('%d.%m.%Y')}"
        )
    except ValueError:
        await update.message.reply_text(
            "Неверный формат даты. Пожалуйста, введите дату в формате ДД.ММ.ГГГГ\n"
            "Например: 01.01.2000"
        )
        return BIRTH_DATE
    
    return ConversationHandler.END

def get_registration_handler():
    """Получение обработчика регистрации"""
    return ConversationHandler(
        entry_points=[CommandHandler('register', register_start)],
        states={
            LAST_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, last_name_received)],
            FIRST_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, first_name_received)],
            GROUP: [MessageHandler(filters.TEXT & ~filters.COMMAND, group_received)],
            BIRTH_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, birth_date_received)],
        },
        fallbacks=[CommandHandler('register', register_start)],
    ) 