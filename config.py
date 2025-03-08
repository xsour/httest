import os


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', '123334')
    SESSION_TYPE = 'filesystem'

    MYSQL_HOST = 'yamanote.proxy.rlwy.net'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = 'FOXLydlLlxTUXNwEccYjTReLkPkVJFMj'
    MYSQL_DB = 'starcourtmall'
    MYSQL_PORT = 43735
