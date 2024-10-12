from parser_03_vers.base_property import BaseProperty

import requests
import json
import base64  # переопределяется (зацикливание)
import urllib.parse  # переопределяется (зацикливание)
from datetime import datetime  # переопределяется (зацикливание)
import os
import requests
import pandas as pd
from pandas import DataFrame
import time
# from bs4 import BeautifulSoup
from joblib import dump
from joblib import load
# from apscheduler.triggers.cron import CronTrigger

# ----------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------
class ServiceTools(BaseProperty):
    """Вспомогательные методы вынесены в отдельный класс."""

    def __init__(self):
        super().__init__()  # Наследуем атрибуты из BaseProperty

        self.__session = self._get_session()  # Экземпляр сессии:
        self.__base_headers = self._get_headers()
        self.__name_table = self._get_name_table()
        self.__schema = self._get_name_schem()
        self.__con = self._get_connect()
        # self.__bloc_scheduler = self._get_scheduler()
        # self.__cron_trigger = self._get_cron_trigger


        # pass

    # __________________________________________________________________ TOOLS
    @staticmethod
    def _check_path_file(path_file):
        """
        Перед сохранением результатов работы парсера проверяем наличие существования директории, если таковой нет,
        то создается.
        """
        # ________________________________________________ CHECK
        # Получаем директорию из пути:
        path_dir = os.path.dirname(path_file)

        # Проверка, существует ли директория, создание её, если нет:
        if not os.path.exists(path_dir):
            os.makedirs(path_dir)
            print(f'Создана новая дирректория для сохранения файлов: {path_dir}')

    def _save_data(self, df: DataFrame, path_file_dump, path_file_excel):
        """
        Перед сохранением результатов работы парсера проверяем наличие существования директории, если таковой нет,
        то создаётся.
        """
        # ________________________________________________ CHECK
        self._check_path_file(path_file_dump)
        self._check_path_file(path_file_excel)
        # ________________________________________________ SAVE
        # Сохраняем результат парсинга в дамп и в эксель:
        dump(df, path_file_dump)  # _name_dump = '../data/df_full_branch_data.joblib'
        df.to_excel(path_file_excel, index=False)  # _name_excel = '../data/df_full_branch_data.xlsx'
        print('Результат парсинга успешно сохранен в дамп и в эксель файлы.')

    # def _get_response(self, url: str, params: dict = None, cookies: dict = None, json_type=True) -> object:
    #     """Универсальная функция для запросов с передаваемыми параметрами. """
    #
    #     # Устанавливаем куки в сессии
    #     if self.__session and cookies:
    #         self.__session.cookies.update(cookies)
    #
    #     # Обычный запрос или сессия:
    #     if self.__session:
    #         response = self.__session.get(url, headers=self.__base_headers, params=params)
    #
    #     else:
    #         response = requests.get(url, headers=self.__base_headers, params=params, cookies=cookies)
    #
    #     # Выполнение запроса:
    #     if response.status_code == 200:
    #         if json_type:
    #             data = response.json()  # Если ответ нужен в json:
    #         elif not json_type:
    #             data = response.text  # Если ответ нужен в html:
    #     else:
    #         data = None
    #         print(f"Ошибка: {response.status_code} - {response.text}")
    #     return data

    def _get_response_json(self, url: str = None, params: dict = None, cookies: dict = None) -> object:
        """Функция для запросов с мутабельными параметрами. """

        # Устанавливаем куки в сессии (если были переданы):
        if cookies:
            self.__session.cookies.update(cookies)

        try:
            # Выполнение запроса с сессией
            response = self.__session.get(url=url, headers=self.__base_headers, params=params)
            # Проверка кода ответа
            if response.status_code == 200:
                data = response.json()  # Ответ в формате JSON

            else:
                # Обработка некорректных HTTP ответов
                raise requests.exceptions.HTTPError(f"Ошибка HTTP: {response.status_code} - {response.text}")

        # Перехватываем любые ошибки, включая сетевые и прочие исключения
        except Exception as error_connect:
            raise  # Передача исключения на верхний уровень для обработки
        return data

    def _get_no_disconnect_request(self, url: str = None, params: dict = None, cookies: dict = None):
        # , json_type=True, retries=20, timeout=120
        """
        requests.exceptions.ReadTimeout: если сервер долго не отвечает.
        requests.exceptions.ChunkedEncodingError: разрыв соединения в процессе передачи данных.
        requests.exceptions.RequestException: общее исключение для отлова любых других ошибок,
        связанных с запросами, включая неожиданные сбои.

        Обработка непредвиденных ошибок: Если возникает ошибка, не связанная с потерей соединения или таймаутом,
        она будет обработана блоком except requests.exceptions.RequestException, что предотвратит аварийное
        завершение программы
        """
        attempt = 0  # Количество попыток
        while attempt < self._get_retries():
            try:
                # Основной запрос:
                data = self._get_response_json(url=url, params=params, cookies=cookies)
                return data  # Возвращаем данные, если успешен

            except (requests.exceptions.ConnectionError,
                    requests.exceptions.Timeout,
                    requests.exceptions.ChunkedEncodingError) as e:
                # Обработка ошибок соединения
                attempt += 1
                print(
                    f"Ошибка соединения: {e}. Попытка {attempt}/{self._get_retries()}."
                    f" Повтор через {self._get_timeout()} сек.")
                time.sleep(self._get_timeout())  # Тайм-аут перед повторной попыткой

            except requests.exceptions.HTTPError as e:
                # Обработка HTTP ошибок
                print(f"HTTP ошибка: {e}. Попытка {attempt + 1}/{self._get_retries()}.")
                attempt += 1
                time.sleep(self._get_timeout())

            except Exception as e:
                # Обработка любых других ошибок
                print(f"Непредвиденная ошибка: {e}. Прерывание.")
                return None

            print("Не удалось выполнить запрос после нескольких попыток.")
            return None

    @staticmethod
    def _base64_decoded(url_param_string):
        """
        Расшифровка параметров URL.
        :param url_param_string: (base64_string)
        :type url_param_string:
        :return:
        :rtype:
        """
        try:
            # Шаг 1: URL-декодирование
            url_param_string_decoded = urllib.parse.unquote(url_param_string)
            # Шаг 2: Base64-декодирование
            base64_decoded_string = base64.b64decode(url_param_string_decoded).decode('utf-8')
            return base64_decoded_string
        except Exception as e:
            print(f'Ошибка декодирования: {e}')
            return None

    @staticmethod
    def _encoded_request_input_params(branch_code: str, region_shop_code: str):
        """
         Формирует закодированные параметры запроса для фильтрации.

        :param branch_code: Код филиала
        :param region_shop_code: Код магазина региона
        :return: Список закодированных параметров фильтра
        :rtype: list

        region_shop_code = 'S906'
        branch_code = 'A311'
        """

        results_keys_value = []

        # 1. Формирование фильтров:
        filter_param_9 = f'["Только в наличии","-9","Да"]'
        filter_param_12 = f'["Забрать из магазина по адресу","-12","{branch_code}"]'
        filter_param_11 = f'["Забрать через 15 минут","-11","{region_shop_code}"]'
        filter_tuple = (filter_param_9, filter_param_12, filter_param_11)

        # 2. Кодирование:
        for param_list in filter_tuple:
            # Преобразование списка в строку
            joined_string = str(param_list)

            encoded_list = joined_string.encode('utf-8')  # Преобразуем списки в строку и кодируем в  в байты 'utf-8':
            base64_encoded = base64.b64encode(encoded_list).decode('utf-8')  # Base64-кодирование
            # print(f"Base64-кодированная строка: {base64_encoded}")
            final_encoded = urllib.parse.quote(base64_encoded)  # URL-кодирование
            # print(f"Итоговый URL-кодированный параметр: {final_encoded}")

            # 3. Сохраняем в виде словаря для передачи как параметр в строку запроса.
            # Добавляем в список результат кодирования:
            results_keys_value.append(final_encoded)  # Ожидаем на выход: [рез1, рез2, рез3]
            # print(results_keys_value)

        filter_params = (f'&filterParams={results_keys_value[0]}'
                         f'&filterParams={results_keys_value[1]}'
                         f'&filterParams={results_keys_value[2]}')

        return filter_params






# ----------------------------------------------------------------------------------------------------------------------

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
                    На верхнем уровне, далее,- передача в request.

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