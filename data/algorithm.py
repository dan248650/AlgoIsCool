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


def add_prefix_function():
    python_code = (
        'w = Window("main")\n'
        's = Vector(input_string)\n'
        'pi = Vector([])\n'
        'w.attach(s)\n'
        'w.attach(pi)\n'
        'n = len(input_string)\n'
        'for k in range(n):\n'
        '    pi.append(0)\n'
        'wait(500)\n'
        '\n'
        'for i in range(1, n):\n'
        '    s.highlight(i, "yellow")\n'
        '    pi.highlight(i - 1, "cyan")\n'
        '    wait(400)\n'
        '    j = pi.value_at(i - 1)\n'
        '\n'
        '    while j > 0:\n'
        '        s.highlight(j, "orange")\n'
        '        wait(300)\n'
        '        if s.value_at(i) == s.value_at(j):\n'
        '            break\n'
        '        s.highlight(i, "red")\n'
        '        s.highlight(j, "red")\n'
        '        wait(300)\n'
        '        s.unhighlight(j)\n'
        '        s.highlight(i, "yellow")\n'
        '        pi.highlight(j - 1, "red")\n'
        '        wait(300)\n'
        '        pi.unhighlight(j - 1)\n'
        '        j = pi.value_at(j - 1)\n'
        '    pi.unhighlight(i - 1)\n'
        '\n'
        '    s.highlight(j, "orange")\n'
        '    wait(200)\n'
        '    if s.value_at(i) == s.value_at(j):\n'
        '        s.highlight(i, "green")\n'
        '        s.highlight(j, "green")\n'
        '        wait(400)\n'
        '        s.unhighlight(j)\n'
        '        j = j + 1\n'
        '    else:\n'
        '        s.highlight(i, "red")\n'
        '        s.highlight(j, "red")\n'
        '        wait(300)\n'
        '        s.unhighlight(j)\n'
        '    s.unhighlight(i)\n'
        '\n'
        '    pi.set(i, j)\n'
        '    pi.highlight(i, "green")\n'
        '    wait(400)\n'
        '    pi.unhighlight(i)\n'
    )
    default_input = {"input_string": "abacaba"}
    default_settings = {"speed_factor": 1.0}
    definition = _build_definition(python_code, default_input, default_settings)

    return Algorithm(
        id="prefix-function",
        name="Prefix function",
        display_name="Prefix-функция (KMP)",
        category_id="search",
        description_short="Массив длин наибольших собственных префиксов-суффиксов",
        description_full="pi[i] — длина наибольшего префикса строки s, который одновременно является суффиксом подстроки s[0..i]. Строится за O(n) с использованием уже посчитанных pi.",
        complexity="O(n)",
        icon="π",
        order_index=100,
        default_input_data=default_input,
        input_schema={
            "input_string": {"type": "string",
                             "constraints": {"min_length": 5, "max_length": 12, "alphabet": "ab"}}
        },
        default_settings=default_settings,
        definition=definition,
        definition_python=python_code,
        definition_mode='python',
    )


def add_z_function():
    python_code = (
        'w = Window("main")\n'
        's = Vector(input_string)\n'
        'z = Vector([])\n'
        'w.attach(s)\n'
        'w.attach(z)\n'
        'n = len(input_string)\n'
        'for k in range(n):\n'
        '    z.append(0)\n'
        'wait(500)\n'
        '\n'
        'l = 0\n'
        'r = 0\n'
        'for i in range(1, n):\n'
        '    s.highlight(i, "yellow")\n'
        '    wait(400)\n'
        '\n'
        '    if i < r:\n'
        '        sym = i - l\n'
        '        s.highlight(sym, "cyan")\n'
        '        z.highlight(sym, "cyan")\n'
        '        wait(300)\n'
        '        zi = z.value_at(sym)\n'
        '        if r - i < zi:\n'
        '            zi = r - i\n'
        '        z.set(i, zi)\n'
        '        z.highlight(i, "orange")\n'
        '        wait(300)\n'
        '        s.unhighlight(sym)\n'
        '        z.unhighlight(sym)\n'
        '        z.unhighlight(i)\n'
        '\n'
        '    while i + z.value_at(i) < n:\n'
        '        left = z.value_at(i)\n'
        '        s.highlight(left, "orange")\n'
        '        s.highlight(i + left, "orange")\n'
        '        wait(300)\n'
        '        if s.value_at(left) != s.value_at(i + left):\n'
        '            s.highlight(left, "red")\n'
        '            s.highlight(i + left, "red")\n'
        '            wait(300)\n'
        '            s.unhighlight(left)\n'
        '            s.unhighlight(i + left)\n'
        '            break\n'
        '        s.highlight(left, "green")\n'
        '        s.highlight(i + left, "green")\n'
        '        wait(300)\n'
        '        s.unhighlight(left)\n'
        '        s.unhighlight(i + left)\n'
        '        z.set(i, left + 1)\n'
        '\n'
        '    if i + z.value_at(i) > r:\n'
        '        l = i\n'
        '        r = i + z.value_at(i)\n'
        '\n'
        '    z.highlight(i, "green")\n'
        '    s.unhighlight(i)\n'
        '    wait(400)\n'
        '    z.unhighlight(i)\n'
    )
    default_input = {"input_string": "abacaba"}
    default_settings = {"speed_factor": 1.0}
    definition = _build_definition(python_code, default_input, default_settings)

    return Algorithm(
        id="z-function",
        name="Z function",
        display_name="Z-функция",
        category_id="search",
        description_short="Z[i] — длина наибольшего общего префикса строки и её суффикса от i",
        description_full="Z[i] — длина наибольшего общего префикса строки s и её суффикса s[i..n-1]. Строится за O(n) через «Z-блок» [l, r).",
        complexity="O(n)",
        icon="Z",
        order_index=101,
        default_input_data=default_input,
        input_schema={
            "input_string": {"type": "string",
                             "constraints": {"min_length": 5, "max_length": 12, "alphabet": "ab"}}
        },
        default_settings=default_settings,
        definition=definition,
        definition_python=python_code,
        definition_mode='python',
    )


