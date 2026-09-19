from flask import (Blueprint, render_template, current_app, flash,
                   redirect, url_for, request, abort)
from utils.auth import login_required
from flask_security import current_user
from data.db import db
from data.__all_models import User, Role, Algorithm
import os
import psutil
import platform
import sqlite3
from datetime import datetime
from forms.algorithm import AlgorithmForm
from visualization.python_to_low import generate_low_level_from_python
import json
from utils.slugify import slugify


admin_bp = Blueprint('admin_bp', __name__, template_folder='templates')


@admin_bp.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin():
        return "Доступ запрещён", 403

    # Статистика по пользователям
    total_users = User.query.count()
    active_users = User.query.filter_by(active=True).count()
    admin_users = User.query.join(User.roles).filter(Role.name == 'admin').count()

    # Алгоритмы
    total_algorithms = Algorithm.query.count()

    # База данных
    db_uri = current_app.config['SQLALCHEMY_DATABASE_URI']
    db_path = db_uri.replace('sqlite:///', '')
    db_size = os.path.getsize(db_path) if os.path.exists(db_path) else 0

    # Системная информация
    system_info = {
        'platform': platform.platform(),
        'python_version': platform.python_version(),
        'hostname': platform.node()
    }

    # Использование ресурсов
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')

    # Статистика по таблицам
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    table_stats = []
    for table in tables:
        table_name = table[0]
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        table_stats.append({'name': table_name, 'count': count})
    conn.close()

    # Списки для таблиц
    users = User.query.all()
    algorithms = Algorithm.query.order_by(Algorithm.order_index).all()

    return render_template('admin/dashboard.html',
                           total_users=total_users,
                           active_users=active_users,
                           admin_users=admin_users,
                           total_algorithms=total_algorithms,
                           db_size=db_size,
                           db_path=os.path.basename(db_path),
                           table_stats=table_stats,
                           system_info=system_info,
                           memory=memory,
                           disk=disk,
                           users=users,
                           algorithms=algorithms,
                           now=datetime.now())


