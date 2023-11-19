from telebot import types
from telebot.types import CallbackQuery
from config_data.config import RAPID_API_HEADERS, RAPID_API_ENDPOINTS
from keyboards.city import for_city, get_kb_calendar
from keyboards.yes_no import get_yes_no
from main import bot
from states.user_states import state

from loader import bot
from telebot.types import Message, CallbackQuery
from loguru import logger
from tg_API.util.get_hotels import hotel_cities, low_high_price_answer
from tg_API.util.get_cities import pars_cities, print_cities
from telegram_bot_calendar import DetailedTelegramCalendar
from datetime import date, timedelta
from tg_API.util import api_reqiest


@bot.message_handler(state=state.cities)
def get_city(message: Message):

    cities_dict = pars_cities(message.text)
    if cities_dict:
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['cities'] = cities_dict
        bot.send_message(message.from_user.id, 'Пожалуйста, уточните:', reply_markup=print_cities(cities_dict))
    else:
        bot.send_message(message.from_user.id, 'Нет такого города. Введите ещё раз.')


@bot.callback_query_handler(func=None, city_config=for_city.filter())  # запрашиваем количество отелей
def count_hotel(call: CallbackQuery):

    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    bot.delete_message(call.message.chat.id, call.message.message_id)

    with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:  # достаем данные с кнопки
        data['city_id'] = call.data.split(':')[1]
        data['city'] = [city for city, city_id in data['cities'].items() if city_id == data['city_id']][0]
    bot.set_state(call.from_user.id, state.amount_hotels, call.message.chat.id)
    bot.send_message(call.message.chat.id, text='Введите количество отелей')

@bot.message_handler(state=state.amount_hotels, is_digit=True)  # Если количество отелей - число
def get_amount_hotels(message: Message) -> None:

    if 1 <= int(message.text) <= 10:
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['amount_hotels'] = int(message.text)
        bot.send_message(message.from_user.id, 'Желаете загрузить фото отелей?', reply_markup=get_yes_no())
    else:
        bot.send_message(message.from_user.id, 'Количество отелей в топе должно быть от 1 до 10')


@bot.message_handler(state=state.amount_hotels, is_digit=False)  # Если количество отелей - не число
def amount_hotels_incorrect(message: Message) -> None:

    bot.send_message(message.from_user.id, 'Количество отелей должно быть от 1 до 10')


@bot.callback_query_handler(func=lambda call: call.data == 'yes' or call.data == 'no')
def need_photo_reply(call: CallbackQuery) -> None:

    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

    with bot.retrieve_data(call.message.chat.id, call.message.chat.id) as data:
        if call.data == "yes":
            bot.send_message(call.message.chat.id, text='Введите количество фото')
            data['need_photo'] = True
            bot.set_state(call.from_user.id, state.amount_photo, call.message.chat.id)
        elif call.data == "no":
            data['need_photo'] = False
            data['amount_photo'] = 0
            calendar, step = DetailedTelegramCalendar(min_date=date.today()).build()
            bot.send_message(call.message.chat.id, f"Введите дату заезда", reply_markup=calendar)
        else:
            bot.send_message(call.message.chat.id, text='⚠️ Нажмите кнопку "Да" или "Нет"')

@bot.message_handler(state=state.amount_photo, is_digit=True)  # Если количество фото - число
@logger.catch
def get_amount_photo(message: Message) -> None:

    if 1 <= int(message.text) <= 10:
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['amount_photo'] = int(message.text)
        calendar, step = DetailedTelegramCalendar(min_date=date.today()).build()
        bot.send_message(message.chat.id, f"Введите дату заезда", reply_markup=calendar)
    else:
        bot.send_message(message.from_user.id, 'Количество фото должно быть от 1 до 10')

