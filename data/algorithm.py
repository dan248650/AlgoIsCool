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
            "edges": {
                "type": "graph_edges",
                "depends_on": "nodes",
            },
            "directed": "boolean",
            "start_node": {
                "type": "number",
                "depends_on": "nodes",
            },
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
            "edges": {
                "type": "graph_edges",
                "depends_on": "nodes",
            },
            "directed": "boolean",
            "start_node": {
                "type": "number",
                "depends_on": "nodes",
            },
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


# ============================================================
# Построение BST (двоичного дерева поиска)
# ============================================================

def add_bst_build():
    python_code = (
        'w = Window("main")\n'
        'root_id = input_array[0]\n'
        'root_node = {"id": root_id, "label": str(root_id)}\n'
        't = Tree(nodes=[root_node], edges=[], root_id=root_id, layout="hierarchical")\n'
        'w.attach(t)\n'
        't.highlight_node(root_id, "green")\n'
        'wait(300)\n'
        '\n'
        'for i in range(1, len(input_array)):\n'
        '    value = input_array[i]\n'
        '    current = root_id\n'
        '    while True:\n'
        '        t.highlight_node(current, "yellow")\n'
        '        wait(200)\n'
        '        cv = t.value_of(current)\n'
        '        children = t.children_of(current)\n'
        '        if value < cv:\n'
        '            if len(children) > 0:\n'
        '                if t.value_of(children[0]) < cv:\n'
        '                    t.unhighlight_node(current)\n'
        '                    current = children[0]\n'
        '                    continue\n'
        '            t.add_child(current, value, str(value))\n'
        '            t.highlight_node(t.children_of(current)[0], "green")\n'
        '            t.unhighlight_node(current)\n'
        '            wait(300)\n'
        '            break\n'
        '        elif value > cv:\n'
        '            if len(children) > 0:\n'
        '                last = children[-1]\n'
        '                if t.value_of(last) > cv:\n'
        '                    t.unhighlight_node(current)\n'
        '                    current = last\n'
        '                    continue\n'
        '            t.add_child(current, value, str(value))\n'
        '            t.highlight_node(t.children_of(current)[-1], "green")\n'
        '            t.unhighlight_node(current)\n'
        '            wait(300)\n'
        '            break\n'
        '        else:\n'
        '            if len(children) > 0:\n'
        '                last = children[-1]\n'
        '                if t.value_of(last) >= cv:\n'
        '                    t.unhighlight_node(current)\n'
        '                    current = last\n'
        '                    continue\n'
        '            t.add_child(current, value, str(value))\n'
        '            t.highlight_node(t.children_of(current)[-1], "green")\n'
        '            t.unhighlight_node(current)\n'
        '            wait(300)\n'
        '            break\n'
    )
    default_input = {"input_array": [50, 30, 70, 20, 40, 60, 80, 35, 45]}
    default_settings = {"speed_factor": 1.0}
    definition = _build_definition(python_code, default_input, default_settings)

    return Algorithm(
        id="bst-build",
        name="Построение BST",
        display_name="Построение двоичного дерева поиска",
        category_id="graph",
        description_short="Построение бинарного дерева поиска из массива",
        description_full="Каждый элемент массива вставляется в BST по правилу: меньше — налево, больше — направо, дубликат — направо. Дерево растёт и перестраивается автоматически.",
        complexity="O(n log n) в среднем",
        icon="tree",
        order_index=50,
        default_input_data=default_input,
        input_schema={"input_array": "array"},
        default_settings=default_settings,
        definition=definition,
        definition_python=python_code,
        definition_mode='python',
    )


# ============================================================
# Поиск в BST
# ============================================================

