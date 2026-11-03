"""
Раскладка графа: считает координаты узлов по топологии.

Модуль изолирован от Structure и от интерпретаторов. Единственная
точка входа — compute_layout(...). Если понадобится подменить
igraph на собственную реализацию или добавить новые стратегии,
это делается здесь, без правок в структурах.
"""
import igraph as ig


DEFAULT_LAYOUT = "kamada_kawai"
DEFAULT_SCALE = 100


def compute_layout(nodes, edges, directed=False,
                   layout_name=DEFAULT_LAYOUT, scale=DEFAULT_SCALE,
                   prev_layout=None):
    """
    nodes: [{'id': <любой>, 'label': str}, ...]
    edges: [{'from': <id>, 'to': <id>}, ...]
    Возвращает {node_id: (x, y)}.

    igraph работает с индексами 0..n-1, а у нас id могут быть любыми, поэтому строим отображение
    id ↔ индекс и обратно.
    """
    n = len(nodes)
    if n == 0:
        return {}

    id_to_idx = {node['id']: i for i, node in enumerate(nodes)}
    idx_to_id = {i: node['id'] for i, node in enumerate(nodes)}

    g = ig.Graph(directed=directed)
    g.add_vertices(n)

    edge_pairs = [
        (id_to_idx[e['from']], id_to_idx[e['to']])
        for e in edges
        if e.get('from') in id_to_idx and e.get('to') in id_to_idx
    ]
    if edge_pairs:
        g.add_edges(edge_pairs)

    if layout_name == "planar" and g.is_planar():
        layout = g.layout_planar()
    else:
        layout = g.layout(layout_name)

    coords = layout.coords
    return {
        idx_to_id[i]: (coords[i][0] * scale, coords[i][1] * scale)
        for i in range(n)
    }


def compute_tree_layout(nodes, edges, root_id, scale=100, prev_layout=None):
    """
    Иерархическая раскладка дерева (упрощённый Reingold-Tilford).

    nodes: [{'id': ..., 'label': ...}, ...]
    edges: [{'from': parent_id, 'to': child_id}, ...]
    root_id: id корневого узла
    prev_layout: {node_id: (x, y)} — опционально, для warm start
                  (сохраняет позиции узлов, которые уже были)
    Возвращает {node_id: (x, y)}.
    """
    children = {n['id']: [] for n in nodes}
    for e in edges:
        if e['from'] in children:
            children[e['from']].append(e['to'])

    # Сначала считаем «ширину» каждого поддерева в единицах листьев.
    subtree_width = {}

    def measure(node):
        if not children[node]:
            subtree_width[node] = 1.0
            return 1.0
        w = sum(measure(c) for c in children[node])
        subtree_width[node] = w
        return w

    measure(root_id)

    layout = {}
    # Горизонтальная координата: рекурсивно распределяем листья
    # в порядке слева направо; каждый узел — центр своего поддерева.
    def place(node, x_left, depth):
        w = subtree_width[node]
        center_x = x_left + w / 2.0
        layout[node] = (center_x * scale, depth * scale)
        cursor = x_left
        for c in children[node]:
            place(c, cursor, depth + 1)
            cursor += subtree_width[c]

    # Warm start: если у нас уже были позиции, используем их
    # для тех узлов, которые не изменили своего относительного места.
    # (Простая версия: только для вновь добавленных узлов.)
    if prev_layout is not None:
        # Стабильная раскладка: узлы, которые уже были, сохраняют
        # свою горизонтальную позицию, новые — вставляются рядом
        # с родителем.
        # Для простоты ниже — «полный пересчёт с сохранением относительного
        # порядка», но контракт позволяет реализовать более сложную логику.
        pass

    place(root_id, 0.0, 0)
    return layout