def add_manacher():
    python_code = (
        'w = Window("main")\n'
        's = Vector(input_string)\n'
        'd1 = Vector([])\n'
        'w.attach(s)\n'
        'w.attach(d1)\n'
        'n = len(input_string)\n'
        'for k in range(n):\n'
        '    d1.append(0)\n'
        'wait(500)\n'
        '\n'
        'l = 0\n'
        'r = -1\n'
        'for i in range(n):\n'
        '    s.highlight(i, "yellow")\n'
        '    wait(400)\n'
        '\n'
        '    if i > r:\n'
        '        k = 1\n'
        '    else:\n'
        '        sym = l + r - i\n'
        '        s.highlight(sym, "cyan")\n'
        '        d1.highlight(sym, "cyan")\n'
        '        wait(300)\n'
        '        k = d1.value_at(sym)\n'
        '        if r - i + 1 < k:\n'
        '            k = r - i + 1\n'
        '        s.unhighlight(sym)\n'
        '        d1.unhighlight(sym)\n'
        '\n'
        '    while i + k < n and i - k >= 0:\n'
        '        s.highlight(i - k, "orange")\n'
        '        s.highlight(i + k, "orange")\n'
        '        wait(300)\n'
        '        if s.value_at(i - k) != s.value_at(i + k):\n'
        '            s.highlight(i - k, "red")\n'
        '            s.highlight(i + k, "red")\n'
        '            wait(300)\n'
        '            s.unhighlight(i - k)\n'
        '            s.unhighlight(i + k)\n'
        '            break\n'
        '        s.highlight(i - k, "green")\n'
        '        s.highlight(i + k, "green")\n'
        '        wait(300)\n'
        '        s.unhighlight(i - k)\n'
        '        s.unhighlight(i + k)\n'
        '        k = k + 1\n'
        '\n'
        '    d1.set(i, k)\n'
        '    if i + k - 1 > r:\n'
        '        l = i - k + 1\n'
        '        r = i + k - 1\n'
        '    d1.highlight(i, "green")\n'
        '    s.unhighlight(i)\n'
        '    wait(400)\n'
        '    d1.unhighlight(i)\n'
    )
    default_input = {"input_string": "abacabadabacaba"}
    default_settings = {"speed_factor": 1.0}
    definition = _build_definition(python_code, default_input, default_settings)

    return Algorithm(
        id="manacher",
        name="Manacher",
        display_name="Алгоритм Манакера",
        category_id="search",
        description_short="Радиусы всех нечётных палиндромов за линейное время",
        description_full="d1[i] — количество нечётных палиндромов с центром в i. Использует уже известный блок [l, r) самого правого палиндрома для ускорения.",
        complexity="O(n)",
        icon="◯",
        order_index=102,
        default_input_data=default_input,
        input_schema={
            "input_string": {"type": "string",
                             "constraints": {"min_length": 5, "max_length": 15, "alphabet": "abcd"}}
        },
        default_settings=default_settings,
        definition=definition,
        definition_python=python_code,
        definition_mode='python',
    )


def add_kmp():
    python_code = (
        'w = Window("main")\n'
        'text = Vector(input_text)\n'
        'pattern = Vector(input_pattern)\n'
        'pi = Vector([])\n'
        'w.attach(text)\n'
        'w.attach(pattern)\n'
        'w.attach(pi)\n'
        'n = len(input_text)\n'
        'm = len(input_pattern)\n'
        'for k in range(m):\n'
        '    pi.append(0)\n'
        'wait(400)\n'
        '\n'
        'for i in range(1, m):\n'
        '    pattern.highlight(i, "yellow")\n'
        '    pi.highlight(i - 1, "cyan")\n'
        '    wait(300)\n'
        '    j = pi.value_at(i - 1)\n'
        '    while j > 0:\n'
        '        pattern.highlight(j, "orange")\n'
        '        wait(200)\n'
        '        if pattern.value_at(i) == pattern.value_at(j):\n'
        '            pattern.highlight(i, "green")\n'
        '            pattern.highlight(j, "green")\n'
        '            wait(300)\n'
        '            pattern.unhighlight(j)\n'
        '            break\n'
        '        pattern.highlight(i, "red")\n'
        '        pattern.highlight(j, "red")\n'
        '        wait(200)\n'
        '        pattern.unhighlight(j)\n'
        '        pattern.highlight(i, "yellow")\n'
        '        pi.highlight(j - 1, "red")\n'
        '        wait(200)\n'
        '        pi.unhighlight(j - 1)\n'
        '        j = pi.value_at(j - 1)\n'
        '    pi.unhighlight(i - 1)\n'
        '    if pattern.value_at(i) == pattern.value_at(j):\n'
        '        j = j + 1\n'
        '    pi.set(i, j)\n'
        '    pi.highlight(i, "green")\n'
        '    pattern.unhighlight(i)\n'
        '    wait(300)\n'
        '    pi.unhighlight(i)\n'
        '\n'
        'j = 0\n'
        'for i in range(n):\n'
        '    text.highlight(i, "yellow")\n'
        '    wait(250)\n'
        '    while j > 0:\n'
        '        if text.value_at(i) == pattern.value_at(j):\n'
        '            break\n'
        '        for s2 in range(m):\n'
        '            pattern.unhighlight(s2)\n'
        '        pattern.highlight(j - 1, "red")\n'
        '        pi.highlight(j - 1, "red")\n'
        '        wait(300)\n'
        '        pattern.unhighlight(j - 1)\n'
        '        pi.unhighlight(j - 1)\n'
        '        j = pi.value_at(j - 1)\n'
        '        for s2 in range(j):\n'
        '            pattern.highlight(s2, "green")\n'
        '        wait(200)\n'
        '    if text.value_at(i) == pattern.value_at(j):\n'
        '        pattern.highlight(j, "green")\n'
        '        j = j + 1\n'
        '    else:\n'
        '        for s2 in range(m):\n'
        '            pattern.unhighlight(s2)\n'
        '    text.unhighlight(i)\n'
        '    if j == m:\n'
        '        for s2 in range(m):\n'
        '            text.highlight(i - m + 1 + s2, "green")\n'
        '        wait(500)\n'
        '        j = pi.value_at(m - 1)\n'
        '        for s2 in range(m):\n'
        '            pattern.unhighlight(s2)\n'
        '        for s2 in range(j):\n'
        '            pattern.highlight(s2, "green")\n'
        '    wait(150)\n'
        '\n'
        'for s2 in range(m):\n'
        '    pattern.unhighlight(s2)\n'
    )
    default_input = {"input_text": "abcabcabd", "input_pattern": "abcab"}
    default_settings = {"speed_factor": 1.0}
    definition = _build_definition(python_code, default_input, default_settings)

    return Algorithm(
        id="kmp",
        name="KMP",
        display_name="Поиск подстроки (KMP)",
        category_id="search",
        description_short="Поиск подстроки через prefix-функцию паттерна",
        description_full="Сначала строится pi-функция для паттерна. Затем паттерн «скользит» по тексту: при несовпадении j откатывается по pi, а не на начало. Три структуры: text, pattern, pi.",
        complexity="O(n + m)",
        icon="KMP",
        order_index=103,
        default_input_data=default_input,
        input_schema={
            "input_text": {"type": "string",
                           "constraints": {"min_length": 8, "max_length": 14, "alphabet": "abcd"}},
            "input_pattern": {"type": "string",
                              "constraints": {"min_length": 3, "max_length": 6, "alphabet": "abcd"}}
        },
        default_settings=default_settings,
        definition=definition,
        definition_python=python_code,
        definition_mode='python',
    )