@admin_bp.route('/admin/algorithms/add', methods=['GET', 'POST'])
@login_required
def add_algorithm():
    if not current_user.is_admin():
        abort(403)
    form = AlgorithmForm()
    if form.validate_on_submit():
        try:
            algo_id = slugify(form.name.data)
            base_id = algo_id
            counter = 1
            while Algorithm.query.get(algo_id):
                algo_id = f"{base_id}-{counter}"
                counter += 1

            algorithm = Algorithm(id=algo_id)
            algorithm.name = form.name.data
            algorithm.display_name = form.display_name.data or None
            algorithm.category_id = form.category_id.data or None
            algorithm.order_index = form.order_index.data or 0
            algorithm.description_short = form.description_short.data or None
            algorithm.description_full = form.description_full.data or None
            algorithm.complexity = form.complexity.data or None
            algorithm.definition_mode = form.definition_mode.data

            if form.definition_mode.data == 'python':
                python_code = form.definition_python.data
                # Передаём default_input_data и default_settings как пример
                input_data = json.loads(form.default_input_data.data) if form.default_input_data.data else {}
                settings = json.loads(form.default_settings.data) if form.default_settings.data else {}
                definition = generate_low_level_from_python(python_code, input_data, settings)
                algorithm.definition = definition
                algorithm.definition_python = python_code
            else:
                definition = {
                    'type': form.definition_type.data,
                    'initial_state': json.loads(form.definition_initial_state.data) if form.definition_initial_state.data and form.definition_initial_state.data.strip() else {},
                    'steps': json.loads(form.definition_steps.data)
                }
                algorithm.definition = definition
                algorithm.definition_python = None

            algorithm.input_schema = json.loads(form.input_schema.data) if form.input_schema.data and form.input_schema.data.strip() else None
            algorithm.default_settings = json.loads(form.default_settings.data) if form.default_settings.data and form.default_settings.data.strip() else None
            algorithm.default_input_data = json.loads(form.default_input_data.data) if form.default_input_data.data and form.default_input_data.data.strip() else None

            db.session.add(algorithm)
            db.session.commit()
            flash('Алгоритм успешно создан!', 'success')
            return redirect(url_for('admin_bp.admin_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка: {str(e)}', 'danger')
    return render_template('admin/algorithm_form.html', form=form, title='Добавление алгоритма', action='add', return_url=url_for('admin_bp.admin_dashboard'))


@admin_bp.route('/admin/algorithms/edit/<algorithm_id>', methods=['GET', 'POST'])
@login_required
def edit_algorithm(algorithm_id):
    if not current_user.is_admin():
        abort(403)
    algorithm = Algorithm.query.get_or_404(algorithm_id)
    form = AlgorithmForm()
    if request.method == 'GET':
        form.name.data = algorithm.name
        form.display_name.data = algorithm.display_name
        form.category_id.data = algorithm.category_id
        form.order_index.data = algorithm.order_index
        form.description_short.data = algorithm.description_short
        form.description_full.data = algorithm.description_full
        form.complexity.data = algorithm.complexity
        form.definition_mode.data = algorithm.definition_mode

        form.definition_python.data = algorithm.definition_python

        if algorithm.definition:
            form.definition_type.data = algorithm.definition.get('type', 'array')
            form.definition_initial_state.data = json.dumps(algorithm.definition.get('initial_state', {}), ensure_ascii=False, indent=2)
            form.definition_steps.data = json.dumps(algorithm.definition.get('steps', []), ensure_ascii=False, indent=2)
        else:
            form.definition_steps.data = '[]'

        form.input_schema.data = json.dumps(algorithm.input_schema, ensure_ascii=False, indent=2) if algorithm.input_schema else ''
        form.default_settings.data = json.dumps(algorithm.default_settings, ensure_ascii=False, indent=2) if algorithm.default_settings else ''
        form.default_input_data.data = json.dumps(algorithm.default_input_data, ensure_ascii=False, indent=2) if algorithm.default_input_data else ''

    if form.validate_on_submit():
        try:
            algorithm.name = form.name.data
            algorithm.display_name = form.display_name.data or None
            algorithm.category_id = form.category_id.data or None
            algorithm.order_index = form.order_index.data or 0
            algorithm.description_short = form.description_short.data or None
            algorithm.description_full = form.description_full.data or None
            algorithm.complexity = form.complexity.data or None
            algorithm.definition_mode = form.definition_mode.data

            if form.definition_mode.data == 'python':
                python_code = form.definition_python.data
                input_data = json.loads(form.default_input_data.data) if form.default_input_data.data else {}
                settings = json.loads(form.default_settings.data) if form.default_settings.data else {}
                definition = generate_low_level_from_python(python_code, input_data, settings)
                algorithm.definition = definition
                algorithm.definition_python = python_code
            else:
                definition = {
                    'type': form.definition_type.data,
                    'initial_state': json.loads(form.definition_initial_state.data) if form.definition_initial_state.data and form.definition_initial_state.data.strip() else {},
                    'steps': json.loads(form.definition_steps.data)
                }
                algorithm.definition = definition
                algorithm.definition_python = None

            algorithm.input_schema = json.loads(form.input_schema.data) if form.input_schema.data and form.input_schema.data.strip() else None
            algorithm.default_settings = json.loads(form.default_settings.data) if form.default_settings.data and form.default_settings.data.strip() else None
            algorithm.default_input_data = json.loads(form.default_input_data.data) if form.default_input_data.data and form.default_input_data.data.strip() else None

            db.session.commit()
            flash('Алгоритм обновлён', 'success')
            return redirect(url_for('admin_bp.admin_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка: {str(e)}', 'danger')
    return render_template('admin/algorithm_form.html', form=form, title='Редактирование алгоритма', action='edit', algorithm_id=algorithm_id, return_url=url_for('admin_bp.admin_dashboard'))


@admin_bp.route('/admin/algorithms/delete/<algorithm_id>', methods=['POST'])
@login_required
def delete_algorithm(algorithm_id):
    if not current_user.is_admin():
        abort(403)
    algorithm = Algorithm.query.get_or_404(algorithm_id)
    try:
        db.session.delete(algorithm)
        db.session.commit()
        flash('Алгоритм удалён', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка удаления: {str(e)}', 'danger')
    return redirect(url_for('admin_bp.admin_dashboard'))
