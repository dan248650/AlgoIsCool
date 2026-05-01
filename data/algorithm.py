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
    default_input_data = db.Column(JSON)              # Данные по умолчанию (например, массив, target, граф)

    definition = db.Column(JSON, nullable=False)
    input_schema = db.Column(JSON)
    default_settings = db.Column(JSON)


def add_linear_search():
    linear_search = Algorithm(
        id="linear-search",
        name="Линейный поиск",
        display_name="Линейный поиск",
        category_id="search",
        description_short="Последовательный перебор элементов",
        description_full="Линейный поиск — алгоритм, который последовательно проверяет каждый элемент массива, пока не найдет искомый или не дойдет до конца.",
        complexity="O(n)",
        icon="linear",
        order_index=10,
        default_input_data={
            "input_array": [64, 34, 25, 12, 22, 11, 90],
            "target": 22
        },
        input_schema={
            "input_array": "array",
            "target": "number"
        },
        default_settings={
            "speed_factor": 1.0,
            "colors": {
                "current": "#FFA07A",
                "found": "#4CAF50"
            }
        },
        definition={
            "type": "array",
            "initial_state": {
                "array": "input_array",
                "target": "target",
                "n": "length(input_array)",
                "index": -1
            },
            "steps": [
                {
                    "name": "Создание элементов",
                    "commands": [
                        {
                            "component": "create_elements",
                            "params": {
                                "array": "array"
                            }
                        }
                    ]
                },
                {
                    "name": "Поиск элемента",
                    "commands": [
                        {
                            "component": "for_each",
                            "items": "range(0, n)",
                            "variable": "i",
                            "commands": [
                                {
                                    "component": "highlight",
                                    "params": {
                                        "element_ids": ["elem_{{i}}"],
                                        "color": "colors.current",
                                        "duration": 600
                                    }
                                },
                                {
                                    "component": "condition",
                                    "condition": "array[i] == target",
                                    "then": [
                                        {
                                            "component": "highlight",
                                            "params": {
                                                "element_ids": ["elem_{{i}}"],
                                                "color": "colors.found",
                                                "duration": 1000
                                            }
                                        },
                                        {
                                            "component": "set_variable",
                                            "variable": "index",
                                            "value": "i"
                                        }
                                    ]
                                },
                                {
                                    "component": "unhighlight",
                                    "params": {
                                        "element_ids": ["elem_{{i}}"],
                                        "duration": 400
                                    }
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    )
    return linear_search


def add_bubble_sort():
    bubble_sort = Algorithm(
        id="bubble-sort",
        name="Сортировка пузырьком",
        display_name="Сортировка пузырьком",
        category_id="sorting",
        description_short="Попарное сравнение и обмен соседних элементов",
        description_full="Сортировка пузырьком — простой алгоритм сортировки, который многократно проходит по массиву, сравнивая соседние элементы и меняя их местами, если они стоят в неправильном порядке. Каждый проход 'всплывает' наибольший элемент в конец массива.",
        complexity="O(n²)",
        icon="bubble",
        order_index=20,
        default_input_data={
            "input_array": [64, 34, 25, 12, 22, 11, 90]
        },
        input_schema={
            "input_array": "array"
        },
        default_settings={
            "speed_factor": 1.0,
            "colors": {
                "comparing": "#FFA07A",
                "swapping": "#FF6B6B",
                "sorted": "#4CAF50",
                "default": "#e0e0e0"
            }
        },
        definition={
            "type": "array",
            "initial_state": {
                "array": "input_array",
                "n": "length(input_array)",
                "i": 0,
                "j": 0
            },
            "steps": [
                {
                    "name": "Создание элементов",
                    "commands": [
                        {
                            "component": "create_elements",
                            "params": {
                                "array": "array"
                            }
                        }
                    ]
                },
                {
                    "name": "Сортировка пузырьком",
                    "commands": [
                        {
                            "component": "for_each",
                            "items": "range(0, n - 1)",
                            "variable": "i",
                            "commands": [
                                {
                                    "component": "for_each",
                                    "items": "range(0, n - i - 1)",
                                    "variable": "j",
                                    "commands": [
                                        {
                                            "component": "highlight",
                                            "params": {
                                                "element_ids": ["elem_{{j}}", "elem_{{j + 1}}"],
                                                "color": "colors.comparing",
                                                "duration": 300
                                            }
                                        },
                                        {
                                            "component": "condition",
                                            "condition": "array[j] > array[j + 1]",
                                            "then": [
                                                {
                                                    "component": "highlight",
                                                    "params": {
                                                        "element_ids": ["elem_{{j}}", "elem_{{j + 1}}"],
                                                        "color": "colors.swapping",
                                                        "duration": 300
                                                    }
                                                },
                                                {
                                                    "component": "swap_elements",
                                                    "params": {
                                                        "element1_id": "elem_{{j}}",
                                                        "element2_id": "elem_{{j + 1}}",
                                                        "duration": 500
                                                    }
                                                },
                                                {
                                                    "component": "set_variable",
                                                    "variable": "array",
                                                    "value": "swap(array, j, j + 1)"
                                                }
                                            ]
                                        },
                                        {
                                            "component": "unhighlight",
                                            "params": {
                                                "element_ids": ["elem_{{j}}", "elem_{{j + 1}}"],
                                                "duration": 300
                                            }
                                        }
                                    ]
                                },
                                {
                                    "component": "highlight",
                                    "params": {
                                        "element_ids": ["elem_{{n - i - 1}}"],
                                        "color": "colors.sorted",
                                        "duration": 400
                                    }
                                }
                            ]
                        },
                        {
                            "component": "highlight",
                            "params": {
                                "element_ids": ["elem_0"],
                                "color": "colors.sorted",
                                "duration": 400
                            }
                        }
                    ]
                }
            ]
        }
    )
    return bubble_sort


def add_bfs():
    bfs = Algorithm(
        id="bfs",
        name="Поиск в ширину (BFS)",
        display_name="Поиск в ширину (BFS)",
        category_id="graph",
        description_short="Обход графа в ширину",
        description_full="Алгоритм обхода графа, который посещает все вершины в порядке увеличения расстояния от стартовой вершины. Использует очередь.",
        complexity="O(V + E)",
        icon="bfs",
        order_index=30,
        default_input_data={
            "nodes": [{"label": "A"}, {"label": "B"}, {"label": "C"}, {"label": "D"}],
            "edges": [{"from": 0, "to": 1}, {"from": 1, "to": 2}, {"from": 2, "to": 3}],
            "directed": False,
            "start_node": 0
        },
        input_schema={
            "nodes": "graph_nodes",
            "edges": "graph_edges",
            "directed": "boolean",
            "start_node": "number"
        },
        default_settings={
            "speed_factor": 1.0,
            "layout": "kamada_kawai"
        },
        definition={
            "type": "graph",
            "initial_state": {
                "visited": [],
                "queue": [],
                "start_node": "start_node"
            },
            "steps": [
                {
                    "name": "Инициализация",
                    "commands": [
                        {"component": "set_variable", "variable": "queue", "value": "[start_node]"},
                        {"component": "set_variable", "variable": "visited", "value": "[start_node]"},
                        {"component": "highlight_node", "params": {"node_id": "{{start_node}}", "color": "#4CAF50", "duration": 300}},
                        {"component": "wait", "params": {"duration": 300}}
                    ]
                },
                {
                    "name": "Основной цикл BFS",
                    "commands": [
                        {
                            "component": "while_loop",
                            "condition": "len(queue) > 0",
                            "commands": [
                                {"component": "set_variable", "variable": "u", "value": "queue[0]"},
                                {"component": "set_variable", "variable": "queue", "value": "queue[1:]"},
                                {"component": "highlight_node", "params": {"node_id": "{{u}}", "color": "#FFA07A", "duration": 300}},
                                {"component": "wait", "params": {"duration": 300}},
                                {
                                    "component": "for_each",
                                    "items": "neighbors(u)",
                                    "variable": "v",
                                    "commands": [
                                        {
                                            "component": "condition",
                                            "condition": "v not in visited",
                                            "then": [
                                                {"component": "highlight_edge", "params": {"from": "{{u}}", "to": "{{v}}", "color": "#0047AB", "duration": 300}},
                                                {"component": "set_variable", "variable": "visited", "value": "visited + [v]"},
                                                {"component": "set_variable", "variable": "queue", "value": "queue + [v]"},
                                                {"component": "highlight_node", "params": {"node_id": "{{v}}", "color": "#4CAF50", "duration": 300}},
                                                {"component": "wait", "params": {"duration": 300}}
                                            ]
                                        }
                                    ]
                                },
                                {"component": "unhighlight_node", "params": {"node_id": "{{u}}", "duration": 300}}
                            ]
                        }
                    ]
                }
            ]
        }
    )
    return bfs


def add_kadane():
    kadane = Algorithm(
        id="kadane",
        name="Максимальная сумма подотрезка",
        display_name="Максимальная сумма подотрезка (Кадане)",
        category_id="search",
        description_short="Поиск подмассива с максимальной суммой",
        description_full="Алгоритм Кадане: поддерживаем текущий подотрезок. Если сумма становится меньше текущего элемента – начинаем новый отрезок.",
        complexity="O(n)",
        icon="kadane",
        order_index=40,
        default_input_data={"input_array": [-2, 1, -3, 4, -1, 2, 1, -5, 4]},
        input_schema={"input_array": "array"},
        default_settings={
            "speed_factor": 1.0,
            "colors": {
                "current_window": "#FFA07A",
                "max_subarray": "#4CAF50"
            }
        },
        definition={
            "type": "array",
            "initial_state": {
                "array": "input_array",
                "n": "length(input_array)",
                "current_sum": 0,
                "max_sum": -10**9,
                "start": 0,
                "end": 0,
                "temp_start": 0
            },
            "steps": [
                {
                    "name": "Создание элементов",
                    "commands": [{"component": "create_elements", "params": {"array": "array"}}]
                },
                {
                    "name": "Алгоритм Кадане",
                    "commands": [
                        # Инициализация первым элементом
                        {
                            "component": "condition",
                            "condition": "n > 0",
                            "then": [
                                {"component": "set_variable", "variable": "current_sum", "value": "array[0]"},
                                {"component": "set_variable", "variable": "max_sum", "value": "array[0]"},
                                {"component": "set_variable", "variable": "temp_start", "value": "0"},
                                {"component": "set_variable", "variable": "start", "value": "0"},
                                {"component": "set_variable", "variable": "end", "value": "0"}
                            ]
                        },
                        # Проход по массиву, начиная с индекса 1
                        {
                            "component": "for_each",
                            "items": "range(1, n)",
                            "variable": "i",
                            "commands": [
                                # Показать текущий элемент
                                {
                                    "component": "highlight",
                                    "params": {"element_ids": ["elem_{{i}}"], "color": "#FFFF00", "duration": 200}
                                },
                                # Основное условие
                                {
                                    "component": "condition",
                                    "condition": "current_sum + array[i] > array[i]",
                                    "then": [
                                        {"component": "set_variable", "variable": "current_sum", "value": "current_sum + array[i]"}
                                        # temp_start остаётся прежним
                                    ],
                                    "else": [
                                        {"component": "set_variable", "variable": "current_sum", "value": "array[i]"},
                                        {"component": "set_variable", "variable": "temp_start", "value": "i"}
                                    ]
                                },
                                # Обновление максимума
                                {
                                    "component": "condition",
                                    "condition": "current_sum > max_sum",
                                    "then": [
                                        {"component": "set_variable", "variable": "max_sum", "value": "current_sum"},
                                        {"component": "set_variable", "variable": "start", "value": "temp_start"},
                                        {"component": "set_variable", "variable": "end", "value": "i"}
                                    ]
                                },
                                {
                                    "component": "condition",
                                    "condition": "current_sum == max_sum",
                                    "then": [
                                        {
                                            "component": "for_each",
                                            "items": "range(temp_start, i + 1)",
                                            "variable": "j",
                                            "commands": [
                                                {"component": "highlight",
                                                 "params": {"element_ids": ["elem_{{j}}"], "color": "#90EE90",
                                                            "duration": 400}}
                                            ]
                                        },
                                        {"component": "wait", "params": {"duration": 400}}
                                    ]
                                },
                                # Сначала снимаем подсветку слева от отрезка
                                {
                                    "component": "for_each",
                                    "items": "range(0, temp_start)",
                                    "variable": "j",
                                    "commands": [
                                        {"component": "unhighlight", "params": {"element_ids": ["elem_{{j}}"], "duration": 50}}
                                    ]
                                },

                            ]
                        }
                    ]
                },
                {
                    "name": "Подсветка максимального подотрезка",
                    "commands": [
                        # Снимаем всё
                        {
                            "component": "for_each",
                            "items": "range(0, n)",
                            "variable": "j",
                            "commands": [{"component": "unhighlight", "params": {"element_ids": ["elem_{{j}}"], "duration": 200}}]
                        },
                        # Подсвечиваем финальный ответ
                        {
                            "component": "condition",
                            "condition": "n > 0",
                            "then": [
                                {
                                    "component": "for_each",
                                    "items": "range(start, end + 1)",
                                    "variable": "j",
                                    "commands": [
                                        {"component": "highlight",
                                         "params": {"element_ids": ["elem_{{j}}"], "color": "colors.max_subarray", "duration": 600}}
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    )
    return kadane


def add_dfs():
    dfs = Algorithm(
        id="dfs",
        name="Поиск в глубину (DFS)",
        display_name="Поиск в глубину (DFS)",
        category_id="graph",
        description_short="Обход графа в глубину",
        description_full="Алгоритм обхода графа, который идёт вглубь по одному пути, используя стек.",
        complexity="O(V + E)",
        icon="dfs",
        order_index=35,
        default_input_data={
            "nodes": [{"label": "A"}, {"label": "B"}, {"label": "C"}, {"label": "D"}, {"label": "E"}],
            "edges": [{"from": 0, "to": 1}, {"from": 0, "to": 2}, {"from": 1, "to": 3}, {"from": 1, "to": 4}],
            "directed": False,
            "start_node": 0
        },
        input_schema={
            "nodes": "graph_nodes",
            "edges": "graph_edges",
            "directed": "boolean",
            "start_node": "number"
        },
        default_settings={
            "speed_factor": 1.0,
            "layout": "kamada_kawai"
        },
        definition={
            "type": "graph",
            "initial_state": {
                "visited": [],
                "stack": [],
                "start_node": "start_node"
            },
            "steps": [
                {
                    "name": "Инициализация",
                    "commands": [
                        {"component": "set_variable", "variable": "stack", "value": "[start_node]"},
                        {"component": "set_variable", "variable": "visited", "value": "[]"},
                        {"component": "highlight_node", "params": {"node_id": "{{start_node}}", "color": "#4CAF50", "duration": 300}},
                        {"component": "wait", "params": {"duration": 300}}
                    ]
                },
                {
                    "name": "Основной цикл DFS (стек)",
                    "commands": [
                        {
                            "component": "while_loop",
                            "condition": "len(stack) > 0",
                            "commands": [
                                {"component": "set_variable", "variable": "u", "value": "stack[-1]"},
                                {"component": "set_variable", "variable": "stack", "value": "stack[:-1]"},
                                {"component": "condition",
                                 "condition": "u not in visited",
                                 "then": [
                                     {"component": "set_variable", "variable": "visited", "value": "visited + [u]"},
                                     {"component": "highlight_node", "params": {"node_id": "{{u}}", "color": "#FFA07A", "duration": 300}},
                                     {"component": "wait", "params": {"duration": 300}},
                                     {
                                         "component": "for_each",
                                         "items": "neighbors(u)",
                                         "variable": "v",
                                         "commands": [
                                             {
                                                 "component": "condition",
                                                 "condition": "v not in visited",
                                                 "then": [
                                                     {"component": "highlight_edge", "params": {"from": "{{u}}", "to": "{{v}}", "color": "#0047AB", "duration": 300}},
                                                     {"component": "set_variable", "variable": "stack", "value": "stack + [v]"},
                                                     {"component": "wait", "params": {"duration": 300}}
                                                 ]
                                             }
                                         ]
                                     }
                                 ]},
                                {"component": "unhighlight_node", "params": {"node_id": "{{u}}", "duration": 300}}
                            ]
                        }
                    ]
                }
            ]
        }
    )
    return dfs
