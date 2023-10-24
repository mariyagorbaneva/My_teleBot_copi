import json
from datetime import date, timedelta
from typing import Union, Dict

from telebot import types
from telebot.types import CallbackQuery
from telegram_bot_calendar import DetailedTelegramCalendar

from config_data.config import RAPID_API_HEADERS, RAPID_API_ENDPOINTS
from keyboards.city import get_cities, for_city, get_kb_calendar
from main import bot
from states.user_states import state
from tg_API.util.adress import get_hotel_address
from tg_API.util.answer import show_info, count_amount_nights
from tg_API.util.api_reqiest import request_to_api


@bot.message_handler(commands='low')
def send_welcome(message: types.Message):
    bot.send_message(message.from_user.id, "Введите город для поиска отелей")
    bot.delete_state(message.from_user.id, message.chat.id)
    bot.set_state(message.from_user.id, state.city, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['last_command'] = 'low'


@bot.message_handler(state=state.city)
def get_city(message: types.Message):
    kb = get_cities(pars_cities(message.text))
    bot.send_message(message.from_user.id, 'Уточните город: ', reply_markup=kb)


def pars_cities(city: str) -> Union[Dict[str, str], None]:
    query_srting = {'q': city, "locale": "ru_RU", "langid": "1033", "siteid": "300000001"}
    response = request_to_api(
        method_type='GET',
        url='https://hotels4.p.rapidapi.com/locations/v3/search',
        payload=query_srting,
        headers=RAPID_API_HEADERS
    )
    data_site = json.loads(response.text)
    cities = dict()
    if data_site.get('sr'):
        city_list = data_site.get('sr')
        for elem in city_list:
            for k, v in elem.items():
                if k == 'type' and (v == 'CITY' or v == 'MULTICITY'):
                    city_id = elem.get('gaiaId')
                    city_name = elem.get('regionNames').get('fullName')
                    cities[city_name] = city_id
    return cities


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
                print(data.get('last_command'))
                if data.get('last_command') in ('low', 'high'):
                    data_dict = data
                    hotel_cities(call.message, data_dict)
                    # bot.set_state(call.from_user.id, UsersStates.last_command, call.message.chat.id)
                    bot.send_message(call.message.chat.id,
                                     f"😉👌 Вот как-то так.\nМожете ввести ещё какую-нибудь команду!\n"
                                     f"Например: <b>/help</b>", parse_mode="html")



def process_hotels_info(hotels_info_list) -> Dict[int, Dict]:
    """
    Функция получает список словарей - результат парсинга отелей, выбирает нужную информацию, обрабатывает и складывает
    в словарь hotels_info_dict

    :param hotels_info_list: Список со словарями. Каждый словарь - полная информация по отелю (результат парсинга).
    :param amount_nights: Количество ночей.
    :return: Словарь с информацией по отелю: {hotel_id: {hotel_info}} (теоретически может быть пустым).
    """

    hotels_info_dict = dict()
    for key, value in hotels_info_list.items():
        hotel_name = key
        hotel_id = value[0]
        price_per_night = value[2]
        distance_city_center = value[1]
        hotel_neighbourhood = get_hotel_address(value[0])
        total_price = value[4]

        hotels_info_dict[hotel_id] = {
            'name': hotel_name,
            'price_per_night': price_per_night,
            'total_price': total_price,
            'distance_city_center': distance_city_center,
            'hotel_url': f'https://www.hotels.com/h{hotel_id}.Hotel-Information/',
            'hotel_neighbourhood': hotel_neighbourhood
        }
    return hotels_info_dict


def hotel_cities(message: types.Message, data: dict) -> Union[Dict[str, str], None]:  # выводим список отелей по запросу
    global payload

    if data.get('last_command') == 'high':
        sort_order = 'PRICE_HIGHEST_FIRST'
    elif data.get('last_command') == 'bestdeal':
        sort_order = 'DISTANCE'
    else:
        sort_order = 'PRICE_LOW_TO_HIGH'

    check_in = (str(data["start_date"])).split("-")
    check_out = (str(data["end_date"])).split("-")

    if data.get('last_command') in ('high', 'low'):
        payload = {
            "locale": "ru_RU",
            "destination": {"regionId": data['city_id']},
            "resultsSize": int(data['count_hotel']),
            "checkInDate": {
                "day": int(check_in[2]),
                "month": int(check_in[1]),
                "year": int(check_in[0])
            },
            "checkOutDate": {
                "day": int(check_out[2]),
                "month": int(check_out[1]),
                "year": int(check_out[0])
            },
            "rooms": [{"adults": 1, "children": []}],
            "sort": sort_order
        }

    response = request_to_api(
        method_type='POST',
        url=RAPID_API_ENDPOINTS['hotel-list'],
        payload=payload,
        headers=RAPID_API_HEADERS)

    amount_nights = count_amount_nights(data['start_date'], data['end_date'])

    data = json.loads(response.text)

    hotels = dict()
    if data.get('data').get('propertySearch').get('properties'):
        for element in data.get('data').get('propertySearch').get('properties'):
            if len(hotels) < 25:
                if element.get('__typename') == 'Property':
                    hotel_id = element.get('id')
                    hotel_primary_img = element.get('propertyImage').get('image').get('url')
                    current_price = round(element.get('price').get('lead').get('amount'), 2)
                    hotel_distance = round(float(
                        element.get('destinationInfo').get('distanceFromDestination').get('value')) * 1.6, 2)
                    total_price = ''
                    for elem in element.get('price').get('displayMessages'):
                        for k, v in elem.items():
                            if k == 'lineItems':
                                for var in v:
                                    for n, val in var.items():
                                        if n == "value" and "total" in val:
                                            total_price = val
                                            break
                    hotels[element.get('name')] = [
                        hotel_id, hotel_distance, current_price, hotel_primary_img, total_price
                    ]
            else:
                break

    info_hotels = process_hotels_info(hotels)  # много отелей
    show_info(message=message,
              amount_photo=5,
              result_data=info_hotels,
              amount_nights=amount_nights)
    print('Don')
