import json
from typing import Dict, Union
from telebot import types
from telebot.types import Message
from main import bot

from config_data.config import RAPID_API_ENDPOINTS, RAPID_API_HEADERS
from tg_API.util.adress import get_hotel_address
from tg_API.util.answer import count_amount_nights, show_info
from tg_API.util.api_reqiest import request_to_api


def hotel_cities(message: types.Message, data_dict: dict) -> Union[Dict[str, str], None]:  # выводим список отелей по запросу
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
    show_info(message=message,
              amount_photo=3,
              result_data=info_hotels,
              amount_nights=amount_nights)



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

    hotels = hotel_cities(message, data)
    if hotels:
        result_dict = process_hotels_info(hotels)
        if sort_index == 1:
            if result_dict:
                show_info(message=message, result_data=result_dict, user=user,
                          amount_nights=amount_nights)
            else:
                bot.send_message(message.chat.id, '⚠️ Не удалось загрузить информацию по отелям города!')

        elif sort_index == 2:
            if result_dict:
                new_result_dict = dict()
                for hotel_id, hotel_data in result_dict.items():
                    if len(new_result_dict.keys()) >= data.get('amount_hotels'):
                        break
                    current_distance = hotel_data.get('distance_city_center')
                    if not current_distance:
                        continue
                    if current_distance <= data.get('end_distance'):
                        new_result_dict[hotel_id] = hotel_data
                if new_result_dict:
                    show_info(message=message, request_data=data, result_data=new_result_dict, user=user,
                              amount_nights=amount_nights)
                else:
                    bot.send_message(message.chat.id, '⚠️ Ничего не нашлось! Измените критерии поиска!')
            else:
                bot.send_message(message.chat.id, '⚠️ По вашему запрос ничего не нашлось! Измените критерии поиска!')
    else:
        bot.send_message(message.chat.id, '⚠️ Ошибка. Попробуйте ещё раз!')


# def show_info(
#         message: Message, request_data: Dict, result_data: Dict[int, Dict], user: str, amount_nights: int
# ) -> None:
#     """
#     Функция вывода информации по найденным отелям.
#     Если пользователь задал вывод фото - Отправляет медиа группу (bot.send_media_group)
#     Иначе составляет список со строковой информацией по отелям. Затем присваивает этот список пейджеру 'my_pages'
#     и вызывает пагинатор 'show_paginator', который и отобразит результат.
#
#     :param message: Сообщение Telegram
#     :param request_data: словарь с данными запроса (город, даты поездки, нужны ли фото)
#     :param result_data: словарь с найденными отелями.
#     :param user: Имя пользователя Telegram (username) - перехватывается и используется только в декораторе
#     для сохранения истории.
#     :param amount_nights: Количество ночей.
#     """
#
#     hotels_info_list = list()
#
#     for hotel_id, hotel_data in result_data.items():
#         if request_data['need_photo']:
#             photo_urls = get_photos(message, hotel_id, request_data['amount_photo'])
#             if photo_urls:
#                 hotel_info_str = get_hotel_info_str_nohtml(hotel_data, amount_nights)
#                 photos = [
#                     InputMediaPhoto(media=url, caption=hotel_info_str) if index == 0 else InputMediaPhoto(media=url)
#                     for index, url in enumerate(photo_urls)
#                 ]
#                 bot.send_media_group(message.chat.id, photos)
#             else:
#                 hotel_info_str = get_hotel_info_str(hotel_data, amount_nights)
#                 bot.send_message(message.chat.id, hotel_info_str, parse_mode="html", disable_web_page_preview=True)
#         else:
#             hotel_info_str = get_hotel_info_str_nohtml(hotel_data, amount_nights)
#             hotels_info_list.append(hotel_info_str)
#
#     if not request_data['need_photo'] and hotels_info_list:
#         my_pages.my_strings = hotels_info_list[:]
#         show_paginator(message)


