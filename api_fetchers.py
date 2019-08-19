"""
Функции-обёртки для работы с API.
"""

import logging
import requests

from datetime import datetime, timedelta
from dateutil import parser as date_parser
from requests.exceptions import HTTPError, Timeout

from django.core.cache import cache
from frontend.utils import crl_cacher

from _project_.settings.api import (HEADERS,
                                    API_EVENT_CITIES_ENDPOINT,
                                    API_FULLTEXT_SEARCH,
                                    API_SEANCES_ENDPOINT,
                                    API_PLACES_ENDPOINT,
                                    API_EVENTS_ENDPOINT,
                                    API_SEANCES_ENDPOINT,
                                    API_CITIES_ENDPOINT,
                                    API_ROOT)


logger = logging.getLogger(__name__)


@crl_cacher
def get_place_events(place_id):
    """
    Получение событий по площадке
    :param place_id: ид площадки
    :return: ответ API CRL или словарь с ошибкой
    """
    data = {}
    url = '%s%s%s/' % (API_ROOT, API_EVENTS_ENDPOINT, place_id)
    try:
        data = requests.get(url, headers=HEADERS).json()
    except Exception as err:
        logger.error("Error with getting place: %s\n%s" % (url, str(err)))
        data['error'] = str(err)
    return data


@crl_cacher
def get_cities(params=None, ref=None, ttl=0):
    """
    Возвращает по апи список городов.
    :param params: словарь с параметрами запроса
    :param ref: реферер
    :param ttl: срок кеширования
    :return: ответ API CRL или словарь с ошибкой
    """
    HEADERS.setdefault('Referer', ref)
    url = "%s%s" % (API_ROOT, API_CITIES_ENDPOINT)
    result = {}
    try:
        response = requests.get(url,
                                headers=HEADERS,
                                params=params,
                                timeout=10)
        response.raise_for_status()
        result = response.json()
    except Timeout:
        logger.error("Timeout error with getting cities: %s" % url)
        result['error'] = 'timeout'
    except HTTPError as err:
        logger.error("Error with getting cities: %s" % str(err))
        result['error'] = str(err)
    return result


@crl_cacher
def get_places(params=None, ref=None):
    """
    Возвращает по апи список площадок
    :param params: словарь с параметрами запроса
    :param ref: реферер
    :return: список площадок
    """
    HEADERS.setdefault('Referer', ref)
    url = "%s%s" % (API_ROOT, API_PLACES_ENDPOINT)
    result = []
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        response.raise_for_status()
        result = response.json()
    except Exception as e:
        result.append({'error': str(e)})
    return result


@crl_cacher
def get_events_list(params=None, ref=None):
    """
    Возвращает по апи данные о событиях по заданным параметрам.
    :param ref:
    :param params:
    :param page: номер страницы результатов, начинается с 1.
    :param page_size: количество результатов на страницу
    :return:
    """
    HEADERS.setdefault('Referer', params.get('ref') if not ref else ref)

    url = "%s%s" % (API_ROOT, API_EVENTS_ENDPOINT)
    result = {}

    try:
        response = requests.get(url,
                                headers=HEADERS,
                                params=params,
                                timeout=10)
        response.raise_for_status()
        result = response.json()

        for item in result.get('events', []):
            nearest_at = item.pop('nearest', None)
            latest_at = item.pop('latest', None)
            if nearest_at:
                item['nearest'] = date_parser.parse(nearest_at)
            if latest_at and latest_at != nearest_at:
                item['latest'] = date_parser.parse(latest_at)
            else:
                item['latest'] = None
            place = item.get('event_place', {})
            item['place_slug'] = place.get('slug')
            item['place_name'] = place.get('name')
    except Timeout:
        logger.error("Timeout error with getting events: %s" % url)
        result['error'] = 'timeout'
    except Exception as err:
        logger.error("Error with getting events: %s" % str(err))
        result['error'] = str(err)
    return result
