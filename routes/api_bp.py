from flask import Blueprint, request, jsonify
from utils.auth import login_required
from flask_security import current_user
from data.algorithm import Algorithm, db
from utils.slugify import slugify
import re


api_bp = Blueprint('api_bp', __name__, url_prefix='/api')


@api_bp.route('/check-auth', methods=['GET'])
def check_auth():
    if current_user.is_authenticated:
        return jsonify({
            'authenticated': True,
            'user': {
                'id': current_user.id,
                'email': current_user.email,
                'name': current_user.name,
                'surname': current_user.surname,
                'is_admin': current_user.is_admin()
            }
        })
    return jsonify({'authenticated': False})


@api_bp.route('/admin/algorithms', methods=['POST'])
@login_required
def create_algorithm():
    """Создать новый алгоритм"""
    if not current_user.is_admin():
        return jsonify({'error': 'Access denied'}), 403

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON data'}), 400

    try:
        # Если id не передан, генерируем из name
        algo_id = data.get('id')
        if not algo_id:
            name = data.get('name')
            if not name:
                return jsonify({'error': 'name is required'}), 400
            algo_id = slugify(name)
            # гарантируем уникальность
            base_id = algo_id
            counter = 1
            while Algorithm.query.get(algo_id):
                algo_id = f"{base_id}-{counter}"
                counter += 1

        # Проверяем, не существует ли уже
        if Algorithm.query.get(algo_id):
            return jsonify({'error': f'Algorithm with id {algo_id} already exists'}), 409

        # Создаём объект
        algorithm = Algorithm(id=algo_id)
        for field in ['name', 'display_name', 'category_id', 'description_short',
                      'description_full', 'complexity', 'order_index',
                      'default_input_data', 'definition', 'input_schema', 'default_settings',
                      'definition_python', 'definition_mode']:
            if field in data:
                setattr(algorithm, field, data[field])

        # Обязательные поля
        if not algorithm.name:
            return jsonify({'error': 'name is required'}), 400
        if not algorithm.definition:
            return jsonify({'error': 'definition is required'}), 400

        db.session.add(algorithm)
        db.session.commit()
        return jsonify({'id': algorithm.id, 'message': 'Algorithm created'}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api_bp.route('/admin/algorithms/<algorithm_id>', methods=['PUT'])
@login_required
def update_algorithm(algorithm_id):
    """Обновить существующий алгоритм"""
    if not current_user.is_admin():
        return jsonify({'error': 'Access denied'}), 403

    algorithm = Algorithm.query.get(algorithm_id)
    if not algorithm:
        return jsonify({'error': 'Algorithm not found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON data'}), 400

    try:
        for field in ['name', 'display_name', 'category_id', 'description_short',
                      'description_full', 'complexity', 'order_index',
                      'default_input_data', 'definition', 'input_schema', 'default_settings',
                      'definition_python', 'definition_mode']:
            if field in data:
                setattr(algorithm, field, data[field])

        db.session.commit()
        return jsonify({'message': 'Algorithm updated'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api_bp.route('/admin/algorithms/<algorithm_id>', methods=['DELETE'])
@login_required
def delete_algorithm(algorithm_id):
    """Удалить алгоритм"""
    if not current_user.is_admin():
        return jsonify({'error': 'Access denied'}), 403

    algorithm = Algorithm.query.get(algorithm_id)
    if not algorithm:
        return jsonify({'error': 'Algorithm not found'}), 404

    try:
        db.session.delete(algorithm)
        db.session.commit()
        return jsonify({'message': 'Algorithm deleted'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api_bp.route('/admin/algorithms', methods=['GET'])
@login_required
def list_algorithms_admin():
    """Список всех алгоритмов"""
    if not current_user.is_admin():
        return jsonify({'error': 'Access denied'}), 403

    algorithms = Algorithm.query.order_by(Algorithm.order_index).all()
    result = []
    for algo in algorithms:
        result.append({
            'id': algo.id,
            'name': algo.name,
            'display_name': algo.display_name,
            'category_id': algo.category_id,
            'description_short': algo.description_short,
            'complexity': algo.complexity,
            'order_index': algo.order_index,
            'icon': algo.icon,
            'definition': algo.definition,
            'input_schema': algo.input_schema,
            'default_settings': algo.default_settings,
            'default_input_data': algo.default_input_data,
            'definition_python': algo.definition_python,
            'definition_mode': algo.definition_mode
        })
    return jsonify(result), 200


@api_bp.route('/admin/algorithms/<algorithm_id>', methods=['GET'])
@login_required
def get_algorithm_admin(algorithm_id):
    """Получение информации об алгоритме"""
    if not current_user.is_admin():
        return jsonify({'error': 'Access denied'}), 403

    algo = Algorithm.query.get_or_404(algorithm_id)
    result = {
        'id': algo.id,
        'name': algo.name,
        'display_name': algo.display_name,
        'category_id': algo.category_id,
        'description_short': algo.description_short,
        'complexity': algo.complexity,
        'order_index': algo.order_index,
        'icon': algo.icon,
        'definition': algo.definition,
        'input_schema': algo.input_schema,
        'default_settings': algo.default_settings,
        'default_input_data': algo.default_input_data,
        'definition_python': algo.definition_python,
        'definition_mode': algo.definition_mode
    }
    return jsonify(result), 200
