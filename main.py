import logging
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from database import get_user, create_or_update_user, add_flight_result, get_leaderboard


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

LASTNAME, FIRSTNAME, GROUP, BIRTHDATE = range(4)

SIMULATOR, TRACK, MODE, BEST_TIME, IMAGE = range(4, 9)

LEADERBOARD_SIMULATOR, LEADERBOARD_MODE, LEADERBOARD_TRACK = range(8, 11)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ['Регистрация пользователя'],
        ['Регистрация результата'],
        ['Таблица лидеров']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        'Привет! 👋\n\n'
        'Я бот для системы FPV Simulators Leaderboard.\n'
        'Сначала необходимо зарегистрироваться, затем можно добавлять результаты.\n'
        'Выберите действие:',
        reply_markup=reply_markup
    )

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ['Регистрация пользователя'],
        ['Регистрация результата'],
        ['Таблица лидеров']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        'Выберите действие:',
        reply_markup=reply_markup
    )

async def register_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        'Давайте начнем регистрацию!\n'
        'Пожалуйста, введите вашу фамилию:',
        reply_markup=ReplyKeyboardRemove()
    )
    return LASTNAME

async def lastname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['lastname'] = update.message.text
    await update.message.reply_text('Отлично! Теперь введите ваше имя:')
    return FIRSTNAME

async def firstname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['firstname'] = update.message.text
    await update.message.reply_text('Введите вашу учебную группу:')
    return GROUP

async def group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['group'] = update.message.text
    await update.message.reply_text('Введите вашу дату рождения в формате ДД.ММ.ГГГГ:')
    return BIRTHDATE

async def birthdate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
 
        datetime.strptime(update.message.text, '%d.%m.%Y')
        context.user_data['birthdate'] = update.message.text
        
      
        create_or_update_user(
            user_id=update.effective_user.id,
            lastname=context.user_data['lastname'],
            firstname=context.user_data['firstname'],
            group_name=context.user_data['group'],
            birthdate=context.user_data['birthdate']
        )
        
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

    user = get_user(update.effective_user.id)
    
    if not user:
        await update.message.reply_text(
            'Для добавления результата необходимо сначала зарегистрироваться.\n'
            'Пожалуйста, нажмите кнопку "Регистрация пользователя"'
        )
        return ConversationHandler.END
    
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
    context.user_data['mode'] = update.message.text
    await update.message.reply_text(
        'Введите лучшее время в секундах:',
        reply_markup=ReplyKeyboardRemove()
    )
    return BEST_TIME

async def best_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        time = float(update.message.text)
        context.user_data['best_time'] = time
        await update.message.reply_text(
            'Отлично! Теперь отправьте скриншот, подтверждающий ваше время.\n'
            'Изображение должно быть в формате JPG или PNG.'
        )
        return IMAGE
    except ValueError:
        await update.message.reply_text('Пожалуйста, введите число:')
        return BEST_TIME

async def save_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message.photo:
            await update.message.reply_text('Пожалуйста, отправьте изображение.')
            return IMAGE
        
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'images/{update.effective_user.id}_{timestamp}.jpg'
        
        await file.download_to_drive(filename)
        

        add_flight_result(
            user_id=update.effective_user.id,
            simulator=context.user_data['simulator'],
            track=context.user_data['track'],
            mode=context.user_data['mode'],
            best_time=context.user_data['best_time'],
            image_path=filename
        )
        
        await show_main_menu(update, context)
        await update.message.reply_text(
            'Результат успешно сохранен! ✅\n\n'
            f'Симулятор: {context.user_data["simulator"]}\n'
            f'Трасса: {context.user_data["track"]}\n'
            f'Режим: {context.user_data["mode"]}\n'
            f'Лучшее время: {context.user_data["best_time"]:.2f} сек'
        )
    except ValueError as e:

        await show_main_menu(update, context)
        await update.message.reply_text(
            'Этот результат хуже вашего предыдущего. Сохранен не будет.'
        )
    except Exception as e:
        logging.error(f"Ошибка при сохранении изображения: {str(e)}")
        await show_main_menu(update, context)
        await update.message.reply_text(
            'Произошла ошибка при сохранении результата. Пожалуйста, попробуйте еще раз.'
        )
    
    return ConversationHandler.END

async def leaderboard_start(update: Update, context: ContextTypes.DEFAULT_TYPE):

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

    context.user_data['leaderboard_track'] = update.message.text
    
    results = get_leaderboard(
        simulator=context.user_data['leaderboard_simulator'],
        mode=context.user_data['leaderboard_mode'],
        track=context.user_data['leaderboard_track']
    )
    
    current_time = datetime.now().strftime('%H:%M %d.%m.%Y')
    leaderboard = f'Leaderboard Аэроквантум-15 от {current_time} г.\n'
    leaderboard += f'{context.user_data["leaderboard_simulator"]}, {context.user_data["leaderboard_mode"].lower()}, {context.user_data["leaderboard_track"]}\n\n'
    
    if not results:
        leaderboard += 'Нет результатов для выбранных параметров.'
    else:
        for i, (lastname, firstname, group, time) in enumerate(results, 1):
            leaderboard += f'{i}. {time:.3f} - {lastname} {firstname}, гр. {group}\n'
        

        for i in range(len(results) + 1, 11):
            leaderboard += f'{i}. (место не занято)\n'
    
    await show_main_menu(update, context)
    await update.message.reply_text(leaderboard)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await show_main_menu(update, context)
    await update.message.reply_text('Действие отменено.')
    return ConversationHandler.END

def main():

    application = Application.builder().token('7792446695:AAENgsE0ROOnpwa8cPjHMYmRk5T7QCCukUA').build()


    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^Регистрация пользователя$'), register_start)],
        states={
            LASTNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, lastname)],
            FIRSTNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, firstname)],
            GROUP: [MessageHandler(filters.TEXT & ~filters.COMMAND, group)],
            BIRTHDATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, birthdate)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

 
    result_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^Регистрация результата$'), register_result_start)],
        states={
            SIMULATOR: [MessageHandler(filters.Regex('^(FPV Freerider|DCL The Game|Liftoff)$'), simulator)],
            TRACK: [MessageHandler(filters.Regex('^(map1|map2)$'), track)],
            MODE: [MessageHandler(filters.Regex('^(Self-Leveling|Acro)$'), mode)],
            BEST_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, best_time)],
            IMAGE: [MessageHandler(filters.PHOTO, save_image)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

 
    leaderboard_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^Таблица лидеров$'), leaderboard_start)],
        states={
            LEADERBOARD_SIMULATOR: [MessageHandler(filters.Regex('^(FPV Freerider|DCL The Game|Liftoff)$'), leaderboard_simulator)],
            LEADERBOARD_MODE: [MessageHandler(filters.Regex('^(Self-Leveling|Acro)$'), leaderboard_mode)],
            LEADERBOARD_TRACK: [MessageHandler(filters.Regex('^(map1|map2)$'), leaderboard_track)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )


    application.add_handler(CommandHandler('start', start))
    application.add_handler(conv_handler)
    application.add_handler(result_handler)
    application.add_handler(leaderboard_handler)


    print('Бот запущен...')
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()