@bot.callback_query_handler(func=DetailedTelegramCalendar.func())
def date_reply(call: CallbackQuery) -> None:
    """
    Функция, реагирующая на нажатие кнопки на клавиатуре-календаре.
    Проверяет, записаны ли состояния 'start_date' и 'end_date'.
    Если нет - снова предлагает выбрать дату и записывает эти состояния.
    Если да, то проверяет состояние пользователя 'last_command'.
    Если 'last_command' == 'low' или 'high' - завершает опрос и
    вызывает функцию для подготовки ответа на запрос пользователя. Затем ожидает ввода следующей команды.
    Иначе продолжает опрос и предлагает ввести минимальную цену за ночь.

    """

    with bot.retrieve_data(call.message.chat.id, call.message.chat.id) as data:
        if not data.get('start_date'):
            result, key, step = DetailedTelegramCalendar(min_date=date.today()).process(call.data)
        elif not data.get('end_date'):
            new_start_date = data.get('start_date') + timedelta(1)
            result, key, step = DetailedTelegramCalendar(min_date=new_start_date).process(call.data)

    if not result and key:
        bot.edit_message_text("Введите дату", call.message.chat.id, call.message.message_id, reply_markup=key)
    elif result:
        with bot.retrieve_data(call.message.chat.id, call.message.chat.id) as data:
            if not data.get('start_date'):
                data['start_date'] = result
                calendar, step = DetailedTelegramCalendar(min_date=result + timedelta(1)).build()
                bot.edit_message_text("Введите дату выезда",
                                      call.message.chat.id, call.message.message_id, reply_markup=calendar)
            elif not data.get('end_date'):
                data['end_date'] = result

                bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

                if data.get('last_command') in ('low', 'high'):
                    data_dict = data
                    #hotel_cities(call.message, data_dict)
                    low_high_price_answer(call.message, data_dict, call.from_user.username)
                    bot.set_state(call.from_user.id, state.last_command, call.message.chat.id)
                    bot.send_message(call.message.chat.id,
                                     f"😉👌 Вот как-то так.\nМожете ввести ещё какую-нибудь команду!\n"
                                     f"Например: <b>/help</b>", parse_mode="html")
                else:
                    bot.set_state(call.from_user.id, state.start_price, call.message.chat.id)
                    bot.send_message(call.message.chat.id, "Введите минимальную цену за ночь $:")
#@bot.message_handler(state=state.start_price, is_digit=False) # проверяем число
# def star_price_incorrect(message: Message) -> None:
#     bot.send_message(message.from_user.id, 'Введите число больше нуля! ')  #если не число - выводит сообщение об ошибке
@bot.message_handler(state=state.start_price, is_digit=True)
def get_start_price(message: Message) -> None:
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['start_price'] = int(message.text)
    bot.set_state(chat_id=message.chat.id, state=state.end_price, user_id=message.from_user.id)
    bot.send_message(message.chat.id, 'Введите максимальную цену за ночь $: ')

@bot.message_handler(state=state.end_price, is_digit=True)
def get_end_price(message: Message) ->None:
    if int(message.text) > 0:
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            if int(message.text) > data['start_price']:
                data['end_price'] = int(message.text)
                bot.set_state(message.from_user.id, state.end_distance, message.chat.id)
                bot.send_message(message.chat.id, "Введите максимальное расстояние до центра в км\n"
                                                  "(например 10):")
            else:
                bot.send_message(message.chat.id,
                                 f"⚠️ Максимальная цена должна быть больше {data['start_price']}$")
    else:
        bot.send_message(message.from_user.id, '⚠️ Введите число больше нуля')

@bot.message_handler(state=state.end_price, is_digit=False)
def get_end_price_incorrect(message: Message) ->None:
    bot.send_message(message.from_user.id, 'Введите число больше нуля! ')


@bot.message_handler(state=state.end_distance)
def get_end_distance(message: Message) -> None:


    if ',' in message.text:
        message.text = message.text.replace(',', '.')

    try:
        message.text = float(message.text)
        if message.text > 0:
            with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
                data['end_distance'] = message.text
                data_dict = data
                low_high_price_answer(message=message, data=data_dict, user=message.from_user.username)
                bot.set_state(user_id=message.from_user.id, state=state.last_command, chat_id=message.chat.id)
                bot.send_message(message.chat.id, f"Вот как-то так.\nМожете ввести ещё какую-нибудь команду!\n"
                                                  f"Например: <b>/help</b>", parse_mode="html")
        else:
            bot.send_message(message.from_user.id, 'Введите число больше нуля')
    except Exception:
        bot.set_state(user_id=message.from_user.id, state=state.last_command, chat_id=message.chat.id)
        bot.send_message(message.chat.id, "Ошибка. Попробуйте еще раз.\n"
                                          "Введите команду! Например: <b>/help</b>", parse_mode="html")






