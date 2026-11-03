import sqlalchemy
from sqlalchemy import orm
from data.db import db
from sqlalchemy_serializer import SerializerMixin
from sqlalchemy import JSON
from datetime import datetime


class Algorithm(db.Model):
    __tablename__ = 'algorithms'

    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.Text, nullable=False)

    # foreign key
    category_id = db.Column(db.String(50), db.ForeignKey('categories.id'))

    # relationship
    category_rel = db.relationship('Category', backref='algorithms')

    display_name = db.Column(db.String(100))          # Отображаемое имя в каталоге
    description_short = db.Column(db.String(200))     # Краткое описание (для каталога)
    description_full = db.Column(db.Text)             # Полное описание
    complexity = db.Column(db.String(50))             # Оценка сложности
    icon = db.Column(db.String(10))
    order_index = db.Column(db.Integer, default=0)    # Порядок для пагинации
    default_input_data = db.Column(JSON)              # Данные по умолчанию

    definition = db.Column(JSON, nullable=False)      # Сгенерированное low-level описание
    input_schema = db.Column(JSON)
    default_settings = db.Column(JSON)

    definition_python = db.Column(db.Text, nullable=True)  # Python-код алгоритма
    definition_mode = db.Column(db.String(20), default='python')  # 'low_level' или 'python'


def _build_definition(python_code, default_input, default_settings):
    """Сгенерировать low-level definition из python-кода алгоритма."""
    from visualization.python_to_low import generate_low_level_from_python
    return generate_low_level_from_python(python_code, default_input, default_settings)


# ============================================================
# Линейный поиск
# ============================================================

def add_linear_search():
    python_code = (
        'w = Window("main")\n'
        'v = Vector(input_array)\n'
        'w.attach(v)\n'
        '\n'
        'for i in range(len(input_array)):\n'
        '    v.highlight(i, "orange")\n'
        '    if input_array[i] == target:\n'
        '        v.highlight(i, "green")\n'
        '        wait(600)\n'
        '        break\n'
        '    v.unhighlight(i)\n'
    )
    default_input = {
        "input_array": [64, 34, 25, 12, 22, 11, 90],
        "target": 22,
    }
    default_settings = {
        "speed_factor": 1.0,
        "colors": {
            "current": "#FFA07A",
            "found": "#4CAF50",
        },
    }
    definition = _build_definition(python_code, default_input, default_settings)

    return Algorithm(
        id="linear-search",
        name="Линейный поиск",
        display_name="Линейный поиск",
        category_id="search",
        description_short="Последовательный перебор элементов",
        description_full="Линейный поиск — алгоритм, который последовательно проверяет каждый элемент массива, пока не найдет искомый или не дойдет до конца.",
        complexity="O(n)",
        icon="linear",
        order_index=10,
        default_input_data=default_input,
        input_schema={
            "input_array": "array",
            "target": "number",
        },
        default_settings=default_settings,
        definition=definition,
        definition_python=python_code,
        definition_mode='python',
    )


# ============================================================
# Сортировка пузырьком
# ============================================================

