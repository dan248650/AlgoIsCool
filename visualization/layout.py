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
                   layout_name=DEFAULT_LAYOUT, scale=DEFAULT_SCALE):
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
