"""
Структуры данных для визуализации.

Структура:
  * знает своё имя (name) — задаётся интерпретатором;
  * знает, к какому окну прикреплена (window) — или None;
  * умеет принимать команды через handle(component, params);
  * отдаёт снапшот через build_snapshot(command_index) — индекс
    передаёт интерпретатор, чтобы счётчик был глобальным.

Структура НЕ ведёт счётчик команд. Она возвращает "сырые" команды
(список dict-ов), а интерпретатор уже сам:
  * присваивает им глобальный номер,
  * складывает в общий commands,
  * складывает рядом снапшот.
"""
from abc import ABC, abstractmethod
from .layout import compute_layout, compute_tree_layout


class Structure(ABC):
    type_name = None  # 'vector' | 'graph' | ...

    def __init__(self):
        self.name = None       # имя экземпляра (задаёт интерпретатор)
        self.window = None     # окно, к которому прикреплена, или None
        self._colors = {}      # index -> color
        self._styles = {}      # index -> dict

    # ---------- Привязка к окну ----------

    def attach_to(self, window):
        self.window = window
        window.structure = self

    def detach(self):
        if self.window is not None:
            self.window.structure = None
            self.window = None

    def is_visible(self) -> bool:
        return self.window is not None and self.window.visible

    # ---------- Вспомогательное ----------

    def _tag(self, command: dict) -> dict:
        """Проставляет имя структуры в команду."""
        command['structure'] = self.name
        return command

    @staticmethod
    def _to_index(value):
        if isinstance(value, int):
            return value
        if isinstance(value, float) and value.is_integer():
            return int(value)
        if isinstance(value, str):
            try:
                return int(value.strip())
            except ValueError:
                pass
        raise ValueError(f"Некорректный индекс: {value!r}")

    # ---------- Абстрактная часть ----------

    @abstractmethod
    def handle(self, component: str, params: dict) -> list:
        """
        Меняет внутреннее состояние структуры и возвращает список
        сырых команд (без индекса, но с полем 'structure').
        Если структура не привязана к окну, изменения всё равно происходят.
        """

    @abstractmethod
    def build_snapshot_dict(self) -> dict:
        """Фрагмент снапшота — только эта структура, без индекса и имени.
        Имя структуры и commandIndex живут в глобальном снапшоте."""


# ======================= ВЕКТОР =======================

class VectorStructure(Structure):
    type_name = 'vector'

    def __init__(self, array):
        super().__init__()
        self.array = list(array)
        self._base_element_size = 40
        self._spacing = 10

    def handle(self, component, params):
        if component == 'create_elements':
            return [self._tag({
                'component': 'create_elements',
                'params': {'array': list(self.array)},
            })]
        if component in ('highlight', 'unhighlight', 'set_opacity'):
            indices = params['indices']
            if not isinstance(indices, list):
                indices = [indices]
            indices = [self._to_index(i) for i in indices]

            if component == 'highlight':
                return self._highlight(indices, params['color'], params.get('style'))
            if component == 'unhighlight':
                return self._unhighlight(indices)
            return self._set_opacity(indices, params['opacity'])
        if component == 'swap':
            return self._swap(params['i'], params['j'])
        raise ValueError(f"Unknown vector component: {component}")

    # --- общие методы (highlight / unhighlight / set_opacity) ---

    def _highlight(self, indices, color, style=None):
        for i in indices:
            self._colors[i] = color
            if style is not None:
                self._styles[i] = style
        return [self._tag({
            'component': 'highlight',
            'params': {
                'element_ids': [f"elem_{i}" for i in indices],
                'color': color,
                'style': style,
            },
        })]

    def _unhighlight(self, indices):
        for i in indices:
            self._colors.pop(i, None)
            self._styles.pop(i, None)
        return [self._tag({
            'component': 'unhighlight',
            'params': {'element_ids': [f"elem_{i}" for i in indices]},
        })]

    def _set_opacity(self, indices, opacity):
        return [self._tag({
            'component': 'set_opacity',
            'params': {
                'element_ids': [f"elem_{i}" for i in indices],
                'opacity': opacity,
            },
        })]

    # --- специфичное для вектора ---

    def _swap(self, i, j):
        self.array[i], self.array[j] = self.array[j], self.array[i]
        # цвета и стили переставляются вместе со значениями,
        # чтобы снапшот совпадал с тем, что видно на экране
        c_i = self._colors.pop(i, None)
        c_j = self._colors.pop(j, None)
        if c_i is not None:
            self._colors[j] = c_i
        if c_j is not None:
            self._colors[i] = c_j
        s_i = self._styles.pop(i, None)
        s_j = self._styles.pop(j, None)
        if s_i is not None:
            self._styles[j] = s_i
        if s_j is not None:
            self._styles[i] = s_j
        return [self._tag({
            'component': 'swap_elements',
            'params': {
                'element1_id': f"elem_{i}",
                'element2_id': f"elem_{j}",
                'duration': 500,
            },
        })]

    # --- снапшот ---

    def build_snapshot_dict(self):
        elements = []
        for i, value in enumerate(self.array):
            elements.append({
                'id': f"elem_{i}",
                'value': value,
                'color': self._colors.get(i),
                'x': i * (self._base_element_size + self._spacing),
                'y': 50,
            })
        return {
            'type': 'vector',
            'baseElementSize': self._base_element_size,
            'elements': elements,
        }


