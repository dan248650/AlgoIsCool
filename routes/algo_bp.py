from flask import Blueprint, render_template, jsonify, request, current_app
from data.algorithm import Algorithm, db
from data.category import Category
import json

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

    algorithms = Algorithm.query.order_by(Algorithm.order_index).all()
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
    algorithms = Algorithm.query.all()
    return jsonify([{
        'id': algo.id,
        'name': algo.name,
        'display_name': algo.display_name,
        'category_id': algo.category_id,
        'input_schema': algo.input_schema
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
        'input_schema': algorithm.input_schema,
        'default_settings': algorithm.default_settings
    })


@algo_bp.route('/api/algorithm/<algorithm_id>/next', methods=['GET'])
def api_next_algorithm(algorithm_id):
    """Получить следующий алгоритм на основе order_index"""
    current = Algorithm.query.get_or_404(algorithm_id)
    # Ищем следующий с большим order_index
    next_algo = Algorithm.query.filter(Algorithm.order_index > current.order_index)\
                               .order_by(Algorithm.order_index).first()
    if not next_algo:
        # Если нет следующего, берём первый (зацикливание)
        next_algo = Algorithm.query.order_by(Algorithm.order_index).first()
    if next_algo:
        return jsonify({
            'next_id': next_algo.id,
            'next_name': next_algo.display_name or next_algo.name
        })
    return jsonify({'error': 'No next algorithm'}), 404


@algo_bp.route('/api/visualize', methods=['POST'])
def api_visualize():
    """Выполнить визуализацию алгоритма"""
    from visualization.array_interpreter import ArrayInterpreter
    from visualization.graph_interpreter import GraphInterpreter

    data = request.json
    algorithm_id = data.get('algorithm_id')
    input_data = data.get('input_data', {})
    settings = data.get('settings', {})

    algorithm = Algorithm.query.get_or_404(algorithm_id)
    definition = algorithm.definition
    algo_type = definition.get('type', 'array')

    if algo_type == 'graph':
        interpreter = GraphInterpreter()
    else:
        interpreter = ArrayInterpreter()

    try:
        result = interpreter.execute_algorithm(
            algorithm.definition,
            input_data,
            settings
        )
        return jsonify({
            'commands': result['commands'],
            'snapshots': result['snapshots']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400
