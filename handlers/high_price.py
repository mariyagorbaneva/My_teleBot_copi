import json
from typing import Union, Dict

from telebot import types
from keyboards.city import get_cities, for_city
from config_data.config import RAPID_API_HEADERS
from main import bot
from states.user_states import state
from tg_API.util.api_reqiest import request_to_api
from telebot.types import CallbackQuery


@bot.message_handler(commands='low')
def send_welcome(message: types.Message):
    bot.send_message(message.from_user.id, "Введите город для поиска отелей")
    bot.delete_state(message.from_user.id, message.chat.id)
    bot.set_state(message.from_user.id, state.city, message.chat.id)


@bot.message_handler(state=state.city)
def get_city(message: types.Message):
    kb = get_cities(pars_cities(message.text))
    bot.send_message(message.from_user.id, 'Уточните город: ', reply_markup=kb)


def pars_cities(city: str) -> Union[Dict[str, str], None]:
    query_srting = {'q': city,"locale": "ru_RU", "langid": "1033", "siteid": "300000001"}
    response = request_to_api(
        method_type='GET',
        url= 'https://hotels4.p.rapidapi.com/locations/v3/search',
        payload= query_srting,
        headers= RAPID_API_HEADERS
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


@bot.callback_query_handler(func=None, city_config=for_city.filter())
def count_hotel(call: CallbackQuery):
    bot.edit_message_reply_markup(call.message.chat.id, call.message.id, reply_markup=None)
    bot.send_message(call.message.chat.id, text='Введите количество отелей')
    bot.set_state(call.from_user.id, state.count_hotel, call.message.chat.id)

