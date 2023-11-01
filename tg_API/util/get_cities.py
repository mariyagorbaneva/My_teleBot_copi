import json
import requests
from typing import Union, Dict

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from tg_API.util.api_reqiest import request_to_api
from config_data.config import RAPID_API_ENDPOINTS, RAPID_API_HEADERS
from tg_API.util.api_reqiest import request_to_api


def pars_cities(city: str) -> Union[Dict[str, str], None]:
    querystring = {"q": city, "locale": "ru_RU", "langid": "1033", "siteid": "300000001"}

    response = request_to_api(
        method_type='GET',
        url=RAPID_API_ENDPOINTS['cities-groups'],
        payload=querystring,
        headers=RAPID_API_HEADERS)
    print(response)
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

def print_cities(cities_dict: Dict[str, str]) -> InlineKeyboardMarkup:
    """
    Клавиатура с кнопками - выбор подходящего по названию города, из которых пользователь выбирает нужный ему.
    :param cities_dict: словарь с названиями городов и их id.
    :return: клавиатура InlineKeyboardMarkup.
    """
    keyboard = InlineKeyboardMarkup(row_width=1)

    for city, city_id in cities_dict.items():
        keyboard.add(InlineKeyboardButton(text=city, callback_data=for_city.new(city_id=city_id)))
    return keyboard