import os
import mimetypes
from flask import Blueprint, send_file, abort, request, current_app, render_template


static_bp = Blueprint('static_routes', __name__)


@static_bp.route('/static/<path:filename>')
def serve_static(filename):
    """Обслуживание статических файлов"""
    file_path = os.path.join(current_app.config['BASE_DIR'], 'static', filename)

    if not os.path.exists(file_path):
        abort(404)

    if os.path.isdir(file_path):
        abort(403)

    content_type, _ = mimetypes.guess_type(file_path)
    if not content_type:
        ext = os.path.splitext(filename)[1]
        content_type = current_app.config['MIME_TYPES'].get(ext, 'application/octet-stream')

    response = send_file(file_path, mimetype=content_type)
    response.headers['Cache-Control'] = 'no-cache'
    return response


@static_bp.route('/<path:filename>')
def serve_public(filename):
    """Обслуживание статических файлов"""
    # Проверяем в static папке
    file_path = os.path.join(current_app.config['BASE_DIR'], 'static', filename)

    if os.path.exists(file_path) and not os.path.isdir(file_path):
        try:
            return send_file(file_path)
        except Exception as e:
            current_app.logger.error(f"Error serving file: {e}")
            abort(500)

    # Проверяем в assets папке (для картинок, шрифтов)
    assets_path = os.path.join(current_app.config['BASE_DIR'], 'static', 'assets', filename)
    if os.path.exists(assets_path) and not os.path.isdir(assets_path):
        try:
            return send_file(assets_path)
        except Exception as e:
            current_app.logger.error(f"Error serving asset: {e}")
            abort(500)

    # Если не нашли, отдаем 404
    abort(404)


@static_bp.route('/assets/<path:filename>')
def serve_assets(filename):
    """Обслуживание assets (картинки, шрифты)"""
    assets_path = os.path.join(current_app.config['BASE_DIR'], 'static', 'assets', filename)

    if not os.path.exists(assets_path):
        abort(404)

    if os.path.isdir(assets_path):
        abort(403)

    content_type, _ = mimetypes.guess_type(assets_path)
    if not content_type:
        ext = os.path.splitext(filename)[1]
        if ext == '.ttf':
            content_type = 'font/ttf'
        elif ext == '.woff':
            content_type = 'font/woff'
        elif ext == '.woff2':
            content_type = 'font/woff2'
        elif ext == '.avif':
            content_type = 'image/avif'
        else:
            content_type = 'application/octet-stream'

    response = send_file(assets_path, mimetype=content_type)
    response.headers['Cache-Control'] = 'public, max-age=30000000'
    return response


@static_bp.route('/favicon.ico')
def favicon():
    favicon_path = os.path.join(current_app.config['BASE_DIR'], 'static', 'favicon.ico')
    if os.path.exists(favicon_path):
        return send_file(favicon_path, mimetype='image/x-icon')
    return '', 204


@static_bp.route('/')
def home_page():
    """Главная страница"""
    return render_template('home.html')