def add_boyer_moore():
    python_code = (
        'w = Window("main")\n'
        'text = Vector(input_text)\n'
        'pattern = Vector(input_pattern)\n'
        'bc_keys = Vector([])\n'
        'bc_vals = Vector([])\n'
        'w.attach(text)\n'
        'w.attach(pattern)\n'
        'w.attach(bc_keys)\n'
        'w.attach(bc_vals)\n'
        'n = len(input_text)\n'
        'm = len(input_pattern)\n'
        'wait(400)\n'
        '\n'
        '# Фаза 1: bad_char таблица\n'
        'for i in range(m):\n'
        '    pattern.highlight(i, "yellow")\n'
        '    wait(300)\n'
        '    ch = pattern.value_at(i)\n'
        '    found = -1\n'
        '    for k in range(bc_keys.size()):\n'
        '        bc_keys.highlight(k, "cyan")\n'
        '        bc_vals.highlight(k, "cyan")\n'
        '        wait(200)\n'
        '        if bc_keys.value_at(k) == ch:\n'
        '            found = k\n'
        '            bc_keys.unhighlight(k)\n'
        '            bc_vals.unhighlight(k)\n'
        '            break\n'
        '        bc_keys.unhighlight(k)\n'
        '        bc_vals.unhighlight(k)\n'
        '    if found == -1:\n'
        '        bc_keys.append(ch)\n'
        '        bc_vals.append(i)\n'
        '        bc_keys.highlight(bc_keys.size() - 1, "green")\n'
        '        bc_vals.highlight(bc_vals.size() - 1, "green")\n'
        '        wait(300)\n'
        '    else:\n'
        '        bc_vals.set(found, i)\n'
        '        bc_vals.highlight(found, "green")\n'
        '        wait(300)\n'
        '    # Сброс всей подсветки таблицы после итерации —\n'
        '    # иначе cyan/зелёный копится и остаётся до конца алгоритма.\n'
        '    for k2 in range(bc_keys.size()):\n'
        '        bc_keys.unhighlight(k2)\n'
        '        bc_vals.unhighlight(k2)\n'
        '    pattern.unhighlight(i)\n'
        '\n'
        '# Фаза 2: поиск\n'
        'i = 0\n'
        'while i <= n - m:\n'
        '    j = m - 1\n'
        '    while j >= 0:\n'
        '        text.highlight(i + j, "yellow")\n'
        '        pattern.highlight(j, "yellow")\n'
        '        wait(300)\n'
        '        if text.value_at(i + j) != pattern.value_at(j):\n'
        '            text.highlight(i + j, "red")\n'
        '            pattern.highlight(j, "red")\n'
        '            wait(400)\n'
        '            text.unhighlight(i + j)\n'
        '            pattern.unhighlight(j)\n'
        '            break\n'
        '        text.unhighlight(i + j)\n'
        '        pattern.unhighlight(j)\n'
        '        j = j - 1\n'
        '    if j < 0:\n'
        '        for s2 in range(m):\n'
        '            text.highlight(i + s2, "green")\n'
        '        wait(500)\n'
        '        i = i + 1\n'
        '    else:\n'
        '        c = text.value_at(i + j)\n'
        '        found = -1\n'
        '        for k in range(bc_keys.size()):\n'
        '            bc_keys.highlight(k, "cyan")\n'
        '            wait(150)\n'
        '            if bc_keys.value_at(k) == c:\n'
        '                found = k\n'
        '                bc_vals.highlight(k, "cyan")\n'
        '                wait(300)\n'
        '                bc_keys.unhighlight(k)\n'
        '                bc_vals.unhighlight(k)\n'
        '                break\n'
        '            bc_keys.unhighlight(k)\n'
        '        if found == -1:\n'
        '            shift = j + 1\n'
        '        else:\n'
        '            shift = j - bc_vals.value_at(found)\n'
        '        if shift < 1:\n'
        '            shift = 1\n'
        '        i = i + shift\n'
        '        wait(300)\n'
    )
    default_input = {"input_text": "abcabcabd", "input_pattern": "abcab"}
    default_settings = {"speed_factor": 1.0}
    definition = _build_definition(python_code, default_input, default_settings)

    return Algorithm(
        id="boyer-moore",
        name="Boyer-Moore",
        display_name="Поиск подстроки (Boyer-Moore)",
        category_id="search",
        description_short="Поиск подстроки через bad-character эвристику",
        description_full="Сравнение с конца паттерна. При несовпадении символ text[i+j] ищется в таблице bad_char (последняя позиция в паттерне); паттерн сдвигается на j − bc[c] (или j+1, если символа нет). Четыре структуры: text, pattern, bc_keys, bc_vals.",
        complexity="O(n·m) худший, O(n/m) средний",
        icon="BM",
        order_index=104,
        default_input_data=default_input,
        input_schema={
            "input_text": {"type": "string",
                           "constraints": {"min_length": 8, "max_length": 14, "alphabet": "abcd"}},
            "input_pattern": {"type": "string",
                              "constraints": {"min_length": 3, "max_length": 6, "alphabet": "abcd"}}
        },
        default_settings=default_settings,
        definition=definition,
        definition_python=python_code,
        definition_mode='python',
    )


