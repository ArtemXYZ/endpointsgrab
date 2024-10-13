"""
Все конфиги проекта
"""
# ----------------------------------------------------------------------------------------------------------------------
# ---------------------------------- Импорт стандартных библиотек Пайтона
import os
import psycopg2
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
#
# # ---------------------------------- Импорт сторонних библиотек
from dotenv import find_dotenv, load_dotenv  # Для переменных окружения
load_dotenv(find_dotenv())  # Загружаем переменную окружения
#
# # ----------------------------------------------------------------------------------------------------------------------
# # ---------------------------- Конфигурации подключения к базам данных
drivername = os.environ.get("CONFIG_MART_SV_DRIVERNAME")
username = os.environ.get("CONFIG_MART_SV_USERNAME")
password = os.environ.get("CONFIG_MART_SV_PASSWORD")
host = os.environ.get("CONFIG_MART_SV_HOST")
port = os.environ.get("CONFIG_MART_SV_PORT")
database = os.environ.get("CONFIG_MART_SV_DATABASE")
#
#
# # Создаем строку подключения к базе данных
connection_string_mart_sv = f'postgresql://{username}:{password}@{host}:{port}/{database}'
#
# # Создаем объект engine для подключения через SQLAlchemy engine_mart_sv
ENGINE = create_engine(connection_string_mart_sv)


