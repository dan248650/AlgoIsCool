import igraph as ig
from .base_interpreter import BaseInterpreter
from typing import Dict, Any, List


class GraphInterpreter(BaseInterpreter):
    def __init__(self):
        super().__init__()
        self._layout_name = "kamada_kawai"  # можно переопределить в settings

    def _get_neighbors(self, state, node):
        adj = state.get('_adjacency', {})
        return adj.get(node, [])

    def _generate_commands(self, algorithm_definition: Dict, state: Dict, settings: Dict, commands: List) -> None:
        nodes = state.get('nodes', [])
        edges = state.get('edges', [])
        directed = state.get('directed', False)
        start_node = state.get('start_node', 0)

        if not nodes:
            raise ValueError("Граф не содержит узлов. Добавьте хотя бы один узел.")

        max_node_id = len(nodes) - 1
        for edge in edges:
            if edge['from'] < 0 or edge['from'] > max_node_id or edge['to'] < 0 or edge['to'] > max_node_id:
                raise ValueError(f"Ребро {edge['from']}→{edge['to']} ссылается на несуществующий узел. "
                                 f"Допустимые индексы: 0..{max_node_id}")

        if start_node < 0 or start_node > max_node_id:
            raise ValueError(f"Стартовый узел {start_node} вне допустимого диапазона (0..{max_node_id})")

        g = ig.Graph(directed=directed)
        g.add_vertices(len(nodes))
        g.add_edges([(e['from'], e['to']) for e in edges])

        if self._layout_name == "planar" and g.is_planar():
            layout = g.layout_planar()
        else:
            layout = g.layout(self._layout_name)

        coords = layout.coords
        scale = 100  # масштаб, клиент сможет дополнительно масштабировать/центрировать
        nodes_with_coords = []
        for i, node in enumerate(nodes):
            x = coords[i][0] * scale
            y = coords[i][1] * scale
            nodes_with_coords.append({
                'id': i,
                'label': node.get('label', str(i)),
                'x': x,
                'y': y,
                'color': None
            })

        state['graph'] = {
            'nodes': nodes_with_coords,
            'edges': edges,
            'directed': directed
        }
        adj = {i: [] for i in range(len(nodes))}
        for e in edges:
            adj[e['from']].append(e['to'])
            if not directed:
                adj[e['to']].append(e['from'])
        state['_adjacency'] = adj

        # команда создания графа
        create_cmd = {
            'component': 'create_graph',
            'params': {
                'nodes': nodes_with_coords,
                'edges': edges,
                'directed': directed
            }
        }
        self._record_command(create_cmd, state, commands)

        # выполнение шагов алгоритма (из БД)
        for step in algorithm_definition.get('steps', []):
            self._execute_step(step, state, settings, commands)

    def _handle_specific_command(self, command, state, settings, commands):
        component = command['component']
        if component == 'create_graph':
            raise ValueError("create_graph should not appear in steps")
        elif component == 'highlight_node':
            self._handle_highlight_node(command, state, settings, commands)
        elif component == 'unhighlight_node':
            self._handle_unhighlight_node(command, state, settings, commands)
        elif component == 'highlight_edge':
            self._handle_highlight_edge(command, state, settings, commands)
        elif component == 'unhighlight_edge':
            self._handle_unhighlight_edge(command, state, settings, commands)
        elif component == 'set_node_label':
            self._handle_set_node_label(command, state, settings, commands)
        else:
            raise ValueError(f"Unknown graph component: {component}")

    def _save_snapshot(self, state: Dict, command_index: int) -> None:
        graph_data = state.get('graph')
        if not graph_data:
            return
        nodes = graph_data['nodes']
        edges = graph_data['edges']
        directed = graph_data['directed']
        node_colors = state.get('_node_colors', {})
        edge_colors = state.get('_edge_colors', {})

        snapshot_nodes = []
        for node in nodes:
            nid = node['id']
            snapshot_nodes.append({
                'id': nid,
                'label': node.get('label', str(nid)),
                'x': node['x'],
                'y': node['y'],
                'color': node_colors.get(nid, None)
            })
        snapshot_edges = []
        for edge in edges:
            key = self._edge_key(edge['from'], edge['to'], directed)
            snapshot_edges.append({
                'from': edge['from'],
                'to': edge['to'],
                'color': edge_colors.get(key, None),
                'label': edge.get('label')
            })
        snapshot = {
            'type': 'graph',
            'commandIndex': command_index,
            'directed': state['graph']['directed'],
            'nodes': snapshot_nodes,
            'edges': snapshot_edges
        }
        self._snapshots.append(snapshot)

    # ---------- Обработчики графовых команд ----------
    def _handle_highlight_node(self, command, state, settings, commands):
        params = self._substitute_templates(command['params'], state)
        params = self._apply_settings(params, settings)
        try:
            node_id = int(params['node_id'])
        except (ValueError, TypeError):
            node_id = params['node_id']
        color = params['color']
        # Обновляем цвет узла в графе
        if '_node_colors' not in state:
            state['_node_colors'] = {}
        state['_node_colors'][node_id] = color
        # не изменяем node['color'] в оригинальном графе
        cmd = {'component': 'highlight_node', 'params': params}
        self._record_command(cmd, state, commands)

    def _handle_unhighlight_node(self, command, state, settings, commands):
        params = self._substitute_templates(command['params'], state)
        params = self._apply_settings(params, settings)
        try:
            node_id = int(params['node_id'])
        except (ValueError, TypeError):
            node_id = params['node_id']
        if '_node_colors' in state and node_id in state['_node_colors']:
            del state['_node_colors'][node_id]
        cmd = {'component': 'unhighlight_node', 'params': params}
        self._record_command(cmd, state, commands)

    def _edge_key(self, from_id, to_id, directed):
        if directed:
            return from_id, to_id
        else:
            return tuple(sorted((from_id, to_id)))

    def _handle_highlight_edge(self, command, state, settings, commands):
        params = self._substitute_templates(command['params'], state)
        params = self._apply_settings(params, settings)
        try:
            from_id = int(params['from'])
            to_id = int(params['to'])
        except (ValueError, TypeError):
            from_id = params['from']
            to_id = params['to']
        color = params['color']
        directed = state['graph']['directed']
        key = self._edge_key(from_id, to_id, directed)
        if '_edge_colors' not in state:
            state['_edge_colors'] = {}
        state['_edge_colors'][key] = color
        cmd = {'component': 'highlight_edge', 'params': params}
        self._record_command(cmd, state, commands)

    def _handle_unhighlight_edge(self, command, state, settings, commands):
        params = self._substitute_templates(command['params'], state)
        params = self._apply_settings(params, settings)
        try:
            from_id = int(params['from'])
            to_id = int(params['to'])
        except (ValueError, TypeError):
            from_id = params['from']
            to_id = params['to']
        directed = state['graph']['directed']
        key = self._edge_key(from_id, to_id, directed)
        if '_edge_colors' in state and key in state['_edge_colors']:
            del state['_edge_colors'][key]
        cmd = {'component': 'unhighlight_edge', 'params': params}
        self._record_command(cmd, state, commands)

    def _handle_set_node_label(self, command, state, settings, commands):
        params = self._substitute_templates(command['params'], state)
        params = self._apply_settings(params, settings)
        try:
            node_id = int(params['node_id'])
        except (ValueError, TypeError):
            node_id = params['node_id']
        label = params['label']
        for node in state['graph']['nodes']:
            if node['id'] == node_id:
                node['label'] = label
                break
        cmd = {'component': 'set_node_label', 'params': params}
        self._record_command(cmd, state, commands)