# ======================= ГРАФ =======================

class GraphStructure(Structure):
    type_name = 'graph'

    def __init__(self, data):
        super().__init__()
        # узлы БЕЗ координат: только id и label.
        # Если id не задан — берём порядковый индекс.
        self.nodes = [
            {'id': n.get('id', i), 'label': n.get('label', str(n.get('id', i)))}
            for i, n in enumerate(data.get('nodes', []))
        ]
        self.edges = data.get('edges', [])
        self.directed = data.get('directed', False)
        self._edge_colors = {}

        # Layout — забота этого модуля, ленивый.
        # _layout_version == _version  → layout актуален
        # _layout_version  < _version  → нужно пересчитать (ensure_layout)
        self._layout = {}  # node_id -> (x, y)
        self._layout_version = -1
        self._version = 0

        # Параметры раскладки
        self._layout_name = data.get('layout', 'kamada_kawai')
        self._layout_scale = data.get('layout_scale', 100)

    def _edge_key(self, a, b):
        if self.directed:
            return a, b
        return tuple(sorted((a, b)))

    def neighbors(self, node_id):
        """
        Список id соседей узла. Для ориентированного графа — только
        исходящие рёбра. Для неориентированного — оба конца каждого
        инцидентного ребра.
        """
        nid = self._to_index(node_id)
        result = []
        for edge in self.edges:
            if edge['from'] == nid:
                result.append(edge['to'])
            elif not self.directed and edge['to'] == nid:
                result.append(edge['from'])
        return result

    def handle(self, component, params):
        if component == 'create_graph':
            self.ensure_layout()
            nodes_with_coords = []
            for node in self.nodes:
                nid = node.get('id')
                x, y = self._layout.get(nid, (0.0, 0.0))
                nodes_with_coords.append({
                    'id': nid,
                    'label': node.get('label', str(nid)),
                    'x': x,
                    'y': y,
                    'color': None,
                })
            return [self._tag({
                'component': 'create_graph',
                'params': {
                    'nodes': nodes_with_coords,
                    'edges': self.edges,
                    'directed': self.directed,
                },
            })]
        if component == 'highlight_node':
            return self._highlight_node(self._to_index(params['node_id']), params['color'])
        if component == 'unhighlight_node':
            return self._unhighlight_node(self._to_index(params['node_id']))
        if component == 'highlight_edge':
            return self._highlight_edge(self._to_index(params['from']), self._to_index(params['to']), params['color'])
        if component == 'unhighlight_edge':
            return self._unhighlight_edge(self._to_index(params['from']), self._to_index(params['to']))
        if component == 'set_node_label':
            return self._set_node_label(self._to_index(params['node_id']), params['label'])
        raise ValueError(f"Unknown graph component: {component}")

    def ensure_layout(self):
        """
        Ленивый расчёт: если топология не менялась с прошлого раза,
        ничего не делает. Пересчёт идёт через compute_layout(...).
        """
        if self._layout_version >= self._version:
            return
        self._layout = compute_layout(
            self.nodes, self.edges,
            directed=self.directed,
            layout_name=self._layout_name,
            scale=self._layout_scale,
        )
        self._layout_version = self._version

    def _bump_version(self):
        """Вызывать при любом изменении топологии.
        Пока таких команд нет — задел на будущее."""
        self._version += 1

    # --- общие методы: элемент = узел ---

    def _highlight_node(self, node_id, color, style=None):
        self._colors[node_id] = color
        if style is not None:
            self._styles[node_id] = style
        return [self._tag({
            'component': 'highlight_node',
            'params': {'node_id': node_id, 'color': color, 'style': style},
        })]

    def _unhighlight_node(self, node_id):
        self._colors.pop(node_id, None)
        self._styles.pop(node_id, None)
        return [self._tag({
            'component': 'unhighlight_node',
            'params': {'node_id': node_id},
        })]

    def _set_opacity(self, indices, opacity):
        # заглушка на будущее: у узлов пока нет прозрачности
        return [self._tag({
            'component': 'set_opacity',
            'params': {
                'element_ids': [f"node_{i}" for i in indices],
                'opacity': opacity,
            },
        })]

    # --- специфичное для графа ---

    def _highlight_edge(self, a, b, color):
        key = self._edge_key(a, b)
        self._edge_colors[key] = color
        return [self._tag({
            'component': 'highlight_edge',
            'params': {'from': a, 'to': b, 'color': color},
        })]

    def _unhighlight_edge(self, a, b):
        key = self._edge_key(a, b)
        self._edge_colors.pop(key, None)
        return [self._tag({
            'component': 'unhighlight_edge',
            'params': {'from': a, 'to': b},
        })]

    def _set_node_label(self, node_id, label):
        for node in self.nodes:
            if node.get('id') == node_id:
                node['label'] = label
                break
        return [self._tag({
            'component': 'set_node_label',
            'params': {'node_id': node_id, 'label': label},
        })]

    # --- снапшот ---

    def build_snapshot_dict(self):
        self.ensure_layout()
        snapshot_nodes = []
        for node in self.nodes:
            nid = node.get('id')
            x, y = self._layout.get(nid, (0.0, 0.0))
            snapshot_nodes.append({
                'id': nid,
                'label': node.get('label', str(nid)),
                'x': x,
                'y': y,
                'color': self._colors.get(nid),
            })
        snapshot_edges = []
        for edge in self.edges:
            key = self._edge_key(edge['from'], edge['to'])
            snapshot_edges.append({
                'from': edge['from'],
                'to': edge['to'],
                'color': self._edge_colors.get(key),
                'label': edge.get('label'),
            })
        return {
            'type': 'graph',
            'directed': self.directed,
            'nodes': snapshot_nodes,
            'edges': snapshot_edges,
        }


