import os


class Config:
    # Базовая директория проекта
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    # Секретный ключ
    SECRET_KEY = os.environ.get('SECRET_KEY', 'algoiscool-dev-key-change-in-production')

    # База данных
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'users.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SECURITY_PASSWORD_SALT = os.environ.get('SECURITY_PASSWORD_SALT', 'my-fixed-salt')
    SECURITY_LOGIN_URL = '/login'
    SECURITY_LOGOUT_URL = '/logout'
    SECURITY_REGISTER_URL = '/register'
    SECURITY_REGISTERABLE = True
    SECURITY_SEND_REGISTER_EMAIL = False
    SECURITY_LOGIN_USER_TEMPLATE = 'auth/login.html'
    SECURITY_REGISTER_USER_TEMPLATE = 'auth/register.html'
    # Отключаем встроенные эндпоинты Flask-Security, будем использовать свои
    SECURITY_CONFIRMABLE = False
    SECURITY_RECOVERABLE = False
    SECURITY_CHANGEABLE = False
    SECURITY_TRACKABLE = False
    SECURITY_EMAIL_SENDER = None

    # Порт
    PORT = 2109

    # MIME типы
    MIME_TYPES = {
        '.js': 'application/javascript',
        '.css': 'text/css',
        '.html': 'text/html',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.svg': 'image/svg+xml',
        '.ico': 'image/x-icon',
        '.ttf': 'font/ttf',
        '.woff': 'font/woff',
        '.woff2': 'font/woff2',
        '.avif': 'image/avif',
        '.json': 'application/json'
    }
