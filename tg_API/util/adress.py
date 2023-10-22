import json

from telebot import logger

from config_data.config import RAPID_API_ENDPOINTS, RAPID_API_HEADERS
from tg_API.util.api_reqiest import request_to_api


def get_hotel_address(hotel_id):
    payload = {
        "propertyId": hotel_id
    }

    response = request_to_api(
        method_type='POST',
        url=RAPID_API_ENDPOINTS['hotel-photos'],
        payload=payload,
        headers=RAPID_API_HEADERS)

    data = json.loads(response.text)

    if hotel_id == data.get('data').get('propertyInfo').get('summary').get('id'):
        hotel_address = \
            data.get('data').get('propertyInfo').get('summary').get('location').get('address').get('addressLine')
        return hotel_address