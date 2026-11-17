import json

from flask import Blueprint, render_template, jsonify, request

from data.algorithm import Algorithm
from data.category import Category

from sqlalchemy import func, or_, and_

algo_bp = Blueprint('algo', __name__, url_prefix='/algo')


# ============== СЕРВЕРНЫЕ СТРАНИЦЫ ==============

@algo_bp.route('/catalog')
def catalog_page():
    """Серверная страница с каталогом алгоритмов"""
    categories = Category.query.order_by(Category.order_index).all()

    result = {}
    for cat in categories:
        result[cat.id] = {
            'name': cat.display_name,
            'algorithms': []
        }

    algorithms = (
        Algorithm.query
        .outerjoin(Category, Algorithm.category_id == Category.id)
        .order_by(
            func.coalesce(Category.order_index, 0),
            func.coalesce(Algorithm.order_index, 0),
        )
        .all()
    )
    for algo in algorithms:
        cat_id = algo.category_id
        if cat_id in result:
            result[cat_id]['algorithms'].append({
                'id': algo.id,
                'name': algo.display_name or algo.name
            })

    return render_template('catalog.html', categories=result)


@algo_bp.route('/visualize/<algorithm_id>')
def visualize_page(algorithm_id):
    """Серверная страница для визуализации алгоритма"""
    algorithm = Algorithm.query.get_or_404(algorithm_id)

    # Берём данные по умолчанию из БД
    input_data = algorithm.default_input_data
    if not input_data:
        input_data = {'input_array': []}

    return render_template(
        'visualize_algo.html',
        algorithm=algorithm,
        input_data=json.dumps(input_data),
        algorithm_id=algorithm_id
    )


# ============== API МАРШРУТЫ ==============

@algo_bp.route('/api/algorithms', methods=['GET'])
def api_get_algorithms():
    """Получить список всех алгоритмов"""
    algorithms = (
        Algorithm.query
        .outerjoin(Category, Algorithm.category_id == Category.id)
        .order_by(
            func.coalesce(Category.order_index, 0),
            func.coalesce(Algorithm.order_index, 0),
        )
        .all()
    )
    return jsonify([{
        'id': algo.id,
        'name': algo.name,
        'display_name': algo.display_name,
        'category_id': algo.category_id,
        'input_schema': algo.input_schema,
        'definition_python': algo.definition_python
    } for algo in algorithms])


@algo_bp.route('/api/algorithm/<algorithm_id>', methods=['GET'])
def api_get_algorithm(algorithm_id):
    """Получить информацию об алгоритме"""
    algorithm = Algorithm.query.get_or_404(algorithm_id)
    return jsonify({
        'id': algorithm.id,
        'name': algorithm.name,
        'display_name': algorithm.display_name,
        'category_id': algorithm.category_id,
        'description_short': algorithm.description_short,
        'description_full': algorithm.description_full,
        'complexity': algorithm.complexity,
        'icon': algorithm.icon,
        'order_index': algorithm.order_index,
        'default_input_data': algorithm.default_input_data,
        'definition': algorithm.definition,
        'definition_python': algorithm.definition_python,
        'input_schema': algorithm.input_schema,
        'default_settings': algorithm.default_settings
    })


@algo_bp.route('/api/algorithm/<algorithm_id>/next', methods=['GET'])
@algo_bp.route('/api/algorithm/<algorithm_id>/next', methods=['GET'])
def api_next_algorithm(algorithm_id):
    """Следующий алгоритм в глобальном порядке:
    сначала category.order_index, потом algorithm.order_index."""
    current = Algorithm.query.get_or_404(algorithm_id)

    current_cat = (
        Category.query.get(current.category_id) if current.category_id else None
    )
    current_cat_order = current_cat.order_index if current_cat else 0
    current_alg_order = current.order_index if current.order_index is not None else 0

    cat_order_col = func.coalesce(Category.order_index, 0)
    alg_order_col = func.coalesce(Algorithm.order_index, 0)

    next_algo = (
        Algorithm.query
        .outerjoin(Category, Algorithm.category_id == Category.id)
        .filter(or_(
            cat_order_col > current_cat_order,
            and_(
                cat_order_col == current_cat_order,
                alg_order_col > current_alg_order,
            ),
        ))
        .order_by(cat_order_col, alg_order_col)
        .first()
    )
    if not next_algo:
        # Зацикливание: первый в глобальном порядке
        next_algo = (
            Algorithm.query
            .outerjoin(Category, Algorithm.category_id == Category.id)
            .order_by(cat_order_col, alg_order_col)
            .first()
        )
    if next_algo:
        return jsonify({
            'next_id': next_algo.id,
            'next_name': next_algo.display_name or next_algo.name
        })
    return jsonify({'error': 'No next algorithm'}), 404


@algo_bp.route('/api/visualize', methods=['POST'])
def api_visualize():
    """Выполнить визуализацию алгоритма"""
    from visualization.base_interpreter import BaseInterpreter

    data = request.json
    algorithm_id = data.get('algorithm_id')
    input_data = data.get('input_data', {})
    settings = data.get('settings', {})

    algorithm = Algorithm.query.get_or_404(algorithm_id)
    definition = algorithm.definition
    if not definition:
        return jsonify({'error': 'Algorithm definition not generated'}), 400

    interpreter = BaseInterpreter()
    try:
        result = interpreter.execute_algorithm(definition, input_data, settings)
        return jsonify({
            'commands': result['commands'],
            'snapshots': result['snapshots']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400
