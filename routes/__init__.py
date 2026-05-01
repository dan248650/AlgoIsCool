from routes.static_bp import static_bp
from routes.algo_bp import algo_bp

from routes.api_bp import api_bp

from routes.login_page import login_bp
from routes.register_page import register_bp

from routes.users_bp import user_bp

from routes.admin_bp import admin_bp


def register_blueprints(app):
    """Регистрация всех Blueprint'ов"""
    app.register_blueprint(static_bp)

    app.register_blueprint(login_bp)
    app.register_blueprint(register_bp)

    app.register_blueprint(algo_bp)

    app.register_blueprint(api_bp)

    app.register_blueprint(user_bp)

    app.register_blueprint(admin_bp)


def register_routes(app):
    register_blueprints(app)
