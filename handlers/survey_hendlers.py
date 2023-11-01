from telebot import types
from telebot.types import CallbackQuery
from config_data.config import RAPID_API_HEADERS, RAPID_API_ENDPOINTS
from keyboards.city import get_cities, for_city, get_kb_calendar
from main import bot
from states.user_states import state

from loader import bot
from telebot.types import Message, CallbackQuery
from loguru import logger
from tg_API.util import get_cities
from tg_API.util.get_cities import pars_cities, print_cities
from telegram_bot_calendar import DetailedTelegramCalendar
from datetime import date, timedelta
from tg_API.util import api_reqiest


@bot.message_handler(state=state.cities)
def get_city(message: Message):
    kb = get_cities(pars_cities(message.text))
    bot.send_message(message.from_user.id, 'Уточните город: ', reply_markup=kb)

    cities_dict = pars_cities(message.text)
    if cities_dict:
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['cities'] = cities_dict
        bot.send_message(message.from_user.id, 'Пожалуйста, уточните:', reply_markup=print_cities(cities_dict))
    else:
        bot.send_message(message.from_user.id, '⚠️ Не нахожу такой город. Введите ещё раз.')


@bot.callback_query_handler(func=None, city_config=for_city.filter())  # запрашиваем количество отелей
def count_hotel(call: CallbackQuery):
    with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:  # достаем данные с кнопки
        data['city_id'] = call.data.split(':')[1]
    bot.edit_message_reply_markup(call.message.chat.id, call.message.id, reply_markup=None)
    bot.send_message(call.message.chat.id, text='Введите количество отелей')
    bot.set_state(call.from_user.id, state.count_hotel, call.message.chat.id)


@bot.message_handler(state=state.count_hotel)
def get_choose_data(message: types.Message):
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['count_hotel'] = message.text

    kb = get_kb_calendar()
    bot.send_message(message.from_user.id, 'Выберите дату заезда: ', reply_markup=kb)

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

                if data.get('last_command') in ('lowprice', 'highprice'):
                    data_dict = data
                    #low_high_price_answer(call.message, data_dict, call.from_user.username)
                    bot.set_state(call.from_user.id, state.last_command, call.message.chat.id)
                    bot.send_message(call.message.chat.id,
                                     f"😉👌 Вот как-то так.\nМожете ввести ещё какую-нибудь команду!\n"
                                     f"Например: <b>/help</b>", parse_mode="html")
                else:
                    bot.set_state(call.from_user.id, state.start_price, call.message.chat.id)
                    bot.send_message(call.message.chat.id, "Введите минимальную цену за ночь $:")

@bot.message_handler(state=state.start_price, is_digit=True)
def get_start_price(message: Message) -> None:
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['start_price'] = int(message.text)
    bot.set_state(message.chat.id, message.from_user.id, state.end_price)
    bot.send_message(message.chat.id, 'Введите максимальную цену за ночь $: ')

@bot.message_handler(state=state.start_price, is_digit=False) # проверяем число
def star_price_incorrect(message: Message) -> None:
    bot.send_message(message.from_user.id, 'Введите число больше нуля! ')  #если не число - выводит сообщение об ошибке

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
                #data_dict = data
                bot.set_state(message.from_user.id, state.last_command, message.chat.id)
                bot.send_message(message.chat.id, f"Вот как-то так.\nМожете ввести ещё какую-нибудь команду!\n"
                                                  f"Например: <b>/help</b>", parse_mode="html")
        else:
            bot.send_message(message.from_user.id, 'Введите число больше нуля')
    except Exception:
        bot.set_state(message.from_user.id, state.last_command, message.chat.id)
        bot.send_message(message.chat.id, "Ошибка. Попробуйте еще раз.\n"
                                          "Введите команду! Например: <b>/help</b>", parse_mode="html")





    print('Don')