def add_bst_search():
    python_code = (
        'w = Window("main")\n'
        'root_id = input_array[0]\n'
        'root_node = {"id": root_id, "label": str(root_id)}\n'
        't = Tree(nodes=[root_node], edges=[], root_id=root_id, layout="hierarchical")\n'
        'w.attach(t)\n'
        '\n'
        '# Мгновенное построение BST\n'
        'for i in range(1, len(input_array)):\n'
        '    value = input_array[i]\n'
        '    current = root_id\n'
        '    while True:\n'
        '        cv = t.value_of(current)\n'
        '        children = t.children_of(current)\n'
        '        if value < cv:\n'
        '            if len(children) > 0:\n'
        '                if t.value_of(children[0]) < cv:\n'
        '                    current = children[0]\n'
        '                    continue\n'
        '            t.add_child(current, value, str(value))\n'
        '            break\n'
        '        elif value > cv:\n'
        '            if len(children) > 0:\n'
        '                if t.value_of(children[-1]) > cv:\n'
        '                    current = children[-1]\n'
        '                    continue\n'
        '            t.add_child(current, value, str(value))\n'
        '            break\n'
        '        else:\n'
        '            if len(children) > 0:\n'
        '                if t.value_of(children[-1]) >= cv:\n'
        '                    current = children[-1]\n'
        '                    continue\n'
        '            t.add_child(current, value, str(value))\n'
        '            break\n'
        '\n'
        'wait(300)\n'
        '\n'
        '# Поиск target с подсветкой пути\n'
        'current = root_id\n'
        'found = False\n'
        'while True:\n'
        '    t.highlight_node(current, "yellow")\n'
        '    wait(300)\n'
        '    if t.value_of(current) == target:\n'
        '        t.highlight_path(root_id, current, "green")\n'
        '        wait(600)\n'
        '        found = True\n'
        '        break\n'
        '    cv = t.value_of(current)\n'
        '    children = t.children_of(current)\n'
        '    if target < cv:\n'
        '        if len(children) > 0:\n'
        '            if t.value_of(children[0]) < cv:\n'
        '                t.unhighlight_node(current)\n'
        '                current = children[0]\n'
        '                continue\n'
        '        break\n'
        '    else:\n'
        '        if len(children) > 0:\n'
        '            if t.value_of(children[-1]) >= cv:\n'
        '                t.unhighlight_node(current)\n'
        '                current = children[-1]\n'
        '                continue\n'
        '        break\n'
        '\n'
        'if not found:\n'
        '    t.highlight_node(current, "red")\n'
        '    wait(600)\n'
    )
    default_input = {
        "input_array": [50, 30, 70, 20, 40, 60, 80],
        "target": 40,
    }
    default_settings = {"speed_factor": 1.0}
    definition = _build_definition(python_code, default_input, default_settings)

    return Algorithm(
        id="bst-search",
        name="Поиск в BST",
        display_name="Поиск в двоичном дереве поиска",
        category_id="graph",
        description_short="Поиск элемента в BST с подсветкой пути",
        description_full="На каждом шаге сравниваем значение с текущим узлом: идём влево, вправо или останавливаемся. При успехе подсвечивается весь путь от корня до найденного узла.",
        complexity="O(log n) в среднем",
        icon="tree",
        order_index=55,
        default_input_data=default_input,
        input_schema={"input_array": "array", "target": "number"},
        default_settings=default_settings,
        definition=definition,
        definition_python=python_code,
        definition_mode='python',
    )


# ============================================================
# Обход дерева в ширину
# ============================================================

def add_tree_bfs():
    python_code = (
        'w = Window("main")\n'
        't = Tree(nodes=nodes, edges=edges, root_id=start_node,\n'
        '         layout="hierarchical")\n'
        'w.attach(t)\n'
        '\n'
        'visited = [start_node]\n'
        'queue = [start_node]\n'
        't.highlight_node(start_node, "green")\n'
        'wait(300)\n'
        '\n'
        'while len(queue) > 0:\n'
        '    u = queue[0]\n'
        '    queue = queue[1:]\n'
        '    t.highlight_node(u, "orange")\n'
        '    wait(300)\n'
        '    for v in t.neighbors(u):\n'
        '        if v not in visited:\n'
        '            t.highlight_edge(u, v, "blue")\n'
        '            visited = visited + [v]\n'
        '            queue = queue + [v]\n'
        '            t.highlight_node(v, "green")\n'
        '            wait(300)\n'
        '    t.unhighlight_node(u)\n'
        '    wait(200)\n'
    )
    default_input = {
        "nodes": [
            {"label": "1"},
            {"label": "2"},
            {"label": "3"},
            {"label": "4"},
            {"label": "5"},
        ],
        "edges": [
            {"from": 0, "to": 1},
            {"from": 0, "to": 2},
            {"from": 1, "to": 3},
            {"from": 1, "to": 4},
        ],
        "start_node": 0,
    }
    default_settings = {"speed_factor": 1.0}
    definition = _build_definition(python_code, default_input, default_settings)

    return Algorithm(
        id="tree-bfs",
        name="Обход дерева в ширину",
        display_name="Обход дерева в ширину (BFS по дереву)",
        category_id="graph",
        description_short="Обход дерева по уровням",
        description_full="BFS по иерархическому дереву: волна от корня вниз. Использует neighbors, который для дерева возвращает только детей.",
        complexity="O(V)",
        icon="tree",
        order_index=60,
        default_input_data=default_input,
        input_schema={
            "nodes": "graph_nodes",
            "edges": {
                "type": "graph_edges",
                "depends_on": "nodes",
                "constraints": {"no_cycles": True, "connected": True},
            },
            "start_node": {
                "type": "number",
                "depends_on": "nodes",
            },
        },
        default_settings=default_settings,
        definition=definition,
        definition_python=python_code,
        definition_mode='python',
    )