def add_bubble_sort():
    python_code = (
        'w = Window("main")\n'
        'v = Vector(input_array)\n'
        'w.attach(v)\n'
        '\n'
        'n = len(input_array)\n'
        'for i in range(n - 1):\n'
        '    for j in range(n - i - 1):\n'
        '        v.highlight([j, j + 1], "orange")\n'
        '        if input_array[j] > input_array[j + 1]:\n'
        '            v.highlight([j, j + 1], "red")\n'
        '            v.swap(j, j + 1)\n'
        '            input_array[j], input_array[j + 1] = input_array[j + 1], input_array[j]\n'
        '        v.unhighlight([j, j + 1])\n'
        '    v.highlight(n - i - 1, "green")\n'
        'v.highlight(0, "green")\n'
    )
    default_input = {
        "input_array": [64, 34, 25, 12, 22, 11, 90],
    }
    default_settings = {
        "speed_factor": 1.0,
        "colors": {
            "comparing": "#FFA07A",
            "swapping": "#FF6B6B",
            "sorted": "#4CAF50",
            "default": "#e0e0e0",
        },
    }
    definition = _build_definition(python_code, default_input, default_settings)

    return Algorithm(
        id="bubble-sort",
        name="Сортировка пузырьком",
        display_name="Сортировка пузырьком",
        category_id="sorting",
        description_short="Попарное сравнение и обмен соседних элементов",
        description_full="Сортировка пузырьком — простой алгоритм сортировки, который многократно проходит по массиву, сравнивая соседние элементы и меняя их местами, если они стоят в неправильном порядке. Каждый проход 'всплывает' наибольший элемент в конец массива.",
        complexity="O(n²)",
        icon="bubble",
        order_index=20,
        default_input_data=default_input,
        input_schema={
            "input_array": "array",
        },
        default_settings=default_settings,
        definition=definition,
        definition_python=python_code,
        definition_mode='python',
    )


# ============================================================
# Поиск в ширину (BFS)
# ============================================================

def add_bfs():
    python_code = (
        'w = Window("main")\n'
        'g = Graph(nodes=nodes, edges=edges, directed=directed)\n'
        'w.attach(g)\n'
        '\n'
        'visited = [start_node]\n'
        'queue = [start_node]\n'
        'g.highlight_node(start_node, "green")\n'
        'wait(300)\n'
        '\n'
        'while len(queue) > 0:\n'
        '    u = queue[0]\n'
        '    queue = queue[1:]\n'
        '    g.highlight_node(u, "orange")\n'
        '    wait(300)\n'
        '    for v in g.neighbors(u):\n'
        '        if v not in visited:\n'
        '            g.highlight_edge(u, v, "blue")\n'
        '            visited = visited + [v]\n'
        '            queue = queue + [v]\n'
        '            g.highlight_node(v, "green")\n'
        '            wait(300)\n'
        '    g.unhighlight_node(u)\n'
        '    wait(200)\n'
    )
    default_input = {
        "nodes": [{"label": "A"}, {"label": "B"}, {"label": "C"}, {"label": "D"}],
        "edges": [{"from": 0, "to": 1}, {"from": 1, "to": 2}, {"from": 2, "to": 3}],
        "directed": False,
        "start_node": 0,
    }
    default_settings = {
        "speed_factor": 1.0,
        "layout": "kamada_kawai",
    }
    definition = _build_definition(python_code, default_input, default_settings)

    return Algorithm(
        id="bfs",
        name="Поиск в ширину (BFS)",
        display_name="Поиск в ширину (BFS)",
        category_id="graph",
        description_short="Обход графа в ширину",
        description_full="Алгоритм обхода графа, который посещает все вершины в порядке увеличения расстояния от стартовой вершины. Использует очередь.",
        complexity="O(V + E)",
        icon="bfs",
        order_index=30,
        default_input_data=default_input,
        input_schema={
            "nodes": "graph_nodes",
            "edges": "graph_edges",
            "directed": "boolean",
            "start_node": "number",
        },
        default_settings=default_settings,
        definition=definition,
        definition_python=python_code,
        definition_mode='python',
    )


# ============================================================
# Поиск в глубину (DFS)
# ============================================================

