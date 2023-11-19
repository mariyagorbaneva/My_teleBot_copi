import json
from typing import Dict, Union, List

from telebot.types import Message, InputMediaPhoto

from config_data.config import RAPID_API_ENDPOINTS, RAPID_API_HEADERS
from loader import bot
from tg_API.util.api_reqiest import request_to_api


def parse_photos(hotel_id: int) -> Union[List[Dict], None]:
    """
    Функция делает запрос в request_to_api и десериализирует результат. Если запрос получен и десериализация прошла -
    возвращает обработанный результат в виде списка словарей, иначе None.

    :param hotel_id: id отеля для запроса по api.
    :return: None или список словарей с полной информацией по фоткам отеля.
    """

    payload = {"propertyId": hotel_id}
    responce = request_to_api(
        method_type="POST",
        url=RAPID_API_ENDPOINTS['hotel-photos'],
        payload=payload,
        headers=RAPID_API_HEADERS)
    if responce and responce.text != '':  # responce.text == '' - это когда у отеля нет фоток, хотя responce == 200
        result = json.loads(responce.text)
        #print(result)
        return result
    return None


def process_photos(all_photos, amount_photos: int) -> Union[List[str], None]:
    """
    Функция получает список словарей - результат парсинга фоток, выбирает нужную информацию, обрабатывает и складывает
    в список result.

    :param all_photos: Список словарей с полной информацией по фоткам отеля.
    :param amount_photos: Количество фотографий.
    :return: result - список заданной в amount_photos длины с url фоток.
    """
    data = all_photos["data"]["propertyInfo"]["propertyGallery"]["images"]
    photos = [data[i]["image"]["url"] for i in range(amount_photos)]

    return photos


def get_hotel_info_str_nohtml(hotel_data: Dict, amount_nights: int) -> str:
    """
    Функция преобразует данные по отелю из словаря в строку без html.
    Используется для вывода информации через медиа группу (bot.send_media_group).

    :param hotel_data: Словарь с информацией по отелю.
    :param amount_nights: Количество ночей.
    :return: Строка без html с информацией по отелю.
    """

    result = f" {hotel_data['name']}\n" \
             f" Район: {hotel_data['hotel_neighbourhood']}\n" \
             f" Расстояние до центра: {hotel_data['distance_city_center']} Км\n" \
             f" Цена за 1 ночь: от {hotel_data['price_per_night']}$\n" \
             f" Примерная стоимость за {amount_nights} ноч.: {hotel_data['total_price']}$\n" \
             f"️ Подробнее об отеле: {hotel_data['hotel_url']}"
    return result


def get_hotel_info_str(hotel_data: Dict, amount_nights: int) -> str:
    """
    Функция преобразует данные по отелю из словаря в строку с html.
    Используется для вывода информации через сообщение (bot.send_message).

    :param hotel_data: Словарь с информацией по отелю.
    :param amount_nights: Количество ночей.
    :return: Строка с html с информацией по отелю
    """

    result = f"<b> Отель:</b> {hotel_data['name']}\n" \
             f"<b> Район:</b> {hotel_data['hotel_neighbourhood']}\n" \
             f"<b> Расстояние до центра:</b> {hotel_data['distance_city_center']} Км\n" \
             f"<b> Цена за 1 ночь: </b> от {hotel_data['price_per_night']}$\n" \
             f"<b> Примерная стоимость за {amount_nights} ноч.:</b> {hotel_data['total_price']}$\n" \
             f"<b> Подробнее об отеле <a href='{hotel_data['hotel_url']}'>на сайте >></a></b>"
    return result


def count_amount_nights(start, end) -> int:
    amount_nights = int((end - start).total_seconds() / 86400)
    return amount_nights


def get_photos(message: Message, hotel_id: int, amount_photo: int) -> Union[List[str], None]:
    """
    Функция делает запросы на парсинг фото и на обработку полученных данных.
    В результате каждого из запросов может прийти None, тогда выдается сообщение об ошибке и возвращается None

    :param message: сообщение Telegram
    :param hotel_id: id отеля
    :param amount_photo: количество фото
    :return: photos_list - список с url фото или None
    """
    print('ID отеля', hotel_id)
    photos_info_list = parse_photos(hotel_id)
    if photos_info_list:
        photos_list = process_photos(photos_info_list, amount_photo)
        if photos_list:
            return photos_list
    bot.send_message(message.chat.id, '⚠️ Ошибка загрузки фото.')
    print(amount_photo)
    return None


def show_info(
        message: Message, amount_photo: int, result_data: Dict[int, Dict], amount_nights: int
) -> None:
    """
    Функция вывода информации по найденным отелям.
    Если пользователь задал вывод фото - Отправляет медиа группу (bot.send_media_group)
    Иначе составляет список со строковой информацией по отелям. Затем присваивает этот список пейджеру 'my_pages'
    и вызывает пагинатор 'show_paginator', который и отобразит результат.

    :param message: Сообщение Telegram
    :param amount_photo: словарь с данными запроса (город, даты поездки, нужны ли фото)
    :param result_data: словарь с найденными отелями.
    :param user: Имя пользователя Telegram (username) - перехватывается и используется только в декораторе
    для сохранения истории.
    :param amount_nights: Количество ночей.
    """

    for hotel_id, hotel_data in result_data.items():
        photo_urls = get_photos(message, hotel_id, amount_photo)
        if photo_urls:
            hotel_info_str = get_hotel_info_str_nohtml(hotel_data, amount_nights)
            photos = [
                InputMediaPhoto(media=url, caption=hotel_info_str) if index == 0 else InputMediaPhoto(media=url)
                for index, url in enumerate(photo_urls)
            ]
            bot.send_media_group(message.chat.id, photos)
        else:
            hotel_info_str = get_hotel_info_str(hotel_data, amount_nights)
            bot.send_message(message.chat.id, hotel_info_str, parse_mode="html", disable_web_page_preview=True)

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