def add_prefix_sums():
    python_code = (
        'w1 = Window("input")\n'
        'w2 = Window("prefix")\n'
        'arr = Vector(input_array)\n'
        'pre = Vector([])\n'
        'w1.attach(arr)\n'
        'w2.attach(pre)\n'
        'wait(500)\n'
        '\n'
        'total = 0\n'
        'for i in range(len(input_array)):\n'
        '    arr.highlight(i, "yellow")\n'
        '    wait(400)\n'
        '    total = total + input_array[i]\n'
        '    pre.append(total)\n'
        '    pre.highlight(i, "green")\n'
        '    arr.unhighlight(i)\n'
        '    wait(300)\n'
        '    pre.unhighlight(i)\n'
    )
    default_input = {"input_array": [1, 3, 2, 5, 4, 6, 2]}
    default_settings = {"speed_factor": 1.0}
    definition = _build_definition(python_code, default_input, default_settings)

    return Algorithm(
        id="prefix-sums",
        name="Prefix sums",
        display_name="Префиксные суммы",
        category_id="search",
        description_short="Растущий второй массив с накопленными суммами",
        description_full="Слева — входной массив, справа — растущий массив префиксных сумм. Каждая новая ячейка = сумма всех элементов от начала до текущего.",
        complexity="O(n)",
        icon="prefix",
        order_index=70,
        default_input_data=default_input,
        input_schema={
            "input_array": {
                "type": "array",
                "constraints": {"min_length": 3, "max_length": 12},
            },
        },
        default_settings=default_settings,
        definition=definition,
        definition_python=python_code,
        definition_mode='python',
    )


def add_suffix_sums():
    python_code = (
        'w1 = Window("input")\n'
        'w2 = Window("suffix")\n'
        'arr = Vector(input_array)\n'
        'suf = Vector([])\n'
        'w1.attach(arr)\n'
        'w2.attach(suf)\n'
        'wait(500)\n'
        '\n'
        'total = 0\n'
        'n = len(input_array)\n'
        'for k in range(n):\n'
        '    i = n - 1 - k\n'
        '    arr.highlight(i, "yellow")\n'
        '    wait(400)\n'
        '    total = total + input_array[i]\n'
        '    suf.insert(0, total)\n'
        '    suf.highlight(0, "cyan")\n'
        '    arr.unhighlight(i)\n'
        '    wait(300)\n'
        '    suf.unhighlight(0)\n'
    )
    default_input = {"input_array": [1, 3, 2, 5, 4, 6, 2]}
    default_settings = {"speed_factor": 1.0}
    definition = _build_definition(python_code, default_input, default_settings)

    return Algorithm(
        id="suffix-sums",
        name="Suffix sums",
        display_name="Суффиксные суммы",
        category_id="search",
        description_short="Растущий второй массив с суффиксными суммами",
        description_full="Слева — входной массив, справа — растущий массив суффиксных сумм. Обрабатываем справа налево; каждая новая ячейка = сумма всех элементов от текущего до конца.",
        complexity="O(n)",
        icon="suffix",
        order_index=75,
        default_input_data=default_input,
        input_schema={
            "input_array": {
                "type": "array",
                "constraints": {"min_length": 3, "max_length": 12},
            },
        },
        default_settings=default_settings,
        definition=definition,
        definition_python=python_code,
        definition_mode='python',
    )