def add_lis():
    python_code = (
        'w = Window("main")\n'
        'arr = Vector(input_array)\n'
        'dp = Vector([])\n'
        'w.attach(arr)\n'
        'w.attach(dp)\n'
        'n = len(input_array)\n'
        'for k in range(n):\n'
        '    dp.append(1)\n'
        'wait(500)\n'
        '\n'
        'for i in range(0, n):\n'
        '    arr.highlight(i, "yellow")\n'
        '    dp.highlight(i, "yellow")\n'
        '    wait(300)\n'
        '    best = 0\n'
        '    for j in range(0, i):\n'
        '        arr.highlight(j, "orange")\n'
        '        dp.highlight(j, "cyan")\n'
        '        wait(200)\n'
        '        if input_array[j] < input_array[i]:\n'
        '            arr.highlight(j, "green")\n'
        '            if dp.value_at(j) > best:\n'
        '                best = dp.value_at(j)\n'
        '        else:\n'
        '            arr.highlight(j, "red")\n'
        '        wait(200)\n'
        '        arr.unhighlight(j)\n'
        '        dp.unhighlight(j)\n'
        '    dp.set(i, best + 1)\n'
        '    dp.highlight(i, "green")\n'
        '    arr.unhighlight(i)\n'
        '    wait(300)\n'
        '    dp.unhighlight(i)\n'
    )
    default_input = {"input_array": [10, 9, 2, 5, 3, 7, 27, 18]}
    default_settings = {"speed_factor": 1.0}
    definition = _build_definition(python_code, default_input, default_settings)

    return Algorithm(
        id="lis",
        name="Longest Increasing Subsequence",
        display_name="Наибольшая возрастающая подпоследовательность (LIS)",
        category_id="search",
        description_short="dp[i] = 1 + max(dp[j] : j<i, a[j]<a[i])",
        description_full="Для каждого i проходим по всем j < i, где input_array[j] < input_array[i]. dp[i] — наибольшая длина возрастающей подпоследовательности, заканчивающейся на i. Ответ = max(dp).",
        complexity="O(n²)",
        icon="LIS",
        order_index=110,
        default_input_data=default_input,
        input_schema={
            "input_array": {"type": "array", "constraints": {
                "min_length": 5, "max_length": 9, "min_value": 1, "max_value": 30
            }}
        },
        default_settings=default_settings,
        definition=definition,
        definition_python=python_code,
        definition_mode='python',
    )


def add_coin_change():
    python_code = (
        'w = Window("main")\n'
        'coins = Vector(input_coins)\n'
        'dp = Vector([])\n'
        'w.attach(coins)\n'
        'w.attach(dp)\n'
        'n = len(input_coins)\n'
        'for k in range(amount + 1):\n'
        '    if k == 0:\n'
        '        dp.append(0)\n'
        '    else:\n'
        '        dp.append(-1)\n'
        'wait(500)\n'
        '\n'
        'for s in range(1, amount + 1):\n'
        '    dp.highlight(s, "yellow")\n'
        '    wait(300)\n'
        '    best = -1\n'
        '    for k in range(0, n):\n'
        '        c = input_coins[k]\n'
        '        coins.highlight(k, "orange")\n'
        '        wait(150)\n'
        '        if c <= s:\n'
        '            if dp.value_at(s - c) != -1:\n'
        '                cand = dp.value_at(s - c) + 1\n'
        '                dp.highlight(s - c, "cyan")\n'
        '                wait(200)\n'
        '                if best == -1 or cand < best:\n'
        '                    best = cand\n'
        '                    dp.highlight(s - c, "green")\n'
        '                wait(150)\n'
        '                dp.highlight(s - c, "yellow")\n'
        '        else:\n'
        '            coins.highlight(k, "red")\n'
        '        wait(150)\n'
        '        coins.unhighlight(k)\n'
        '    if best != -1:\n'
        '        dp.set(s, best)\n'
        '        dp.highlight(s, "green")\n'
        '    else:\n'
        '        dp.highlight(s, "red")\n'
        '    wait(300)\n'
        '    dp.unhighlight(s)\n'
    )
    default_input = {"input_coins": [1, 2, 5], "amount": 11}
    default_settings = {"speed_factor": 1.0}
    definition = _build_definition(python_code, default_input, default_settings)

    return Algorithm(
        id="coin-change",
        name="Coin change",
        display_name="Размен монет (минимум монет)",
        category_id="search",
        description_short="dp[s] = min(dp[s-c]+1 : c <= s, dp[s-c] != -1)",
        description_full="dp[s] — минимальное число монет для суммы s. Для каждой суммы перебираем все монеты c: если dp[s-c] достижима, кандидат = dp[s-c]+1. Ответ = dp[amount].",
        complexity="O(amount · n)",
        icon="coin",
        order_index=111,
        default_input_data=default_input,
        input_schema={
            "input_coins": {"type": "array", "constraints": {
                "min_length": 2, "max_length": 4, "min_value": 1, "max_value": 10,
                "label": "Монеты"
            }},
            "amount": {"type": "number", "constraints": {
                "min": 5, "max": 15, "nonnegative": True, "label": "Сумма"
            }}
        },
        default_settings=default_settings,
        definition=definition,
        definition_python=python_code,
        definition_mode='python',
    )


