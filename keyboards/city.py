from datetime import date
from typing import Dict
from telebot.callback_data import CallbackData
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from telegram_bot_calendar import DetailedTelegramCalendar

for_city = CallbackData('city_id', prefix='search')
for_history = CallbackData('history_id', prefix="history")

# def get_cities(cities: Dict[str, str]) -> InlineKeyboardMarkup:
#     keyboard = InlineKeyboardMarkup(row_width=1)
#     for city, city_id in cities.items():
#         keyboard.add(InlineKeyboardButton(text=city, callback_data=for_city.new(city_id=city_id)))
#     return keyboard
def get_kb_calendar() -> InlineKeyboardMarkup:
    calendar, step = DetailedTelegramCalendar(min_date=date.today()).build()
    return calendar