def add_nearest_smaller_left():
    python_code = (
        'w1 = Window("input")\n'
        'w2 = Window("stack")\n'
        'w3 = Window("result")\n'
        'arr = Vector(input_array)\n'
        'st = Vector([])\n'
        'res = Vector([])\n'
        'w1.attach(arr)\n'
        'w2.attach(st)\n'
        'w3.attach(res)\n'
        'wait(500)\n'
        '\n'
        'for i in range(len(input_array)):\n'
        '    arr.highlight(i, "yellow")\n'
        '    wait(400)\n'
        '    while st.size() > 0:\n'
        '        top = st.value_at(st.size() - 1)\n'
        '        if input_array[top] >= input_array[i]:\n'
        '            st.pop()\n'
        '            wait(200)\n'
        '            continue\n'
        '        break\n'
        '    if st.size() == 0:\n'
        '        res.append(-1)\n'
        '        res.highlight(i, "red")\n'
        '    else:\n'
        '        top = st.value_at(st.size() - 1)\n'
        '        res.append(top)\n'
        '        res.highlight(i, "green")\n'
        '    st.append(i)\n'
        '    arr.unhighlight(i)\n'
        '    wait(300)\n'
        '    res.unhighlight(i)\n'
    )
    default_input = {"input_array": [3, 1, 4, 1, 5, 9, 2, 6]}
    default_settings = {"speed_factor": 1.0}
    definition = _build_definition(python_code, default_input, default_settings)

    return Algorithm(
        id="nearest-smaller-left",
        name="Nearest smaller to left",
        display_name="Ближайший меньший слева",
        category_id="search",
        description_short="Монотонный стек: для каждого элемента найти ближайший меньший слева",
        description_full="Для каждого arr[i] ищем индекс ближайшего j < i с arr[j] < arr[i] (или -1). Стек (второе окно) хранит индексы возрастающих элементов; перед добавлением нового чистим от элементов >= arr[i]. Результат (третье окно) — ответы по каждому индексу.",
        complexity="O(n)",
        icon="stack",
        order_index=80,
        default_input_data=default_input,
        input_schema={
            "input_array": {
                "type": "array",
                "constraints": {"min_length": 3, "max_length": 12},
            },
        },
        default_settings=default_settings,
        definition=definition,
        definition_python=python_code,
        definition_mode='python',
    )


def add_boyer_moore_majority():
    python_code = (
        'w1 = Window("array")\n'
        'w2 = Window("state")\n'
        'arr = Vector(input_array)\n'
        'state = Vector([0, 0])\n'
        'w1.attach(arr)\n'
        'w2.attach(state)\n'
        'wait(500)\n'
        '\n'
        'for i in range(len(input_array)):\n'
        '    arr.highlight(i, "yellow")\n'
        '    wait(300)\n'
        '    cand = state.value_at(0)\n'
        '    cnt = state.value_at(1)\n'
        '    if cnt == 0:\n'
        '        state.set(0, input_array[i])\n'
        '        state.set(1, 1)\n'
        '    elif input_array[i] == cand:\n'
        '        state.set(1, cnt + 1)\n'
        '    else:\n'
        '        state.set(1, cnt - 1)\n'
        '    arr.unhighlight(i)\n'
        '    wait(200)\n'
        '\n'
        'cand = state.value_at(0)\n'
        'final_count = 0\n'
        'for i in range(len(input_array)):\n'
        '    if input_array[i] == cand:\n'
        '        final_count = final_count + 1\n'
        '\n'
        'if final_count * 2 > len(input_array):\n'
        '    for i in range(len(input_array)):\n'
        '        if input_array[i] == cand:\n'
        '            arr.highlight(i, "green")\n'
        'else:\n'
        '    for i in range(len(input_array)):\n'
        '        if input_array[i] == cand:\n'
        '            arr.highlight(i, "red")\n'
        'wait(1000)\n'
    )
    default_input = {"input_array": [2, 2, 1, 1, 1, 2, 2]}
    default_settings = {"speed_factor": 1.0}
    definition = _build_definition(python_code, default_input, default_settings)

    return Algorithm(
        id="boyer-moore-majority",
        name="Boyer-Moore majority vote",
        display_name="Поиск мажоритарного элемента (Boyer-Moore)",
        category_id="search",
        description_short="Кандидат + счётчик: большинство найдено за один проход",
        description_full="Классический трюк: держим кандидата и счётчик. При cnt = 0 меняем кандидата; при совпадении "
                         "cnt+1, иначе cnt-1. В конце проверяем, действительно ли кандидат — мажоритарный ("
                         "встречается больше n/2 раз). Второе окно показывает текущего кандидата и счётчик.",
        complexity="O(n)",
        icon="vote",
        order_index=85,
        default_input_data=default_input,
        input_schema={
            "input_array": {
                "type": "array",
                "constraints": {"min_length": 3, "max_length": 13},
            },
        },
        default_settings=default_settings,
        definition=definition,
        definition_python=python_code,
        definition_mode='python',
    )


