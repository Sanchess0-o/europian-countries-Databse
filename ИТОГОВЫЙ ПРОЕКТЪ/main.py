import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import logic
from config import TOKEN
import re

bot = telebot.TeleBot(TOKEN)


user_states = {}

def escape_markdown(text):
    """Экранирование специальных символов Markdown"""
    if not text:
        return text
    

    escape_chars = r'_*[]()~`>#+-=|{}.!'
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    
    return text

def format_country_list(countries):
    """Форматирование списка стран без Markdown разметки"""
    if not countries:
        return "Нет данных"
    
  
    regions = {}
    for english_name, name in countries:
        country_info = logic.get_country_by_english_name(english_name)
        if country_info:
            region = country_info[3]
            if region not in regions:
                regions[region] = []
            regions[region].append((english_name, name))
    
   
    response = " ВСЕ СТРАНЫ ЕВРОПЫ:\n\n"
    
    for region, country_list in regions.items():
        response += f"{region}:\n"
        for english_name, name in country_list:
            response += f"   • /{english_name} - {name}\n"
        response += "\n"
    
    return response

@bot.message_handler(commands=['start'])
def start_command(message):
    # Проверяем базу данных
    if not logic.init_db():
        bot.send_message(
            message.chat.id,
            "⚠️ База данных не инициализирована!\n"
            "Для работы бота необходимо заполнить базу данных."
        )
        return
    
    welcome_text = (
        'Привет! 🇪🇺\n'
        'Здесь ты можешь узнать всю информацию про страны Европы.\n'
        'Этот бот может быть полезен для домашних заданий или если лень гуглить.\n\n'
        'Доступные команды:\n'
        '/European_countries - Список всех стран Европы\n'
        '/regions - Список стран по регионам\n'
        '/help - Помощь\n\n'
        'Чтобы узнать о стране, напиши ее название на английском через слэш, например: /Russia'
    )
    bot.send_message(message.chat.id, welcome_text)

@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = (
        ' КАК ПОЛЬЗОВАТЬСЯ БОТОМ:\n\n'
        '1. Просмотр всех стран:\n'
        '   /European_countries - все страны Европы\n'
        '   /regions - страны по регионам\n\n'
        '2. Получение информации о стране:\n'
        '   /[Название_страны_на_английском]\n'
        '   Пример: /France, /Germany, /Italy\n\n'
        '3. После выбора страны используйте кнопки для получения конкретной информации.'
    )
    bot.send_message(message.chat.id, help_text)

@bot.message_handler(commands=['European_countries'])
def show_all_countries(message):
    """Показать все страны"""
    countries = logic.get_all_countries()
    
    if not countries:
        bot.send_message(
            message.chat.id,
            "База данных стран пуста. Запустите database_filler.py для заполнения."
        )
        return
    

    response = format_country_list(countries)
    
   
    bot.send_message(message.chat.id, response)