def add_dfs():
    python_code = (
        'w = Window("main")\n'
        'g = Graph(nodes=nodes, edges=edges, directed=directed)\n'
        'w.attach(g)\n'
        '\n'
        'visited = []\n'
        'stack = [start_node]\n'
        'g.highlight_node(start_node, "green")\n'
        'wait(300)\n'
        '\n'
        'while len(stack) > 0:\n'
        '    u = stack[-1]\n'
        '    stack = stack[:-1]\n'
        '    if u not in visited:\n'
        '        visited = visited + [u]\n'
        '        g.highlight_node(u, "orange")\n'
        '        wait(300)\n'
        '        for v in g.neighbors(u):\n'
        '            if v not in visited:\n'
        '                g.highlight_edge(u, v, "blue")\n'
        '                stack = stack + [v]\n'
        '                wait(300)\n'
        '    g.unhighlight_node(u)\n'
        '    wait(200)\n'
    )
    default_input = {
        "nodes": [{"label": "A"}, {"label": "B"}, {"label": "C"}, {"label": "D"}, {"label": "E"}],
        "edges": [{"from": 0, "to": 1}, {"from": 0, "to": 2}, {"from": 1, "to": 3}, {"from": 1, "to": 4}],
        "directed": False,
        "start_node": 0,
    }
    default_settings = {
        "speed_factor": 1.0,
        "layout": "kamada_kawai",
    }
    definition = _build_definition(python_code, default_input, default_settings)

    return Algorithm(
        id="dfs",
        name="Поиск в глубину (DFS)",
        display_name="Поиск в глубину (DFS)",
        category_id="graph",
        description_short="Обход графа в глубину",
        description_full="Алгоритм обхода графа, который идёт вглубь по одному пути, используя стек.",
        complexity="O(V + E)",
        icon="dfs",
        order_index=35,
        default_input_data=default_input,
        input_schema={
            "nodes": "graph_nodes",
            "edges": "graph_edges",
            "directed": "boolean",
            "start_node": "number",
        },
        default_settings=default_settings,
        definition=definition,
        definition_python=python_code,
        definition_mode='python',
    )


# ============================================================
# Максимальная сумма подотрезка (Кадане)
# ============================================================

def add_kadane():
    python_code = (
        'w = Window("main")\n'
        'v = Vector(input_array)\n'
        'w.attach(v)\n'
        '\n'
        'n = len(input_array)\n'
        'current_sum = 0\n'
        'max_sum = -1000000000\n'
        'start = 0\n'
        'end = 0\n'
        'temp_start = 0\n'
        '\n'
        'if n > 0:\n'
        '    current_sum = input_array[0]\n'
        '    max_sum = input_array[0]\n'
        '\n'
        'for i in range(1, n):\n'
        '    v.highlight(i, "yellow")\n'
        '    if current_sum + input_array[i] > input_array[i]:\n'
        '        current_sum = current_sum + input_array[i]\n'
        '    else:\n'
        '        current_sum = input_array[i]\n'
        '        temp_start = i\n'
        '    if current_sum > max_sum:\n'
        '        max_sum = current_sum\n'
        '        start = temp_start\n'
        '        end = i\n'
        '    if current_sum == max_sum:\n'
        '        for j in range(temp_start, i + 1):\n'
        '            v.highlight(j, "lightgreen")\n'
        '        wait(400)\n'
        '    for j in range(0, temp_start):\n'
        '        v.unhighlight(j)\n'
        '\n'
        'for j in range(0, n):\n'
        '    v.unhighlight(j)\n'
        'for j in range(start, end + 1):\n'
        '    v.highlight(j, "green")\n'
    )
    default_input = {
        "input_array": [-2, 1, -3, 4, -1, 2, 1, -5, 4],
    }
    default_settings = {
        "speed_factor": 1.0,
        "colors": {
            "current_window": "#FFA07A",
            "max_subarray": "#4CAF50",
        },
    }
    definition = _build_definition(python_code, default_input, default_settings)

    return Algorithm(
        id="kadane",
        name="Максимальная сумма подотрезка",
        display_name="Максимальная сумма подотрезка (Кадане)",
        category_id="search",
        description_short="Поиск подмассива с максимальной суммой",
        description_full="Алгоритм Кадане: поддерживаем текущий подотрезок. Если сумма становится меньше текущего элемента – начинаем новый отрезок.",
        complexity="O(n)",
        icon="kadane",
        order_index=40,
        default_input_data=default_input,
        input_schema={
            "input_array": "array",
        },
        default_settings=default_settings,
        definition=definition,
        definition_python=python_code,
        definition_mode='python',
    )
