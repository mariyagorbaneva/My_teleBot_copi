from typing import Dict
from telebot.callback_data import CallbackData
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

for_city = CallbackData('city_id', prefix='search')


def get_cities(cities: Dict[str, str]) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=1)
    for city, city_id in cities.items():
        keyboard.add(InlineKeyboardButton(text=city, callback_data=for_city.new(city_id=city_id)))
    return keyboard

