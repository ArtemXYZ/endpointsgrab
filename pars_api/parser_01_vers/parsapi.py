"""
Универсальные инструменты для парсинга данных через API.
"""
# ----------------------------------------------------------------------------------------------------------------------
import os
import requests
import pandas as pd
from pandas import DataFrame
import time
import schedule
from datetime import datetime
import random
import json
import base64
import urllib.parse
from bs4 import BeautifulSoup
from joblib import dump
from joblib import load
from tqdm import tqdm
from typing import Union



from parser_02_vers.params_bank import *  # Все куки хедеры и параметры
# from settings.configs import engine_mart_sv


# ----------------------------------------------------------------------------------------------------------------------
# raise TypeError(f'Object of type {o.__class__.__name__} '
#                         f'is not JSON serializable')
# ----------------------------------------------------------------------------------------------------------------------
class ParsAPI:
    """Вспомогательные методы вынесены в отдельный класс."""

    # Создаём сессию:
    _SESSION = requests.Session()
    _IMITATION_PING_MIN = 0.5
    _IMITATION_PING_MAX = 2.5
    _BASE_HEADERS: dict = BASE_HEADERS # В заголовках необходимо указать Юзер Агент для корректных запросов.
    _BASE_FOLDER_SAVE = '../data/'
    # ------------------------------------------------------------------------------------------------------------------
    def __init__(self):
        pass
    # ------------------------------------------------------------------------------------------------------------------
    # __________________________________________________________________ encoded
    def param_encoded(self, param_string: str | int | float):
        """Базовый метод кодирования в base64."""
        param_string = str(param_string) # Приводим к str принудительно.
        bytes_string = param_string.encode('utf-8') # Преобразуем строку в байтовый объект (bytes), utf-8:
        base64_encoded = base64.b64encode(bytes_string).decode('utf-8')  # Base64-кодирование
        result_encoded = urllib.parse.quote(base64_encoded)  # URL-кодирование
        return result_encoded
    # __________________________________________________________________
    # __________________________________________________________________ encoded_param_single
    def encoded_param_string(self, key: str, value: str) -> str:
        """Mетод кодирования одиночного параметра (ключ: значение) в base64."""
        value_encoded = self.param_encoded(value)
        return f'&{key}={value_encoded}'

    # def encoded_param_dict(self, key: str, value: str) -> dict:
    #     """Mетод кодирования одиночного параметра (ключ: значение) в base64."""
    #     value_encoded = self.url_encoded(value)
    #     return {key: value_encoded}
    #
    # def encoded_param_tuple(self, key: str, value: str) -> tuple:
    #     """Mетод кодирования одиночного параметра (ключ: значение) в base64."""
    #     value_encoded = self.url_encoded(value)
    #     return (key, value_encoded)
    # __________________________________________________________________
    # __________________________________________________________________ validation_input_value
    def values_validation(self, value: any) -> any:
        """Валидация данных.
        Пропускаются только стандартные типы данных. На верхнем уровне, будут приведены в str."""
        if not isinstance(value, (str, int, float, dict, list, tuple, bool)):
            raise ValueError(f"Неподдерживаемый тип данных: {type(value)} для объекта {value}. "
                             f"Допустимые типы даннных: str, int, float, dict, list, tuple, bool.")
        return value

    def args_validation(self,
                        key: str,
                        value: Union[str, int, float, tuple[Union[str, int, float]], list[Union[str, int, float]]]
                        ) -> str:
        """На вход элемент картежа (for in *args)"""
        tmp_params_list = []
        param_string = None

        # Если на вход обычные (str, int, float) - просто кодируем:
        if isinstance(value, (str, int, float)):
            param_string = self.encoded_param_string(key, value)

        # Если на вход (tuple, list), - перебираем по элементам и кодируем:
        elif isinstance(value, (tuple, list)):
            for v in value:
                # if not isinstance(v, (str, int, float)):
                #     raise ValueError(f"Неподдерживаемый тип данных: {type(v)} в итерируемом объекте {value}. "
                #                      f"Элементы должны быть str, int или float.")

                param_string_tmp = self.encoded_param_string(key, v)
                tmp_params_list.append(param_string_tmp)
            param_string = ''.join(tmp_params_list)

        # Не пропускаем другие типы данных:
        else:
            raise ValueError(f"Неподдерживаемый тип данных для входного значения: {type(value)}. "
                             f"Ожидались str, int, float, tuple или list.")
        return param_string
    # __________________________________________________________________
    # __________________________________________________________________ encoded_params_methods
    def encoded_params_list(self, key: str, *values: str | int | float) -> list[tuple]:
        """
        Формирователь закодированных (в base64) параметров 1.0.
        В случаях, когда требуется передать в URL-строку параметры типа: одинаковые ключи - разные значения

                    # Пример в URL-строке:
                    '&filterParams=value_1&filterParams=value_2&filterParams=value_3',

        тогда формируем список картежей всех переданных параметров, повторяя ключ:

                    # Пример выходных параметров (для наглядности не в закодированном виде).
                    filter_params = [
                        ('filterParams', encoded_value_1),
                        ('filterParams', encoded_value_2),
                    ].
                    На верхнем уровне, далее, - передача в request.

        Однако, стоит учитывать, что не все сервисы корректно принимают параметры с одинаковыми ключами. Хотя requests
        корректно формирует URL с повторяющимися параметрами, сервер может их неправильно обрабатывать.
        """
        result_params_list = []
        for value in values:  # Перебираем все значения в *values
            validation_value_encoded = self.args_validation(key, value)  # url_encoded(value) parser_01_vers_(procedural_func)
            param_string = (validation_value_encoded)  # param_string = (key, value_encoded) parser_01_vers_(procedural_func)
            result_params_list.append(param_string)
        return result_params_list

    def encoded_params_monostring(self, key: str, *values: str | int | float) -> str:
        """
        Формирователь закодированных (в base64) параметров 1.1.
        В случаях, когда требуется передать в URL-строку параметры типа: одинаковые ключи - разные значения

                    # Пример в URL-строке:
                    '&filterParams=value_1&filterParams=value_2&filterParams=value_3',

        тогда формируем строку с конкатенацией всех переданных параметров, повторяя ключ:

                    # Пример выходных параметров (для наглядности не в закодированном виде).
                    filter_params = '&filterParams=value_1&filterParams=value_2&filterParams=value_3',
                    На верхнем уровне, далее, - передача в в формируемую строку (full_url = f'{url_base}{ilter_params}.

        Этот метод служит только для передачи параметров запроса с одинаковыми ключами непосредственно
        в формируемую строку (full_url = f'{url_base}{ilter_params}, передача такой строки через метод param в requests
        вызовет ошибку.
        """
        temp_params_list  = []
        # Перебираем все значения в *values
        for value in values:
            param_string = self.args_validation(key, value)  # f'&{key}={self._encoded(value)}' parser_01_vers_(procedural_func)
            temp_params_list.append(param_string)
        result_params = ''.join(temp_params_list)
        return result_params

    def encoded_params_dict(self, no_encoded_params_dict: dict[str, str]) -> dict[str, str]:
        """
        Формирователь закодированных (в base64) параметров 2.0.
        В случаях, когда требуется передать в URL-строку параметры типа: уникальные ключи - значения

                    # Пример в URL-строке:
                    '&filterParams_1=value_1&filterParams_2=value_2&filterParams_3=value_3',

        тогда на основе переданного в метод словаря формируем новый, но уже с закодированными параметрами
        (предварительно проводится валидация данных):

                    # Пример выходных параметров (для наглядности не в закодированном виде).
                    filter_params = {
                        filterParams_1: encoded_value_1
                        filterParams_2: encoded_value_2
                        filterParams_3: encoded_value_3
                        }.
                    На верхнем уровне, далее, - передача в request.
        """
        return {key: self.param_encoded(value) for key, value in no_encoded_params_dict.items()
                if self.values_validation(key) and self.values_validation(value)}
    # __________________________________________________________________
    # __________________________________________________________________ url_construct -
    # def url_construct(self, url_string):
    #
    #     http_url = f'https://{url_string}'
    #
    #     url_base = f'https://{url_string}'
    #
    #     # Конструктор куков:
    #     cookies_count_product = {
    #         'MVID_CITY_ID': city_id,
    #         'MVID_REGION_ID': region_id,
    #         'MVID_REGION_SHOP': region_shop_id,
    #         'MVID_TIMEZONE_OFFSET': timezone_offset,
    #     }
    #
    #     # Полная строка с фильтрами:
    #     full_url = f'{url_count}{result_filters_params}'




    # нужно авторазбиение урл строки и выделение тех частей что будут динамически изменяемы.
    # url_count = f'https://www.mvideo.ru/bff/products/listing?categoryId={category_id}&offset=0&limit=1'


    # __________________________________________________________________

# ----------------------------------------------------------------------------------------------------------------------
# ***
# ----------------------------------------------------------------------------------------------------------------------






# prs = ParsAPI()
# wer = { 's': 'r', 4 : 5,}
# a = prs.encoded_params_dict(wer)
# # a = prs.encoded_params_monostring('qwe',  [2, [3, 4]], (6,(3,)), 45)
# print(a)