import os
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from database import create_task, get_tasks, complete_task, delete_task, init_db

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv('config/.env')
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Состояния для ConversationHandler
TITLE, DESCRIPTION = range(2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    await update.message.reply_text(
        f"Привет, {user.first_name}! Я бот для управления задачами.\n"
        "Используйте следующие команды:\n"
        "/new - Создать новую задачу\n"
        "/list - Показать список задач\n"
        "/help - Показать справку"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    await update.message.reply_text(
        "Доступные команды:\n"
        "/start - Начать работу с ботом\n"
        "/new - Создать новую задачу\n"
        "/list - Показать список задач\n"
        "/help - Показать это сообщение"
    )

async def new_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало создания новой задачи"""
    await update.message.reply_text("Введите заголовок задачи:")
    return TITLE

async def title_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка заголовка задачи"""
    context.user_data['title'] = update.message.text
    await update.message.reply_text("Введите описание задачи (или отправьте /skip):")
    return DESCRIPTION

async def skip_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пропуск описания задачи"""
    return await save_task(update, context)

async def description_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка описания задачи"""
    context.user_data['description'] = update.message.text
    return await save_task(update, context)

async def save_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохранение задачи в базу данных"""
    user_id = update.effective_user.id
    title = context.user_data['title']
    description = context.user_data.get('description', '')
    
    task = create_task(user_id, title, description)
    await update.message.reply_text(
        f"Задача создана!\n"
        f"ID: {task.id}\n"
        f"Заголовок: {task.title}\n"
        f"Описание: {task.description or 'Нет описания'}"
    )
    return ConversationHandler.END

async def list_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать список задач"""
    user_id = update.effective_user.id
    tasks = get_tasks(user_id)
    
    if not tasks:
        await update.message.reply_text("У вас пока нет задач. Создайте новую с помощью команды /new")
        return
    
    message = "Ваши задачи:\n\n"
    for task in tasks:
        status = "✅" if task.is_completed else "⏳"
        message += f"{status} {task.title}\n"
        if task.description:
            message += f"   {task.description}\n"
        message += f"   ID: {task.id}\n\n"
    
    await update.message.reply_text(message)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на кнопки"""
    query = update.callback_query
    await query.answer()
    
    action, task_id = query.data.split(':')
    task_id = int(task_id)
    user_id = query.from_user.id
    
    if action == 'complete':
        if complete_task(task_id, user_id):
            await query.message.reply_text(f"Задача {task_id} отмечена как выполненная!")
        else:
            await query.message.reply_text("Ошибка при выполнении задачи")
    elif action == 'delete':
        if delete_task(task_id, user_id):
            await query.message.reply_text(f"Задача {task_id} удалена!")
        else:
            await query.message.reply_text("Ошибка при удалении задачи")

def main():
    """Основная функция запуска бота"""
    # Инициализация базы данных
    init_db()
    
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()

    # Создаем обработчик для создания новой задачи
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('new', new_task)],
        states={
            TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, title_received)],
            DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, description_received),
                CommandHandler('skip', skip_description)
            ],
        },
        fallbacks=[],
    )

    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("list", list_tasks))
    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(button_handler))

    # Запускаем бота
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main() 