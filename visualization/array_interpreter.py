from .base_interpreter import BaseInterpreter
from typing import Dict, Any, List


class ArrayInterpreter(BaseInterpreter):
    def _generate_commands(self, algorithm_definition: Dict, state: Dict, settings: Dict, commands: List) -> None:
        for step in algorithm_definition['steps']:
            self._execute_step(step, state, settings, commands)

    def _execute_command(self, command: Dict, state: Dict, settings: Dict, commands: List) -> None:
        component = command['component']
        # Перехватываем set_variable, чтобы выполнить синхронизацию _elements
        if component == 'set_variable':
            self._handle_set_variable(command, state, settings, commands)
            return
        try:
            super()._execute_command(command, state, settings, commands)
            return
        except ValueError:
            pass

        # специфичные команды массивов
        if component == 'create_elements':
            self._handle_create_elements(command, state, settings, commands)
        elif component == 'highlight':
            self._handle_highlight(command, state, settings, commands)
        elif component == 'unhighlight':
            self._handle_unhighlight(command, state, settings, commands)
        elif component == 'swap_elements':
            self._handle_swap_elements(command, state, settings, commands)
        elif component == 'move_straight':
            self._handle_move_straight(command, state, settings, commands)
        elif component == 'set_opacity':
            self._handle_set_opacity(command, state, settings, commands)
        else:
            raise ValueError(f"Unknown array component: {component}")

    def _save_snapshot(self, state: Dict, command_index: int) -> None:
        array = state.get('array', [])
        if not array:
            return
        spacing = state.get('_spacing', 10)
        elements_data = state.get('_elements', {})
        elements = []
        for i, value in enumerate(array):
            elem_id = f"elem_{i}"
            x = i * (self._base_element_size + spacing)
            y = 50
            color = elements_data.get(elem_id, {}).get('color') if elem_id in elements_data else None
            elements.append({
                'id': elem_id,
                'value': value,
                'color': color,
                'x': x,
                'y': y
            })
        snapshot = {
            'baseElementSize': self._base_element_size,
            'commandIndex': command_index,
            'elements': elements
        }
        self._snapshots.append(snapshot)

    def _handle_create_elements(self, command, state, settings, commands):
        array = command['params']['array']
        if isinstance(array, str):
            array = self._evaluate_expression(array, state)
        if not isinstance(array, list):
            raise ValueError("Array must be a list")
        spacing = settings.get('spacing', 10)
        state['_spacing'] = spacing
        if '_elements' not in state:
            state['_elements'] = {}
        for i, value in enumerate(array):
            elem_id = f"elem_{i}"
            x = i * (self._base_element_size + spacing)
            y = 50
            state[f"{elem_id}_x"] = x
            state[f"{elem_id}_y"] = y
            state['_elements'][elem_id] = {
                'value': value,
                'x': x,
                'y': y,
                'color': None
            }
            cmd = {
                'component': 'create_element',
                'params': {'id': elem_id, 'value': value, 'x': x, 'y': y}
            }
            self._record_command(cmd, state, commands)

    def _handle_highlight(self, command, state, settings, commands):
        params = self._substitute_templates(command['params'], state)
        params = self._apply_settings(params, settings)
        elem_ids = params.get('element_ids', [])
        color = params.get('color')
        for elem_id in elem_ids:
            if elem_id in state.get('_elements', {}):
                state['_elements'][elem_id]['color'] = color
        cmd = {'component': 'highlight', 'params': params}
        self._record_command(cmd, state, commands)

    def _handle_unhighlight(self, command, state, settings, commands):
        params = self._substitute_templates(command['params'], state)
        params = self._apply_settings(params, settings)
        elem_ids = params.get('element_ids', [])
        for elem_id in elem_ids:
            if elem_id in state.get('_elements', {}):
                state['_elements'][elem_id]['color'] = None
        cmd = {'component': 'unhighlight', 'params': params}
        self._record_command(cmd, state, commands)

    def _handle_swap_elements(self, command, state, settings, commands):
        params = self._substitute_templates(command['params'], state)
        params = self._apply_settings(params, settings)
        elem1_id = params['element1_id']
        elem2_id = params['element2_id']
        elem1 = state['_elements'].get(elem1_id)
        elem2 = state['_elements'].get(elem2_id)
        if elem1 and elem2:
            elem1['x'], elem2['x'] = elem2['x'], elem1['x']
            elem1['y'], elem2['y'] = elem2['y'], elem1['y']
            state[f"{elem1_id}_x"] = elem1['x']
            state[f"{elem2_id}_x"] = elem2['x']
            state[f"{elem1_id}_y"] = elem1['y']
            state[f"{elem2_id}_y"] = elem2['y']
        cmd = {'component': 'swap_elements', 'params': params}
        self._record_command(cmd, state, commands)

    def _handle_move_straight(self, command, state, settings, commands):
        params = self._substitute_templates(command['params'], state)
        params = self._apply_settings(params, settings)
        elem_ids = params.get('element_ids', [])
        to_x = params.get('to_x')
        to_y = params.get('to_y')
        for elem_id in elem_ids:
            if elem_id in state.get('_elements', {}):
                state['_elements'][elem_id]['x'] = to_x
                state['_elements'][elem_id]['y'] = to_y
                state[f"{elem_id}_x"] = to_x
                state[f"{elem_id}_y"] = to_y
        cmd = {'component': 'move_straight', 'params': params}
        self._record_command(cmd, state, commands)

    def _handle_set_opacity(self, command, state, settings, commands):
        params = self._substitute_templates(command['params'], state)
        params = self._apply_settings(params, settings)
        cmd = {'component': 'set_opacity', 'params': params}
        self._record_command(cmd, state, commands)

    def _handle_set_variable(self, command, state, settings, commands):
        variable = command['variable']
        value_expr = command['value']
        value = self._evaluate_expression(value_expr, state)
        state[variable] = value
        if variable == 'array' and isinstance(value, list):
            for idx, val in enumerate(value):
                elem_id = f"elem_{idx}"
                if elem_id in state.get('_elements', {}):
                    state['_elements'][elem_id]['value'] = val
        cmd = {
            'component': 'set_variable',
            'params': {'variable': variable, 'value': value}
        }
        self._record_command(cmd, state, commands)