def add_house_robber():
    python_code = (
        'w = Window("main")\n'
        'arr = Vector(input_array)\n'
        'dp = Vector([])\n'
        'w.attach(arr)\n'
        'w.attach(dp)\n'
        'n = len(input_array)\n'
        'for k in range(n):\n'
        '    dp.append(0)\n'
        'wait(500)\n'
        '\n'
        'for i in range(0, n):\n'
        '    arr.highlight(i, "yellow")\n'
        '    if i == 0:\n'
        '        dp.set(0, input_array[0])\n'
        '        dp.highlight(0, "green")\n'
        '        wait(300)\n'
        '        dp.unhighlight(0)\n'
        '        arr.unhighlight(0)\n'
        '        continue\n'
        '    if i == 1:\n'
        '        if input_array[0] > input_array[1]:\n'
        '            dp.set(1, input_array[0])\n'
        '        else:\n'
        '            dp.set(1, input_array[1])\n'
        '        dp.highlight(1, "green")\n'
        '        wait(300)\n'
        '        dp.unhighlight(1)\n'
        '        arr.unhighlight(1)\n'
        '        continue\n'
        '    skip = dp.value_at(i - 1)\n'
        '    take = dp.value_at(i - 2) + input_array[i]\n'
        '    dp.highlight(i - 1, "cyan")\n'
        '    dp.highlight(i - 2, "orange")\n'
        '    wait(400)\n'
        '    if skip > take:\n'
        '        dp.set(i, skip)\n'
        '        dp.highlight(i - 1, "green")\n'
        '    else:\n'
        '        dp.set(i, take)\n'
        '        dp.highlight(i - 2, "green")\n'
        '    dp.highlight(i, "green")\n'
        '    wait(300)\n'
        '    dp.unhighlight(i - 1)\n'
        '    dp.unhighlight(i - 2)\n'
        '    dp.unhighlight(i)\n'
        '    arr.unhighlight(i)\n'
    )
    default_input = {"input_array": [2, 7, 9, 3, 1]}
    default_settings = {"speed_factor": 1.0}
    definition = _build_definition(python_code, default_input, default_settings)

    return Algorithm(
        id="house-robber",
        name="House robber",
        display_name="Ограбление домов",
        category_id="search",
        description_short="dp[i] = max(dp[i-1], dp[i-2] + a[i])",
        description_full="Каждый дом содержит деньги. Нельзя грабить два соседних дома. dp[i] = максимум из «пропустить i-й» (dp[i-1]) и «взять i-й» (dp[i-2] + a[i]).",
        complexity="O(n)",
        icon="🏠",
        order_index=112,
        default_input_data=default_input,
        input_schema={
            "input_array": {"type": "array", "constraints": {
                "min_length": 4, "max_length": 8, "min_value": 1, "max_value": 20
            }}
        },
        default_settings=default_settings,
        definition=definition,
        definition_python=python_code,
        definition_mode='python',
    )


def add_max_product_subarray():
    python_code = (
        'w = Window("main")\n'
        'arr = Vector(input_array)\n'
        'max_dp = Vector([])\n'
        'min_dp = Vector([])\n'
        'w.attach(arr)\n'
        'w.attach(max_dp)\n'
        'w.attach(min_dp)\n'
        'n = len(input_array)\n'
        'for k in range(n):\n'
        '    max_dp.append(0)\n'
        '    min_dp.append(0)\n'
        'wait(500)\n'
        '\n'
        'max_dp.set(0, input_array[0])\n'
        'min_dp.set(0, input_array[0])\n'
        'best = input_array[0]\n'
        'arr.highlight(0, "yellow")\n'
        'max_dp.highlight(0, "green")\n'
        'min_dp.highlight(0, "green")\n'
        'wait(400)\n'
        'arr.unhighlight(0)\n'
        'max_dp.unhighlight(0)\n'
        'min_dp.unhighlight(0)\n'
        '\n'
        'for i in range(1, n):\n'
        '    arr.highlight(i, "yellow")\n'
        '    max_dp.highlight(i - 1, "cyan")\n'
        '    min_dp.highlight(i - 1, "cyan")\n'
        '    wait(300)\n'
        '    a = max_dp.value_at(i - 1) * input_array[i]\n'
        '    b = min_dp.value_at(i - 1) * input_array[i]\n'
        '    c = input_array[i]\n'
        '    hi = a\n'
        '    if b > hi:\n'
        '        hi = b\n'
        '    if c > hi:\n'
        '        hi = c\n'
        '    lo = a\n'
        '    if b < lo:\n'
        '        lo = b\n'
        '    if c < lo:\n'
        '        lo = c\n'
        '    max_dp.set(i, hi)\n'
        '    min_dp.set(i, lo)\n'
        '    if hi > best:\n'
        '        best = hi\n'
        '    max_dp.highlight(i, "green")\n'
        '    min_dp.highlight(i, "green")\n'
        '    wait(400)\n'
        '    max_dp.unhighlight(i - 1)\n'
        '    min_dp.unhighlight(i - 1)\n'
        '    max_dp.unhighlight(i)\n'
        '    min_dp.unhighlight(i)\n'
        '    arr.unhighlight(i)\n'
    )
    default_input = {"input_array": [2, 3, -2, 4, -1, 2, -3]}
    default_settings = {"speed_factor": 1.0}
    definition = _build_definition(python_code, default_input, default_settings)

    return Algorithm(
        id="max-product-subarray",
        name="Maximum product subarray",
        display_name="Максимальное произведение подмассива",
        category_id="search",
        description_short="Два состояния max/min из-за смены знака при отрицательных",
        description_full="Ведём два массива: max_dp[i] — максимальное произведение подмассива, заканчивающегося на i, min_dp[i] — минимальное (может стать максимальным при умножении на отрицательное). hi = max(max_dp[i-1]*a[i], min_dp[i-1]*a[i], a[i]), lo = min(...).",
        complexity="O(n)",
        icon="×",
        order_index=113,
        default_input_data=default_input,
        input_schema={
            "input_array": {"type": "array", "constraints": {
                "min_length": 4, "max_length": 8, "min_value": -5, "max_value": 5,
                "has_negatives": True
            }}
        },
        default_settings=default_settings,
        definition=definition,
        definition_python=python_code,
        definition_mode='python',
    )


