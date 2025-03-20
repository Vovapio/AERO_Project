import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from database import (
    init_db, get_or_create_user, add_result, get_leaderboard,
    Simulator, FlightMode, Map
)
from registration import get_registration_handler

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
CHOOSING_ACTION, REGISTERING_USER, CHOOSING_SIMULATOR, CHOOSING_MODE, CHOOSING_MAP, ENTERING_TIME = range(6)

def create_simulator_keyboard():
    """Создание клавиатуры с симуляторами"""
    keyboard = [
        [InlineKeyboardButton(sim.value, callback_data=f"sim_{sim.name}")]
        for sim in Simulator
    ]
    return InlineKeyboardMarkup(keyboard)

def create_mode_keyboard():
    """Создание клавиатуры с режимами полета"""
    keyboard = [
        [InlineKeyboardButton(mode.value, callback_data=f"mode_{mode.name}")]
        for mode in FlightMode
    ]
    return InlineKeyboardMarkup(keyboard)

def create_map_keyboard():
    """Создание клавиатуры с картами"""
    keyboard = [
        [InlineKeyboardButton(map.value, callback_data=f"map_{map.name}")]
        for map in Map
    ]
    return InlineKeyboardMarkup(keyboard)

def create_action_keyboard():
    """Создание клавиатуры с действиями"""
    keyboard = [
        [InlineKeyboardButton("Внести время", callback_data="action_add")],
        [InlineKeyboardButton("Leaderboard", callback_data="action_leaderboard")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    
    # Проверяем, зарегистрирован ли пользователь
    db_user = get_or_create_user(
        telegram_id=user.id,
        first_name=user.first_name,
        last_name=user.last_name or "",
        group="Default",
        birth_date=datetime.now()
    )
    
    if db_user.group == "Default":
        await update.message.reply_text(
            "Для начала работы нужно зарегистрироваться.\n"
            "Используйте команду /register"
        )
        return ConversationHandler.END
    
    await update.message.reply_text(
        "Вы хотите внести время или увидеть leaderboard?",
        reply_markup=create_action_keyboard()
    )
    return CHOOSING_ACTION

async def action_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора действия"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "action_add":
        await query.message.reply_text(
            "Выберите симулятор:",
            reply_markup=create_simulator_keyboard()
        )
        return CHOOSING_SIMULATOR
    elif query.data == "action_leaderboard":
        await query.message.reply_text(
            "Выберите симулятор для просмотра таблицы лидеров:",
            reply_markup=create_simulator_keyboard()
        )
        return CHOOSING_SIMULATOR

async def simulator_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора симулятора"""
    query = update.callback_query
    await query.answer()
    
    simulator_name = query.data.split('_')[1]
    context.user_data['simulator'] = Simulator[simulator_name]
    
    await query.message.reply_text(
        "Выберите режим полета:",
        reply_markup=create_mode_keyboard()
    )
    return CHOOSING_MODE

async def mode_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора режима полета"""
    query = update.callback_query
    await query.answer()
    
    mode_name = query.data.split('_')[1]
    context.user_data['flight_mode'] = FlightMode[mode_name]
    
    await query.message.reply_text(
        "Выберите название трассы:",
        reply_markup=create_map_keyboard()
    )
    return CHOOSING_MAP

async def map_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора карты"""
    query = update.callback_query
    await query.answer()
    
    map_name = query.data.split('_')[1]
    context.user_data['map_name'] = Map[map_name]
    
    if 'action' in context.user_data and context.user_data['action'] == 'leaderboard':
        return await show_leaderboard(update, context)
    else:
        await query.message.reply_text(
            "Введите время в формате: секунды.миллисекунды\n"
            "Пример: 38.106"
        )
        return ENTERING_TIME

async def time_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ввода времени"""
    try:
        time = float(update.message.text)
        user = update.effective_user
        
        # Получаем пользователя из базы данных
        db_user = get_or_create_user(
            telegram_id=user.id,
            first_name=user.first_name,
            last_name=user.last_name or "",
            group="Default",
            birth_date=datetime.now()
        )
        
        if db_user.group == "Default":
            await update.message.reply_text(
                "Для внесения результатов нужно зарегистрироваться.\n"
                "Используйте команду /register"
            )
            return ConversationHandler.END
        
        # Добавляем результат
        add_result(
            user_id=db_user.id,
            simulator=context.user_data['simulator'],
            flight_mode=context.user_data['flight_mode'],
            map_name=context.user_data['map_name'],
            time=time
        )
        
        await update.message.reply_text(
            "Вы отлично пролетели, поздравляю! Ваш результат записан!"
        )
    except ValueError:
        await update.message.reply_text(
            "Неверный формат времени. Пожалуйста, введите число в формате: секунды.миллисекунды\n"
            "Пример: 38.106"
        )
        return ENTERING_TIME
    
    return ConversationHandler.END

async def show_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показ таблицы лидеров"""
    query = update.callback_query
    await query.answer()
    
    leaderboard = get_leaderboard(
        simulator=context.user_data['simulator'],
        flight_mode=context.user_data['flight_mode'],
        map_name=context.user_data['map_name']
    )
    
    current_time = datetime.now().strftime("%H:%M %d.%m.%Y")
    message = (
        f"Leaderboard Аэроквантум-15 от {current_time} г.\n"
        f"{context.user_data['simulator'].value}, {context.user_data['flight_mode'].value.lower()}, "
        f"{context.user_data['map_name'].value}\n\n"
    )
    
    for i, result in enumerate(leaderboard, 1):
        message += f"{i}. {result['time']:.3f} - {result['name']}, гр. {result['group']}\n"
    
    # Дополняем пустыми местами до 10
    while len(leaderboard) < 10:
        message += f"{len(leaderboard) + 1}. (место не занято)\n"
        leaderboard.append(None)
    
    await query.message.reply_text(message)
    return ConversationHandler.END

def main():
    """Основная функция запуска бота"""
    # Инициализация базы данных
    init_db()
    
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()

    # Создаем обработчик диалога
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING_ACTION: [
                CallbackQueryHandler(action_chosen, pattern='^action_')
            ],
            CHOOSING_SIMULATOR: [
                CallbackQueryHandler(simulator_chosen, pattern='^sim_')
            ],
            CHOOSING_MODE: [
                CallbackQueryHandler(mode_chosen, pattern='^mode_')
            ],
            CHOOSING_MAP: [
                CallbackQueryHandler(map_chosen, pattern='^map_')
            ],
            ENTERING_TIME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, time_entered)
            ],
        },
        fallbacks=[CommandHandler('start', start)],
    )

    # Добавляем обработчики
    application.add_handler(conv_handler)
    application.add_handler(get_registration_handler())

    # Запускаем бота
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main() 