class TreeStructure(GraphStructure):
    type_name = 'tree'

    def __init__(self, data):
        super().__init__(data)
        # Узлы: id (уникальный), label (для отображения), value (для сравнений).
        # Если value не задан — берём id; если id не задан — порядковый индекс.
        self.nodes = []
        for i, n in enumerate(data.get('nodes', [])):
            nid = n.get('id', i)
            value = n.get('value', nid)
            self.nodes.append({
                'id': nid,
                'label': n.get('label', str(value)),
                'value': value,
            })

        # Счётчик для авто-генерации id в add_child.
        numeric_ids = [n['id'] for n in self.nodes if isinstance(n['id'], int)]
        self._next_id = (max(numeric_ids) + 1) if numeric_ids else 1

        # Корень: явный или центр графа.
        explicit_root = data.get('root_id')
        if explicit_root is not None:
            self.root_id = explicit_root
        else:
            self.root_id = self._find_center()

        # Для дерева directed всегда True: рёбра — от родителя к ребёнку.
        # (Если пришли неориентированные рёбра, интерпретируем их
        # как «родитель ↔ ребёнок» и считаем от корня.)
        self.directed = True
        self._build_parent_map()

    # ---------- Поиск корня ----------

    def _find_center(self):
        """Центр графа: узлы с минимальным эксцентриситетом."""
        if not self.nodes:
            raise ValueError("Tree: нет узлов")

        # BFS от каждого узла; для дерева это O(V^2), приемлемо.
        adj = {n['id']: [] for n in self.nodes}
        for e in self.edges:
            adj[e['from']].append(e['to'])
            adj[e['to']].append(e['from'])

        def eccentricity(start):
            dist = {start: 0}
            queue = [start]
            while queue:
                u = queue.pop(0)
                for v in adj[u]:
                    if v not in dist:
                        dist[v] = dist[u] + 1
                        queue.append(v)
            return max(dist.values())

        ecc = {n['id']: eccentricity(n['id']) for n in self.nodes}
        min_ecc = min(ecc.values())
        candidates = [nid for nid, e in ecc.items() if e == min_ecc]

        # Если кандидатов несколько (чётный диаметр), берём первый
        # по порядку в nodes — для стабильности.
        order = {n['id']: i for i, n in enumerate(self.nodes)}
        candidates.sort(key=lambda nid: order[nid])
        return candidates[0]

    def _build_parent_map(self):
        """parent_of[child] = parent. Для корня — None.
        После обхода нормализуем self.edges: каждое ребро становится
        parent → child, независимо от того, как оно было в input."""
        self.parent_of = {self.root_id: None}
        children_of = {self.root_id: []}
        queue = [self.root_id]
        visited = {self.root_id}

        # adjacency (неориентированная) для обхода
        adj = {n['id']: [] for n in self.nodes}
        for e in self.edges:
            adj[e['from']].append(e['to'])
            adj[e['to']].append(e['from'])

        while queue:
            u = queue.pop(0)
            for v in adj[u]:
                if v not in visited:
                    visited.add(v)
                    self.parent_of[v] = u
                    children_of.setdefault(u, []).append(v)
                    children_of.setdefault(v, [])
                    queue.append(v)

        self.children_of_map = children_of

        # Сохраняем label рёбер (если были) по обоим направлениям,
        # чтобы при нормализации не потерять.
        label_map = {}
        for e in self.edges:
            if e.get('label') is not None:
                label_map[(e['from'], e['to'])] = e['label']
                label_map[(e['to'], e['from'])] = e['label']

        # Перестраиваем self.edges: каждое ребро = parent → child.
        new_edges = []
        for nid, parent in self.parent_of.items():
            if parent is None:
                continue
            edge = {'from': parent, 'to': nid}
            label = label_map.get((parent, nid))
            if label is not None:
                edge['label'] = label
            new_edges.append(edge)
        self.edges = new_edges

    def handle(self, component, params):
        if component == 'add_child':
            return self.add_child(
                params['parent_id'],
                params['value'],
                params.get('label'),
            )
        if component == 'remove_leaf':
            return self.remove_leaf(params['node_id'])
        if component == 'highlight_path':
            return self.highlight_path(
                params['from_id'],
                params['to_id'],
                params.get('color'),
            )
        # Всё остальное — из GraphStructure (create_graph, highlight_node, ...)
        return super().handle(component, params)

    # ---------- neighbors ----------

    def neighbors(self, node_id):
        nid = self._to_index(node_id)
        children = list(self.children_of_map.get(nid, []))
        children.sort(key=lambda c: (self._value_of_id(c), c))
        return children

    # ---------- Раскладка ----------

    def ensure_layout(self):
        if self._layout_version >= self._version:
            return

        # Для дерева иерархическая раскладка.
        # Передаём prev_layout для потенциального warm start.
        self._layout = compute_tree_layout(
            self.nodes, self.edges, root_id=self.root_id,
            scale=self._layout_scale,
            prev_layout=self._layout,
        )
        self._layout_version = self._version

    def children_of(self, node_id):
        """
        Список id детей, отсортированный по значению (value) детей.
        Для BST это даёт порядок [левый, правый]:
        children[0] — меньший ребёнок, children[-1] — больший.
        """
        children = list(self.children_of_map.get(self._to_index(node_id), []))
        children.sort(key=lambda c: (self._value_of_id(c), c))
        return children

    def _value_of_id(self, node_id):
        """Внутренний: значение узла по id (для сортировки и сравнений)."""
        nid = self._to_index(node_id)
        for n in self.nodes:
            if n['id'] == nid:
                return n.get('value', nid)
        raise ValueError(f"Tree: node {node_id} not found")

    def value_of(self, node_id):
        """Публичный: значение узла по id. Используется в DSL для BST."""
        return self._value_of_id(node_id)

    # ---------- Динамика ----------

    def add_child(self, parent_id, value, label=None):
        """
        Добавить ребёнка к parent_id. child_id генерируется автоматически,
        value сохраняется отдельно (может повторяться в BST-дублях).
        Возвращает сырые команды.
        """
        parent_id = self._to_index(parent_id)

        new_id = self._next_id
        self._next_id += 1

        self.nodes.append({
            'id': new_id,
            'label': label if label is not None else str(value),
            'value': value,
        })
        self.edges.append({'from': parent_id, 'to': new_id})
        self.children_of_map.setdefault(parent_id, []).append(new_id)
        self.children_of_map.setdefault(new_id, [])
        self.parent_of[new_id] = parent_id

        self._bump_version()

        return [self._tag({
            'component': 'replace_graph',
            'params': self._build_graph_params(),
        })]

    def remove_leaf(self, node_id):
        """Удалить лист. Если не лист — ошибка."""
        node_id = self._to_index(node_id)
        if self.children_of_map.get(node_id):
            raise ValueError(f"Node {node_id} is not a leaf")
        if node_id == self.root_id:
            raise ValueError("Cannot remove root")

        parent = self.parent_of.get(node_id)
        if parent is not None:
            self.children_of_map[parent].remove(node_id)
        self.parent_of.pop(node_id, None)
        self.children_of_map.pop(node_id, None)
        self.nodes = [n for n in self.nodes if n['id'] != node_id]
        self.edges = [e for e in self.edges
                      if e['from'] != node_id and e['to'] != node_id]

        self._bump_version()

        return [self._tag({
            'component': 'replace_graph',
            'params': self._build_graph_params(),
        })]

    def highlight_path(self, from_id, to_id, color):
        """Подсветить путь между узлами from_id и to_id (через LCA)."""
        from_id = self._to_index(from_id)
        to_id = self._to_index(to_id)
        path = self._find_path(from_id, to_id)
        raw = []
        for node_id in path:
            self._colors[node_id] = color
            raw.append(self._tag({
                'component': 'highlight_node',
                'params': {'node_id': node_id, 'color': color},
            }))
        return raw

    def _find_path(self, a, b):
        path_a = self._path_from_root(a)
        path_b = self._path_from_root(b)
        i = 0
        while (i < len(path_a) and i < len(path_b)
               and path_a[i] == path_b[i]):
            i += 1
        # общий префикс + обратная часть A (без LCA) + часть B без LCA
        return path_a[:i] + list(reversed(path_a[i:])) + path_b[i:]

    def _path_from_root(self, node_id):
        path = []
        current = node_id
        while current is not None:
            path.append(current)
            current = self.parent_of.get(current)
        return list(reversed(path))

    # ---------- Снапшот ----------

    def build_snapshot_dict(self):
        self.ensure_layout()
        snapshot_nodes = []
        for node in self.nodes:
            nid = node.get('id')
            x, y = self._layout.get(nid, (0.0, 0.0))
            snapshot_nodes.append({
                'id': nid,
                'label': node.get('label', str(nid)),
                'value': node.get('value', nid),
                'x': x,
                'y': y,
                'color': self._colors.get(nid),
            })
        snapshot_edges = []
        for edge in self.edges:
            key = self._edge_key(edge['from'], edge['to'])
            snapshot_edges.append({
                'from': edge['from'],
                'to': edge['to'],
                'color': self._edge_colors.get(key),
                'label': edge.get('label'),
            })
        return {
            'type': 'tree',
            'directed': self.directed,
            'nodes': snapshot_nodes,
            'edges': snapshot_edges,
        }

    def _build_graph_params(self):
        """Полное состояние дерева в формате create_graph params."""
        self.ensure_layout()
        nodes_with_coords = []
        for node in self.nodes:
            nid = node.get('id')
            x, y = self._layout.get(nid, (0.0, 0.0))
            nodes_with_coords.append({
                'id': nid,
                'label': node.get('label', str(nid)),
                'value': node.get('value', nid),
                'x': x,
                'y': y,
                'color': self._colors.get(nid),
            })
        snapshot_edges = []
        for edge in self.edges:
            key = self._edge_key(edge['from'], edge['to'])
            snapshot_edges.append({
                'from': edge['from'],
                'to': edge['to'],
                'color': self._edge_colors.get(key),
                'label': edge.get('label'),
            })
        return {
            'nodes': nodes_with_coords,
            'edges': snapshot_edges,
            'directed': self.directed,
        }


# ======================= ФАБРИКА =======================

_STRUCTURES = {
    'vector': VectorStructure,
    'graph': GraphStructure,
    'tree': TreeStructure,
}


def create_structure(type_name: str, data, name: str = None) -> Structure:
    if type_name not in _STRUCTURES:
        raise ValueError(f"Unknown structure type: {type_name}")
    structure = _STRUCTURES[type_name](data)
    structure.name = name
    return structure