def add_jump_game():
    python_code = (
        'w = Window("main")\n'
        'arr = Vector(input_array)\n'
        'dp = Vector([])\n'
        'w.attach(arr)\n'
        'w.attach(dp)\n'
        'n = len(input_array)\n'
        'for k in range(n):\n'
        '    dp.append(-1)\n'
        'wait(500)\n'
        '\n'
        'dp.set(0, 0)\n'
        'arr.highlight(0, "yellow")\n'
        'dp.highlight(0, "green")\n'
        'wait(400)\n'
        'arr.unhighlight(0)\n'
        'dp.unhighlight(0)\n'
        '\n'
        'for i in range(1, n):\n'
        '    arr.highlight(i, "yellow")\n'
        '    wait(300)\n'
        '    best = -1\n'
        '    for j in range(0, i):\n'
        '        if dp.value_at(j) != -1:\n'
        '            reach = j + input_array[j]\n'
        '            arr.highlight(j, "cyan")\n'
        '            dp.highlight(j, "cyan")\n'
        '            wait(200)\n'
        '            if reach >= i:\n'
        '                cand = dp.value_at(j) + 1\n'
        '                arr.highlight(j, "green")\n'
        '                dp.highlight(j, "green")\n'
        '                wait(150)\n'
        '                if best == -1 or cand < best:\n'
        '                    best = cand\n'
        '                arr.highlight(j, "cyan")\n'
        '                dp.highlight(j, "cyan")\n'
        '            else:\n'
        '                arr.highlight(j, "red")\n'
        '            wait(200)\n'
        '            arr.unhighlight(j)\n'
        '            dp.unhighlight(j)\n'
        '    if best != -1:\n'
        '        dp.set(i, best)\n'
        '        dp.highlight(i, "green")\n'
        '    else:\n'
        '        dp.highlight(i, "red")\n'
        '    wait(300)\n'
        '    dp.unhighlight(i)\n'
        '    arr.unhighlight(i)\n'
    )
    default_input = {"input_array": [2, 3, 1, 1, 4]}
    default_settings = {"speed_factor": 1.0}
    definition = _build_definition(python_code, default_input, default_settings)

    return Algorithm(
        id="jump-game",
        name="Jump game II",
        display_name="Минимум прыжков до конца",
        category_id="search",
        description_short="dp[i] = min(dp[j]+1 : j + a[j] >= i)",
        description_full="dp[i] — минимум прыжков, чтобы достичь позиции i. Из j можно допрыгнуть до i, если j + input_array[j] >= i. Ответ = dp[n-1] (или -1, если недостижимо).",
        complexity="O(n²)",
        icon="↑",
        order_index=114,
        default_input_data=default_input,
        input_schema={
            "input_array": {"type": "array", "constraints": {
                "min_length": 4, "max_length": 8, "min_value": 1, "max_value": 4
            }}
        },
        default_settings=default_settings,
        definition=definition,
        definition_python=python_code,
        definition_mode='python',
    )


def add_lcs():
    python_code = (
        'w = Window("main")\n'
        's1 = Vector(input_text1)\n'
        's2 = Vector(input_text2)\n'
        'n = len(input_text1)\n'
        'm = len(input_text2)\n'
        'dp = Table(rows=n + 1, cols=m + 1, default=0)\n'
        'w.attach(s1)\n'
        'w.attach(s2)\n'
        'w.attach(dp)\n'
        'wait(500)\n'
        '\n'
        'for i in range(1, n + 1):\n'
        '    for j in range(1, m + 1):\n'
        '        s1.highlight(i - 1, "yellow")\n'
        '        s2.highlight(j - 1, "yellow")\n'
        '        wait(150)\n'
        '        if s1.value_at(i - 1) == s2.value_at(j - 1):\n'
        '            dp.highlight_cell(i - 1, j - 1, "cyan")\n'
        '            val = dp.get(i - 1, j - 1) + 1\n'
        '            dp.set(i, j, val)\n'
        '            dp.highlight_cell(i, j, "green")\n'
        '        else:\n'
        '            dp.highlight_cell(i - 1, j, "cyan")\n'
        '            dp.highlight_cell(i, j - 1, "cyan")\n'
        '            up = dp.get(i - 1, j)\n'
        '            left = dp.get(i, j - 1)\n'
        '            if up > left:\n'
        '                dp.set(i, j, up)\n'
        '            else:\n'
        '                dp.set(i, j, left)\n'
        '            dp.highlight_cell(i, j, "orange")\n'
        '        wait(300)\n'
        '        s1.unhighlight(i - 1)\n'
        '        s2.unhighlight(j - 1)\n'
        '        dp.unhighlight_cell(i - 1, j - 1)\n'
        '        dp.unhighlight_cell(i - 1, j)\n'
        '        dp.unhighlight_cell(i, j - 1)\n'
        '        dp.unhighlight_cell(i, j)\n'
    )
    default_input = {"input_text1": "abcde", "input_text2": "ace"}
    default_settings = {"speed_factor": 1.0}
    definition = _build_definition(python_code, default_input, default_settings)

    return Algorithm(
        id="lcs",
        name="Longest Common Subsequence",
        display_name="Наибольшая общая подпоследовательность (LCS)",
        category_id="search",
        description_short="dp[i][j] = dp[i-1][j-1]+1 или max(dp[i-1][j], dp[i][j-1])",
        description_full="Если s1[i-1]==s2[j-1], dp[i][j] = dp[i-1][j-1]+1. Иначе dp[i][j] = max(dp[i-1][j], dp[i][j-1]). Ответ = dp[n][m] — длина LCS.",
        complexity="O(n·m)",
        icon="LCS",
        order_index=120,
        default_input_data=default_input,
        input_schema={
            "input_text1": {"type": "string", "constraints": {"min_length": 3, "max_length": 6, "label": "Первая строка"}},
            "input_text2": {"type": "string", "constraints": {"min_length": 3, "max_length": 6, "label": "Вторая строка"}}
        },
        default_settings=default_settings,
        definition=definition,
        definition_python=python_code,
        definition_mode='python',
    )


