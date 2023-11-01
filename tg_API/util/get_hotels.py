import json
from typing import Dict, Union
from telebot import types

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
            "resultsSize": data_dict['count_hotel'],
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
              amount_photo=5,
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