def add_trapping_rain_water():
    python_code = (
        'w1 = Window("input")\n'
        'w2 = Window("water")\n'
        'w3 = Window("left_max")\n'
        'w4 = Window("right_max")\n'
        'arr = Vector(input_array)\n'
        'lmax = Vector([])\n'
        'rmax = Vector([])\n'
        'wat = Vector([])\n'
        'w1.attach(arr)\n'
        'w2.attach(wat)\n'
        'w3.attach(lmax)\n'
        'w4.attach(rmax)\n'
        'wait(500)\n'
        '\n'
        'n = len(input_array)\n'
        '\n'
        '# Проход 1: left_max[i] = max(input_array[0..i])\n'
        'cur = 0\n'
        'for i in range(n):\n'
        '    arr.highlight(i, "yellow")\n'
        '    wait(300)\n'
        '    if input_array[i] > cur:\n'
        '        cur = input_array[i]\n'
        '    lmax.append(cur)\n'
        '    lmax.highlight(i, "cyan")\n'
        '    arr.unhighlight(i)\n'
        '    wait(200)\n'
        '    lmax.unhighlight(i)\n'
        '\n'
        '# Проход 2: right_max[i] = max(input_array[i..n-1])\n'
        '# Идём справа налево; каждый новый элемент вставляем в начало.\n'
        'cur = 0\n'
        'for k in range(n):\n'
        '    i = n - 1 - k\n'
        '    arr.highlight(i, "orange")\n'
        '    wait(300)\n'
        '    if input_array[i] > cur:\n'
        '        cur = input_array[i]\n'
        '    rmax.insert(0, cur)\n'
        '    rmax.highlight(0, "cyan")\n'
        '    arr.unhighlight(i)\n'
        '    wait(200)\n'
        '    rmax.unhighlight(0)\n'
        '\n'
        '# Проход 3: water[i] = min(left_max[i], right_max[i]) - input_array[i]\n'
        'total = 0\n'
        'for i in range(n):\n'
        '    arr.highlight(i, "yellow")\n'
        '    wait(300)\n'
        '    lv = lmax.value_at(i)\n'
        '    rv = rmax.value_at(i)\n'
        '    if lv < rv:\n'
        '        m = lv\n'
        '    else:\n'
        '        m = rv\n'
        '    w_i = m - input_array[i]\n'
        '    if w_i < 0:\n'
        '        w_i = 0\n'
        '    total = total + w_i\n'
        '    wat.append(w_i)\n'
        '    if w_i > 0:\n'
        '        arr.highlight(i, "cyan")\n'
        '    wat.highlight(i, "green")\n'
        '    wait(300)\n'
        '    wat.unhighlight(i)\n'
        '    if w_i == 0:\n'
        '        arr.unhighlight(i)\n'
        '\n'
        'wait(1000)\n'
    )
    default_input = {"input_array": [0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]}
    default_settings = {"speed_factor": 1.0}
    definition = _build_definition(python_code, default_input, default_settings)

    return Algorithm(
        id="trapping-rain-water",
        name="Trapping rain water",
        display_name="Сбор дождевой воды",
        category_id="search",
        description_short="Три прохода: left_max, right_max, water",
        description_full="Проход 1: для каждого i считаем max слева. Проход 2: для каждого i считаем max справа. Проход 3: water[i] = min(left_max[i], right_max[i]) - height[i].",
        complexity="O(n)",
        icon="water",
        order_index=90,
        default_input_data=default_input,
        input_schema={
            "input_array": {
                "type": "array",
                "constraints": {"min_length": 3, "max_length": 12, "min_value": 0},
            },
        },
        default_settings=default_settings,
        definition=definition,
        definition_python=python_code,
        definition_mode='python',
    )