def add_edit_distance():
    python_code = (
        'w = Window("main")\n'
        's1 = Vector(input_text1)\n'
        's2 = Vector(input_text2)\n'
        'n = len(input_text1)\n'
        'm = len(input_text2)\n'
        'dp = Table(rows=n + 1, cols=m + 1, default=0)\n'
        'w.attach(s1)\n'
        'w.attach(s2)\n'
        'w.attach(dp)\n'
        'wait(500)\n'
        '\n'
        'for i in range(0, n + 1):\n'
        '    dp.set(i, 0, i)\n'
        'for j in range(0, m + 1):\n'
        '    dp.set(0, j, j)\n'
        'wait(400)\n'
        '\n'
        'for i in range(1, n + 1):\n'
        '    for j in range(1, m + 1):\n'
        '        s1.highlight(i - 1, "yellow")\n'
        '        s2.highlight(j - 1, "yellow")\n'
        '        wait(150)\n'
        '        if s1.value_at(i - 1) == s2.value_at(j - 1):\n'
        '            dp.highlight_cell(i - 1, j - 1, "cyan")\n'
        '            val = dp.get(i - 1, j - 1)\n'
        '            dp.set(i, j, val)\n'
        '            dp.highlight_cell(i, j, "green")\n'
        '        else:\n'
        '            dp.highlight_cell(i - 1, j - 1, "cyan")\n'
        '            dp.highlight_cell(i - 1, j, "cyan")\n'
        '            dp.highlight_cell(i, j - 1, "cyan")\n'
        '            diag = dp.get(i - 1, j - 1) + 1\n'
        '            up = dp.get(i - 1, j) + 1\n'
        '            left = dp.get(i, j - 1) + 1\n'
        '            best = diag\n'
        '            if up < best:\n'
        '                best = up\n'
        '            if left < best:\n'
        '                best = left\n'
        '            dp.set(i, j, best)\n'
        '            dp.highlight_cell(i, j, "orange")\n'
        '        wait(300)\n'
        '        s1.unhighlight(i - 1)\n'
        '        s2.unhighlight(j - 1)\n'
        '        dp.unhighlight_cell(i - 1, j - 1)\n'
        '        dp.unhighlight_cell(i - 1, j)\n'
        '        dp.unhighlight_cell(i, j - 1)\n'
        '        dp.unhighlight_cell(i, j)\n'
    )
    default_input = {"input_text1": "kitten", "input_text2": "sitting"}
    default_settings = {"speed_factor": 1.0}
    definition = _build_definition(python_code, default_input, default_settings)

    return Algorithm(
        id="edit-distance",
        name="Edit distance",
        display_name="Расстояние редактирования (Левенштейн)",
        category_id="search",
        description_short="Минимум операций insert/delete/replace",
        description_full="dp[i][j] — минимум операций, чтобы превратить s1[0..i-1] в s2[0..j-1]. Совпало → dp[i-1][j-1]. Не совпало → min(diag, up, left) + 1 (replace, delete, insert).",
        complexity="O(n·m)",
        icon="edit",
        order_index=121,
        default_input_data=default_input,
        input_schema={
            "input_text1": {"type": "string", "constraints": {"min_length": 4, "max_length": 8, "label": "Исходная строка"}},
            "input_text2": {"type": "string", "constraints": {"min_length": 4, "max_length": 8, "label": "Целевая строка"}}
        },
        default_settings=default_settings,
        definition=definition,
        definition_python=python_code,
        definition_mode='python',
    )


def add_knapsack():
    python_code = (
        'w = Window("main")\n'
        'weights = Vector(input_weights)\n'
        'values = Vector(input_values)\n'
        'n = len(input_weights)\n'
        'C = capacity\n'
        'dp = Table(rows=n + 1, cols=C + 1, default=0)\n'
        'w.attach(weights)\n'
        'w.attach(values)\n'
        'w.attach(dp)\n'
        'wait(500)\n'
        '\n'
        'for i in range(1, n + 1):\n'
        '    weights.highlight(i - 1, "yellow")\n'
        '    values.highlight(i - 1, "yellow")\n'
        '    wait(300)\n'
        '    for cap in range(0, C + 1):\n'
        '        dp.highlight_cell(i - 1, cap, "cyan")\n'
        '        if input_weights[i - 1] <= cap:\n'
        '            take = dp.get(i - 1, cap - input_weights[i - 1]) + input_values[i - 1]\n'
        '            skip = dp.get(i - 1, cap)\n'
        '            if take > skip:\n'
        '                dp.set(i, cap, take)\n'
        '                dp.highlight_cell(i, cap, "green")\n'
        '            else:\n'
        '                dp.set(i, cap, skip)\n'
        '                dp.highlight_cell(i, cap, "orange")\n'
        '        else:\n'
        '            dp.set(i, cap, dp.get(i - 1, cap))\n'
        '            dp.highlight_cell(i, cap, "orange")\n'
        '        wait(200)\n'
        '        dp.unhighlight_cell(i - 1, cap)\n'
        '        dp.unhighlight_cell(i, cap)\n'
        '    weights.unhighlight(i - 1)\n'
        '    values.unhighlight(i - 1)\n'
    )
    default_input = {"input_weights": [2, 3, 4], "input_values": [3, 4, 5], "capacity": 6}
    default_settings = {"speed_factor": 1.0}
    definition = _build_definition(python_code, default_input, default_settings)

    return Algorithm(
        id="knapsack",
        name="0/1 Knapsack",
        display_name="Задача о рюкзаке (0/1)",
        category_id="search",
        description_short="Максимум ценности при ограничении по весу",
        description_full="dp[i][w] — максимум ценности, используя первые i предметов и вместимость w. Если предмет i-1 влезает: max(взять, не взять). Иначе — только не взять.",
        complexity="O(n·W)",
        icon="🎒",
        order_index=122,
        default_input_data=default_input,
        input_schema={
            "input_weights": {"type": "array", "constraints": {
                "min_length": 2, "max_length": 8, "min_value": 1, "max_value": 5,
                "label": "Веса"
            }},
            "input_values": {
                "type": "array",
                "constraints": {
                    "min_value": 1, "max_value": 10,
                    "label": "Ценности"
                },
                "depends_on": {"field": "input_weights", "mode": "same_length"}
            },
            "capacity": {
                "type": "number",
                "constraints": {"min": 1, "nonnegative": True, "label": "Вместимость"},
                "depends_on": {"field": "input_weights", "mode": "sum_scaled", "ratio": 0.7}
            }
        },
        default_settings=default_settings,
        definition=definition,
        definition_python=python_code,
        definition_mode='python',
    )


