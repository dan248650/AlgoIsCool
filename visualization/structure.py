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
from .layout import compute_layout


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


# ======================= ФАБРИКА =======================

_STRUCTURES = {
    'vector': VectorStructure,
    'graph': GraphStructure,
}


def create_structure(type_name: str, data, name: str = None) -> Structure:
    if type_name not in _STRUCTURES:
        raise ValueError(f"Unknown structure type: {type_name}")
    structure = _STRUCTURES[type_name](data)
    structure.name = name
    return structure
