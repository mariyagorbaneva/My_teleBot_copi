import json
from typing import Dict, Union
from telebot import types
from telebot.types import Message

from database.db_controller import save_user
from main import bot

from config_data.config import RAPID_API_ENDPOINTS, RAPID_API_HEADERS
from tg_API.util.adress import get_hotel_address
from tg_API.util.answer import count_amount_nights, show_info
from tg_API.util.api_reqiest import request_to_api


def hotel_cities(message: types.Message, data_dict: dict):  # выводим список отелей по запросу
    global payload
    if data_dict.get('last_command') == 'high':
        sort_order = 'PRICE_HIGHEST_FIRST'
    elif data_dict.get('last_command') == 'bestdeal':
        sort_order = 'DISTANCE'
    else:
        sort_order = 'PRICE_LOW_TO_HIGH'

    check_in = (str(data_dict["start_date"])).split("-")
    check_out = (str(data_dict["end_date"])).split("-")

    if data_dict.get('last_command') in ('high', 'low'):
        payload = {
            "locale": "ru_RU",
            "destination": {"regionId": data_dict['city_id']},
            "resultsSize": data_dict['amount_hotels'],
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
        print(data_dict)
    else:
        payload = {
            "destination": {"regionId": data_dict['city_id']},
            "pageNumber": "1",
            "resultsSize": data_dict['amount_hotels'],
            "checkInDate": {
                "day": int(check_in[2]),
                "month": int(check_in[1]),
                "year": int(check_in[0])
            },
            "checkOutDate": {
                "day": int(check_in[2]),
                "month": int(check_in[1]),
                "year": int(check_in[0])
            },
            "rooms": [{"adults": 1, "children": []}],
            "sort": sort_order,
            "filters": {"price": {
                "max": data_dict['end_price'],
                "min": data_dict['start_price']
            }},
        }
    response = request_to_api(
        method_type='POST',
        url=RAPID_API_ENDPOINTS['hotel-list'],
        payload=payload,
        headers=RAPID_API_HEADERS)

    amount_nights = count_amount_nights(data_dict['start_date'], data_dict['end_date'])

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
    user = save_user(message)
    show_info(message=message,
              amount_photo=data_dict['amount_photo'],
              result_data=info_hotels,
              amount_nights=amount_nights,
              request_data=data_dict,
              user=user.id)



def process_hotels_info(hotels_info_list) -> Dict[int, Dict]:
    """
    Функция получает список словарей - результат парсинга отелей, выбирает нужную информацию, обрабатывает и складывает
    в словарь hotels_info_dict
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

def low_high_price_answer(message: Message, data: Dict, user: str) -> None:

    amount_nights = int((data['end_date'] - data['start_date']).total_seconds() / 86400)
    if data.get('last_command') == 'low':
        sort_order_text = f"самых дешевых отелей в городе <b>{data['city']}</b>\n"
        sort_index = 1
    elif data.get('last_command') == 'high':
        sort_order_text = f"самых дорогих отелей в городе <b>{data['city']}</b>\n"
        sort_index = 1
    else:
        sort_order_text = f"В ценовом диапазоне <b>от {data['start_price']}$ до {data['end_price']}$</b>\n" \
                f"Максимальная удаленность от центра: <b>{data['end_distance']} Км</b>\n"
        sort_index = 2

    reply_str = f" Ок, ищем: <b>топ {data['amount_hotels']}</b> " \
                f"{sort_order_text}" \
                f"{f'Нужно загрузить фото' if data['need_photo'] else f'Фото не нужны'}" \
                f" — <b>{data['amount_photo']}</b> штук\n" \
                f"Длительность поездки: <b>{amount_nights} ноч.</b> " \
                f"(с {data['start_date']} по {data['end_date']})."
    bot.send_message(message.chat.id, reply_str, parse_mode="html")

    hotel_cities(message, data)