@bot.message_handler(commands=['regions'])
def show_regions(message):
    """Показать регионы"""
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    
    regions = [
        ("Западная Европа", "west_europe"),
        ("Восточная Европа", "east_europe"),
        ("Северная Европа", "north_europe"),
        ("Южная Европа", "south_europe")
    ]
    
    for region_name, region_code in regions:
        markup.add(InlineKeyboardButton(region_name, callback_data=f"region_{region_code}"))
    
    bot.send_message(message.chat.id, "Выберите регион:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text.startswith('/') and len(message.text) > 1)
def handle_country_command(message):
  
    if message.text in ['/start', '/help', '/European_countries', '/regions']:
        return
    
    country_command = message.text[1:] 
    
   
    country_info = logic.get_country_by_english_name(country_command)
    
    if country_info:
      
        user_states[message.chat.id] = country_command
        
     
        markup = InlineKeyboardMarkup()
        markup.row_width = 2
        
        buttons = [
            (" Столица", "capital"),
            (" Население", "population"),
            (" Площадь", "area"),
            (" Плотность", "density"),
            ("% от Европы", "percentage"),
            (" Границы", "borders"),
            (" Всё сразу", "all"),
            (" Выбрать другую", "change")
        ]
        
        for text, callback in buttons:
            markup.add(InlineKeyboardButton(text, callback_data=callback))
        
        
        country_name_escaped = escape_markdown(country_info[1])
        
        bot.send_message(
            message.chat.id,
            f"Вы выбрали: {country_name_escaped}\nЧто вы хотите узнать об этой стране?",
            reply_markup=markup
        )
    else:
        bot.send_message(
            message.chat.id,
            f"Страна '{country_command}' не найдена.\n"
            "Используйте команду /European_countries для просмотра всех доступных стран."
        )

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    """Обработка нажатий на inline-кнопки"""
    chat_id = call.message.chat.id
    
    if call.data.startswith("region_"):
       
        region_code = call.data.split("_")[1]
        
        region_map = {
            "west_europe": "Западная Европа",
            "east_europe": "Восточная Европа",
            "north_europe": "Северная Европа",
            "south_europe": "Южная Европа"
        }
        
        region_name = region_map.get(region_code, "Неизвестный регион")
        countries = logic.get_countries_by_region(region_name)
        
        if countries:
            response = f"СТРАНЫ {region_name}:\n\n"
            for english_name, name in countries:
                response += f"• /{english_name} - {name}\n"
            
            bot.edit_message_text(
                response,
                chat_id,
                call.message.message_id
            )
        else:
            bot.answer_callback_query(call.id, f"Нет стран в регионе {region_name}")
    
    elif chat_id in user_states:
        country_name = user_states[chat_id]
        country_info = logic.get_country_by_english_name(country_name)
        
        if not country_info:
            bot.answer_callback_query(call.id, "Ошибка: страна не найдена")
            return
        
      
        if call.data == "change":
            bot.edit_message_text(
                "Выберите другую страну, используя команду /[название_страны] или /European_countries для списка всех стран.",
                chat_id,
                call.message.message_id
            )
            return
        
       
        country_name_escaped = escape_markdown(country_info[1])
        
        if call.data == "all":
       
            response = (
                f" ПОЛНАЯ ИНФОРМАЦИЯ О {country_name_escaped}:\n\n"
                f" Столица: {country_info[4] or 'Не указана'}\n"
                f" Население: {logic.format_population(country_info[5])}\n"
                f" Площадь: {logic.format_area(country_info[6])}\n"
                f" Плотность населения: {logic.get_country_info(country_name, 'density')}\n"
                f" % от населения Европы: {logic.get_country_info(country_name, 'percentage')}\n"
                f" Граничит с: {country_info[9] or 'Не указаны'}\n\n"
                f" Регион: {country_info[3]}"
            )
            
        else:
            
            field_map = {
                "capital": (" Столица", "capital"),
                "population": (" Население", "population"),
                "area": (" Площадь", "area"),
                "density": (" Плотность населения", "density"),
                "percentage": (" % от населения Европы", "percentage"),
                "borders": (" Граничит с", "borders")
            }
            
            if call.data in field_map:
                field_name, field_key = field_map[call.data]
                value = logic.get_country_info(country_name, field_key)
                
                value_escaped = escape_markdown(str(value))
                response = f"{field_name} {country_name_escaped}:\n{value_escaped}"
            else:
                response = "Неизвестный запрос"
        
      
        bot.edit_message_text(
            response,
            chat_id,
            call.message.message_id
        )
        
        
        bot.answer_callback_query(call.id)
    
    else:
        bot.answer_callback_query(call.id, "Пожалуйста, сначала выберите страну")



if __name__ == "__main__":
    print("Проверяю базу данных...")
    if logic.init_db():
        print("База данных подключена успешно!")
        print("Бот запущен...")
        bot.polling(none_stop=True)
    else:
        print("ОШИБКА: База данных не инициализирована!")
        print("Запустите сначала: python db.py")