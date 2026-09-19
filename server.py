from flask import Flask, redirect, flash
import logging
import os

# Импортируем конфигурацию
from config import Config

# Импортируем модели и БД
from data.db import db
from data.algorithm import (Algorithm, add_linear_search, add_bubble_sort,
                            add_bfs, add_dfs, add_kadane)
from data.category import init_categories

# Импортируем маршруты
from routes import register_blueprints
from utils import error_handlers

from flask_security import Security, SQLAlchemyUserDatastore, current_user
import uuid
from locale import setlocale, Error, LC_ALL

from data.__all_models import User, Role
from utils.generation_password import generate_password_for_user


# Создание приложения
def create_app(config_class=Config):
    app = Flask(__name__,
                static_folder='static',
                template_folder='templates')

    app.config.from_object(config_class)
    logging.basicConfig(level=logging.INFO)

    db.init_app(app)

    with app.app_context():
        # Создаём все таблицы (если их нет)
        db.create_all()
        app.logger.info("Database initialized")

        # Заполняем алгоритмы (создаём или обновляем)
        init_algorithms()
        app.logger.info("Algorithms initialized/updated")

        init_categories()
        app.logger.info("Category added")

    user_datastore = SQLAlchemyUserDatastore(db, User, Role)
    security = Security(app, user_datastore, register_blueprint=False)

    with app.app_context():
        init_database()  # инициализация ролей и админа

    register_blueprints(app)
    error_handlers.register_handlers(app)

    @app.context_processor
    def inject_user():
        return dict(current_user=current_user)

    return app


def init_algorithms():
    """Создаёт или обновляет записи алгоритмов."""
    def update_or_create(algo_func):
        new_algo = algo_func()
        existing = Algorithm.query.get(new_algo.id)
        if existing:
            # обновляем поля
            for key in ['name', 'display_name', 'category_id', 'description_short',
                        'description_full', 'complexity', 'icon', 'order_index',
                        'default_input_data', 'definition', 'input_schema',
                        'default_settings', 'definition_python', 'definition_mode']:
                setattr(existing, key, getattr(new_algo, key))
            db.session.add(existing)
        else:
            db.session.add(new_algo)

    update_or_create(add_linear_search)
    update_or_create(add_bubble_sort)
    update_or_create(add_bfs)
    update_or_create(add_dfs)
    update_or_create(add_kadane)
    db.session.commit()


def init_database():
    try:
        roles = ['admin', 'user']
        for role_name in roles:
            role = db.session.query(Role).filter_by(name=role_name).first()
            if not role:
                role = Role(name=role_name)
                db.session.add(role)
        db.session.commit()

        admin_role = db.session.query(Role).filter_by(name='admin').first()
        admin = db.session.query(User).filter_by(email='admin@algoiscool.ru').first()

        if not admin and admin_role:
            password = generate_password_for_user()
            print(f"Admin password: {password}")

            admin_user = User(
                name='Admin',
                surname='',
                email='admin@algoiscool.ru',
                city_from='Moscow, Russia',
                fs_uniquifier=str(uuid.uuid4()),
                active=True
            )
            admin_user.set_password(password)
            admin_user.roles.append(admin_role)

            db.session.add(admin_user)
            db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Ошибка при инициализации БД: {e}")


# Запуск приложения
if __name__ == '__main__':
    app = create_app()
    print("AlgoIsCool Server Started")
    print(f"Server: http://localhost:{Config.PORT}")
    app.run(
        host='0.0.0.0',
        port=Config.PORT,
        debug=True,
        use_reloader=False
    )