def add_matrix_chain():
    python_code = (
        'w = Window("main")\n'
        'dims = Vector(input_dimensions)\n'
        'n = len(input_dimensions) - 1\n'
        'dp = Table(rows=n, cols=n, default=0)\n'
        'w.attach(dims)\n'
        'w.attach(dp)\n'
        'wait(500)\n'
        '\n'
        'for L in range(2, n + 1):\n'
        '    for i in range(0, n - L + 1):\n'
        '        j = i + L - 1\n'
        '        dp.highlight_cell(i, j, "yellow")\n'
        '        wait(200)\n'
        '        best = 1000000000\n'
        '        best_k = i\n'
        '        for k in range(i, j):\n'
        '            dims.highlight(k, "cyan")\n'
        '            dims.highlight(k + 1, "cyan")\n'
        '            dp.highlight_cell(i, k, "orange")\n'
        '            dp.highlight_cell(k + 1, j, "orange")\n'
        '            cost = dp.get(i, k) + dp.get(k + 1, j) + input_dimensions[i] * input_dimensions[k + 1] * input_dimensions[j + 1]\n'
        '            if cost < best:\n'
        '                best = cost\n'
        '                best_k = k\n'
        '            wait(300)\n'
        '            dims.unhighlight(k)\n'
        '            dims.unhighlight(k + 1)\n'
        '            dp.unhighlight_cell(i, k)\n'
        '            dp.unhighlight_cell(k + 1, j)\n'
        '        dp.set(i, j, best)\n'
        '        dp.highlight_cell(i, j, "green")\n'
        '        wait(400)\n'
        '        dp.unhighlight_cell(i, j)\n'
    )
    default_input = {"input_dimensions": [10, 30, 5, 60]}
    default_settings = {"speed_factor": 1.0}
    definition = _build_definition(python_code, default_input, default_settings)

    return Algorithm(
        id="matrix-chain",
        name="Matrix chain multiplication",
        display_name="Порядок перемножения матриц",
        category_id="search",
        description_short="Минимум скалярных умножений при разной расстановке скобок",
        description_full="dims[i]..dims[i+1] — размеры матрицы i. dp[i][j] — минимум умножений для матриц i..j. Перебираем k — точку разделения. cost = dp[i][k] + dp[k+1][j] + dims[i]·dims[k+1]·dims[j+1].",
        complexity="O(n³)",
        icon="×",
        order_index=123,
        default_input_data=default_input,
        input_schema={
            "input_dimensions": {"type": "array", "constraints": {"min_length": 4, "max_length": 6, "min_value": 1, "max_value": 99, "label": "Размеры"}}
        },
        default_settings=default_settings,
        definition=definition,
        definition_python=python_code,
        definition_mode='python',
    )


def add_lps():
    python_code = (
        'w = Window("main")\n'
        's = Vector(input_string)\n'
        'r = Vector(input_string)\n'
        'r.reverse()\n'
        'n = len(input_string)\n'
        'dp = Table(rows=n + 1, cols=n + 1, default=0)\n'
        'w.attach(s)\n'
        'w.attach(r)\n'
        'w.attach(dp)\n'
        'wait(600)\n'
        '\n'
        'for i in range(1, n + 1):\n'
        '    for j in range(1, n + 1):\n'
        '        s.highlight(i - 1, "yellow")\n'
        '        r.highlight(j - 1, "yellow")\n'
        '        wait(150)\n'
        '        if s.value_at(i - 1) == r.value_at(j - 1):\n'
        '            dp.highlight_cell(i - 1, j - 1, "cyan")\n'
        '            val = dp.get(i - 1, j - 1) + 1\n'
        '            dp.set(i, j, val)\n'
        '            dp.highlight_cell(i, j, "green")\n'
        '        else:\n'
        '            dp.highlight_cell(i - 1, j, "cyan")\n'
        '            dp.highlight_cell(i, j - 1, "cyan")\n'
        '            up = dp.get(i - 1, j)\n'
        '            left = dp.get(i, j - 1)\n'
        '            if up > left:\n'
        '                dp.set(i, j, up)\n'
        '            else:\n'
        '                dp.set(i, j, left)\n'
        '            dp.highlight_cell(i, j, "orange")\n'
        '        wait(300)\n'
        '        s.unhighlight(i - 1)\n'
        '        r.unhighlight(j - 1)\n'
        '        dp.unhighlight_cell(i - 1, j - 1)\n'
        '        dp.unhighlight_cell(i - 1, j)\n'
        '        dp.unhighlight_cell(i, j - 1)\n'
        '        dp.unhighlight_cell(i, j)\n'
    )
    default_input = {"input_string": "bbabcbcab"}
    default_settings = {"speed_factor": 1.0}
    definition = _build_definition(python_code, default_input, default_settings)

    return Algorithm(
        id="lps",
        name="Longest Palindromic Subsequence",
        display_name="Наибольшая палиндромная подпоследовательность",
        category_id="search",
        description_short="LCS(s, reverse(s)) — длина максимального палиндрома",
        description_full="Палиндромная подпоследовательность s совпадает с подпоследовательностью reverse(s). Задача сводится к LCS(s, reverse(s)). dp[i][j] — длина LPS для s[0..i-1] и reverse(s)[0..j-1].",
        complexity="O(n²)",
        icon="↺",
        order_index=124,
        default_input_data=default_input,
        input_schema={
            "input_string": {"type": "string", "constraints": {"min_length": 4, "max_length": 16, "alphabet": "abcdef"}}
        },
        default_settings=default_settings,
        definition=definition,
        definition_python=python_code,
        definition_mode='python',
    )
