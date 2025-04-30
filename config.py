import os


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', '123334')
    SESSION_TYPE = 'filesystem'

    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'xsour'
    MYSQL_PASSWORD = '1234'
    MYSQL_DB = 'starcourtmall'
    MYSQL_PORT = 3306
