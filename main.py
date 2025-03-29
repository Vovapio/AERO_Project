# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

import logging
import sqlite3
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# Включаем логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Состояния для регистрации
LASTNAME, FIRSTNAME, GROUP, BIRTHDATE = range(4)
# Состояния для регистрации результата
SIMULATOR, TRACK, MODE, BEST_TIME = range(4, 8)
# Состояния для просмотра таблицы лидеров
LEADERBOARD_SIMULATOR, LEADERBOARD_MODE, LEADERBOARD_TRACK = range(8, 11)

def init_db():
    """Инициализация базы данных"""
    conn = sqlite3.connect('fpv_leaderboard.db')
    c = conn.cursor()
    
    # Таблица пользователей
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY,
                  lastname TEXT,
                  firstname TEXT,
                  group_name TEXT,
                  birthdate TEXT)''')
    
    # Таблица результатов полетов
    c.execute('''CREATE TABLE IF NOT EXISTS flight_results
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  simulator TEXT,
                  track TEXT,
                  mode TEXT,
                  best_time REAL,
                  date TEXT,
                  FOREIGN KEY (user_id) REFERENCES users (user_id))''')
    
    conn.commit()
    conn.close()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    keyboard = [
        ['Регистрация результата'],
        ['Таблица лидеров']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        'Привет! 👋\n\n'
        'Я бот для системы FPV Simulators Leaderboard.\n'
        'Выберите действие:',
        reply_markup=reply_markup
    )

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показ главного меню"""
    keyboard = [
        ['Регистрация результата'],
        ['Таблица лидеров']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        'Выберите действие:',
        reply_markup=reply_markup
    )

async def register_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало процесса регистрации"""
    await update.message.reply_text(
        'Давайте начнем регистрацию!\n'
        'Пожалуйста, введите вашу фамилию:',
        reply_markup=ReplyKeyboardRemove()
    )
    return LASTNAME

async def lastname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка фамилии"""
    context.user_data['lastname'] = update.message.text
    await update.message.reply_text('Отлично! Теперь введите ваше имя:')
    return FIRSTNAME

async def firstname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка имени"""
    context.user_data['firstname'] = update.message.text
    await update.message.reply_text('Введите вашу учебную группу:')
    return GROUP

async def group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка учебной группы"""
    context.user_data['group'] = update.message.text
    await update.message.reply_text('Введите вашу дату рождения в формате ДД.ММ.ГГГГ:')
    return BIRTHDATE

async def birthdate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка даты рождения и сохранение в БД"""
    try:
        # Проверка формата даты
        datetime.strptime(update.message.text, '%d.%m.%Y')
        context.user_data['birthdate'] = update.message.text
        
        # Сохранение в базу данных
        conn = sqlite3.connect('fpv_leaderboard.db')
        c = conn.cursor()
        c.execute('''INSERT OR REPLACE INTO users 
                     (user_id, lastname, firstname, group_name, birthdate)
                     VALUES (?, ?, ?, ?, ?)''',
                  (update.effective_user.id,
                   context.user_data['lastname'],
                   context.user_data['firstname'],
                   context.user_data['group'],
                   context.user_data['birthdate']))
        conn.commit()
        conn.close()
        
        await show_main_menu(update, context)
        
        await update.message.reply_text(
            'Регистрация успешно завершена! ✅\n\n'
            f'Фамилия: {context.user_data["lastname"]}\n'
            f'Имя: {context.user_data["firstname"]}\n'
            f'Группа: {context.user_data["group"]}\n'
            f'Дата рождения: {context.user_data["birthdate"]}'
        )
    except ValueError:
        await update.message.reply_text(
            'Неверный формат даты. Пожалуйста, введите дату в формате ДД.ММ.ГГГГ:'
        )
        return BIRTHDATE
    
    return ConversationHandler.END

async def register_result_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало регистрации результата полета"""
    keyboard = [
        ['FPV Freerider'],
        ['DCL The Game'],
        ['Liftoff']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        'Выберите симулятор:',
        reply_markup=reply_markup
    )
    return SIMULATOR

async def simulator(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора симулятора"""
    context.user_data['simulator'] = update.message.text
    
    keyboard = [
        ['map1'],
        ['map2']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        'Выберите трассу:',
        reply_markup=reply_markup
    )
    return TRACK

async def track(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора трассы"""
    context.user_data['track'] = update.message.text
    
    keyboard = [
        ['Self-Leveling'],
        ['Acro']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        'Выберите режим:',
        reply_markup=reply_markup
    )
    return MODE

async def mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора режима"""
    context.user_data['mode'] = update.message.text
    await update.message.reply_text(
        'Введите лучшее время в секундах:',
        reply_markup=ReplyKeyboardRemove()
    )
    return BEST_TIME

async def best_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка лучшего времени и сохранение результата"""
    try:
        time = float(update.message.text)
        conn = sqlite3.connect('fpv_leaderboard.db')
        c = conn.cursor()
        c.execute('''INSERT INTO flight_results 
                     (user_id, simulator, track, mode, best_time, date)
                     VALUES (?, ?, ?, ?, ?, ?)''',
                  (update.effective_user.id,
                   context.user_data['simulator'],
                   context.user_data['track'],
                   context.user_data['mode'],
                   time,
                   datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
        conn.close()
        
        await show_main_menu(update, context)
        await update.message.reply_text(
            'Результат успешно сохранен! ✅\n\n'
            f'Симулятор: {context.user_data["simulator"]}\n'
            f'Трасса: {context.user_data["track"]}\n'
            f'Режим: {context.user_data["mode"]}\n'
            f'Лучшее время: {time:.2f} сек'
        )
    except ValueError:
        await update.message.reply_text('Пожалуйста, введите число:')
        return BEST_TIME
    
    return ConversationHandler.END

async def leaderboard_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало просмотра таблицы лидеров"""
    keyboard = [
        ['FPV Freerider'],
        ['DCL The Game'],
        ['Liftoff']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        'Выберите симулятор:',
        reply_markup=reply_markup
    )
    return LEADERBOARD_SIMULATOR

async def leaderboard_simulator(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора симулятора для таблицы лидеров"""
    context.user_data['leaderboard_simulator'] = update.message.text
    
    keyboard = [
        ['Self-Leveling'],
        ['Acro']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        'Выберите режим полёта:',
        reply_markup=reply_markup
    )
    return LEADERBOARD_MODE

async def leaderboard_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора режима для таблицы лидеров"""
    context.user_data['leaderboard_mode'] = update.message.text
    
    keyboard = [
        ['map1'],
        ['map2']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        'Выберите название трассы:',
        reply_markup=reply_markup
    )
    return LEADERBOARD_TRACK

async def leaderboard_track(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора трассы и показ таблицы лидеров"""
    context.user_data['leaderboard_track'] = update.message.text
    
    conn = sqlite3.connect('fpv_leaderboard.db')
    c = conn.cursor()
    
    # Получаем результаты по выбранным параметрам
    c.execute('''SELECT u.lastname, u.firstname, u.group_name, fr.best_time
                 FROM flight_results fr
                 JOIN users u ON fr.user_id = u.user_id
                 WHERE fr.simulator = ? AND fr.mode = ? AND fr.track = ?
                 ORDER BY fr.best_time ASC
                 LIMIT 10''',
              (context.user_data['leaderboard_simulator'],
               context.user_data['leaderboard_mode'],
               context.user_data['leaderboard_track']))
    
    results = c.fetchall()
    conn.close()
    
    current_time = datetime.now().strftime('%H:%M %d.%m.%Y')
    leaderboard = f'Leaderboard Аэроквантум-15 от {current_time} г.\n'
    leaderboard += f'{context.user_data["leaderboard_simulator"]}, {context.user_data["leaderboard_mode"].lower()}, {context.user_data["leaderboard_track"]}\n\n'
    
    if not results:
        leaderboard += 'Нет результатов для выбранных параметров.'
    else:
        for i, (lastname, firstname, group, time) in enumerate(results, 1):
            leaderboard += f'{i}. {time:.3f} - {lastname} {firstname}, гр. {group}\n'
        
        # Добавляем пустые места, если их меньше 10
        for i in range(len(results) + 1, 11):
            leaderboard += f'{i}. (место не занято)\n'
    
    await show_main_menu(update, context)
    await update.message.reply_text(leaderboard)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена регистрации"""
    await show_main_menu(update, context)
    await update.message.reply_text('Действие отменено.')
    return ConversationHandler.END

def main():
    # Инициализация базы данных
    init_db()
    
    # Создаем приложение бота
    application = Application.builder().token('7792446695:AAENgsE0ROOnpwa8cPjHMYmRk5T7QCCukUA').build()

    # Создаем обработчик регистрации пользователя
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^Регистрация$'), register_start)],
        states={
            LASTNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, lastname)],
            FIRSTNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, firstname)],
            GROUP: [MessageHandler(filters.TEXT & ~filters.COMMAND, group)],
            BIRTHDATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, birthdate)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    # Создаем обработчик регистрации результата
    result_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^Регистрация результата$'), register_result_start)],
        states={
            SIMULATOR: [MessageHandler(filters.Regex('^(FPV Freerider|DCL The Game|Liftoff)$'), simulator)],
            TRACK: [MessageHandler(filters.Regex('^(map1|map2)$'), track)],
            MODE: [MessageHandler(filters.Regex('^(Self-Leveling|Acro)$'), mode)],
            BEST_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, best_time)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    # Создаем обработчик просмотра таблицы лидеров
    leaderboard_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^Таблица лидеров$'), leaderboard_start)],
        states={
            LEADERBOARD_SIMULATOR: [MessageHandler(filters.Regex('^(FPV Freerider|DCL The Game|Liftoff)$'), leaderboard_simulator)],
            LEADERBOARD_MODE: [MessageHandler(filters.Regex('^(Self-Leveling|Acro)$'), leaderboard_mode)],
            LEADERBOARD_TRACK: [MessageHandler(filters.Regex('^(map1|map2)$'), leaderboard_track)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    # Добавляем обработчики команд
    application.add_handler(CommandHandler('start', start))
    application.add_handler(conv_handler)
    application.add_handler(result_handler)
    application.add_handler(leaderboard_handler)

    # Запускаем бота
    print('Бот запущен...')
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
