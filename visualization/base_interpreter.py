import re
from typing import Dict, Any, List


class BaseInterpreter:
    def __init__(self):
        self.functions = {
            'length': lambda x: len(x),
            'range': lambda start, end: list(range(start, end)),
            'increment': lambda x: x + 1,
            'decrement': lambda x: x - 1,
            'get_element_position': self.get_element_position,
            'swap': self._swap_array_elements,
            'neighbors': self._get_neighbors
        }
        self._base_element_size = 40
        self._command_counter = 0
        self._snapshots = []

    def _swap_array_elements(self, array, i1, i2):
        result = array.copy()
        result[i1], result[i2] = result[i2], result[i1]
        return result

    def _get_neighbors(self, state, node):
        return []

    def get_element_position(self, element_id: str, state: dict) -> dict:
        return {'x': state.get(f'{element_id}_x', 0), 'y': state.get(f'{element_id}_y', 0)}

    def _merge_settings(self, default: Dict, user: Dict) -> Dict:
        result = default.copy() if default else {}
        if 'colors' in user:
            if 'colors' not in result:
                result['colors'] = {}
            result['colors'].update(user['colors'])
        for key, value in user.items():
            if key != 'colors':
                result[key] = value
        return result

    def _substitute_templates(self, params: Dict, state: Dict) -> Dict:
        def replace_value(value):
            if isinstance(value, str):
                def replacer(match):
                    expr = match.group(1).strip()
                    result = self._evaluate_expression(expr, state)
                    return str(result) if result is not None else ''
                return re.sub(r'\{\{(.+?)\}\}', replacer, value)
            elif isinstance(value, dict):
                return {k: replace_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [replace_value(item) for item in value]
            else:
                return value
        return replace_value(params)

    def _apply_settings(self, params: Dict, settings: Dict) -> Dict:
        result = params.copy()
        if 'color' in result:
            color_value = result['color']
            if isinstance(color_value, str):
                clean_color = color_value.strip()
                if clean_color.startswith('{{') and clean_color.endswith('}}'):
                    clean_color = clean_color[2:-2]
                if clean_color.startswith('colors.'):
                    color_key = clean_color.split('.')[1]
                    color_from_settings = settings.get('colors', {}).get(color_key)
                    if color_from_settings:
                        result['color'] = color_from_settings
                    else:
                        result['color'] = '#000000'
        return result

    def _evaluate_expression(self, expr: str, state: Dict) -> Any:
        expr = expr.strip()

        # ---------- НОВОЕ: литерал списка ----------
        if expr.startswith('[') and expr.endswith(']'):
            inner = expr[1:-1].strip()
            if inner == '':
                return []
            items = []
            current = ''
            brackets = 0
            for ch in inner:
                if ch == ',' and brackets == 0:
                    items.append(current.strip())
                    current = ''
                else:
                    if ch == '[':
                        brackets += 1
                    elif ch == ']':
                        brackets -= 1
                    current += ch
            if current.strip():
                items.append(current.strip())
            result = []
            for it in items:
                if it.strip():
                    result.append(self._evaluate_expression(it, state))
                else:
                    result.append(None)
            return result

        if expr in state:
            return state[expr]
        try:
            if '.' in expr:
                return float(expr)
            return int(expr)
        except ValueError:
            pass

        for op in ['+', '-', '*', '/']:
            if op in expr:
                parts = expr.rsplit(op, 1)
                if len(parts) == 2:
                    left = self._evaluate_expression(parts[0].strip(), state)
                    right = self._evaluate_expression(parts[1].strip(), state)
                    if op == '+':
                        if isinstance(left, list) and isinstance(right, list):
                            return left + right
                        if isinstance(left, (int, float)) and isinstance(right, (int, float)):
                            return left + right
                    elif op == '-':
                        if isinstance(left, (int, float)) and isinstance(right, (int, float)):
                            return left - right
                    elif op == '*':
                        if isinstance(left, (int, float)) and isinstance(right, (int, float)):
                            return left * right
                    elif op == '/':
                        if isinstance(left, (int, float)) and isinstance(right, (int, float)) and right != 0:
                            return left / right

        # Доступ по индексу
        array_match = re.match(r'^(\w+)\[([^\]]+)\]$', expr)
        if array_match:
            var_name = array_match.group(1)
            index_expr = array_match.group(2)
            array = self._evaluate_expression(var_name, state)
            index = self._evaluate_expression(index_expr, state)
            if isinstance(array, list) and isinstance(index, int):
                return array[index]

        # Срезы
        slice_match = re.match(r'^(\w+)\[([^\[\]]*):([^\[\]]*)\]$', expr)
        if slice_match:
            var_name = slice_match.group(1)
            start_expr = slice_match.group(2).strip()
            end_expr = slice_match.group(3).strip()
            lst = self._evaluate_expression(var_name, state)
            if not isinstance(lst, list):
                raise ValueError(f"Cannot slice non-list: {var_name}")
            start = self._evaluate_expression(start_expr, state) if start_expr else None
            end = self._evaluate_expression(end_expr, state) if end_expr else None
            if start is None and end is None:
                return lst[:]
            if start is None:
                return lst[:end]
            if end is None:
                return lst[start:]
            return lst[start:end]

        # Вызов функции
        func_match = re.match(r'^(\w+)\(([^)]*)\)$', expr)
        if func_match:
            func_name = func_match.group(1)
            args_str = func_match.group(2)
            args = []
            if args_str.strip():
                for arg in args_str.split(','):
                    args.append(self._evaluate_expression(arg.strip(), state))
            if func_name in self.functions:
                if func_name == 'neighbors':
                    return self.functions[func_name](state, *args)
                return self.functions[func_name](*args)
            if func_name == 'len':
                if len(args) != 1:
                    raise ValueError("len() takes exactly one argument")
                return len(args[0])

        return expr

    def _evaluate_condition(self, condition: str, state: Dict) -> bool:
        condition = condition.strip()
        if ' not in ' in condition:
            parts = condition.split(' not in ')
            left = self._evaluate_expression(parts[0].strip(), state)
            right = self._evaluate_expression(parts[1].strip(), state)
            return left not in right
        if ' in ' in condition:
            parts = condition.split(' in ')
            left = self._evaluate_expression(parts[0].strip(), state)
            right = self._evaluate_expression(parts[1].strip(), state)
            return left in right

        for op in ['>=', '<=', '!=', '==', '>', '<']:
            if op in condition:
                parts = condition.split(op, 1)
                left = self._evaluate_expression(parts[0].strip(), state)
                right = self._evaluate_expression(parts[1].strip(), state)
                if op == '>':
                    return left > right
                if op == '<':
                    return left < right
                if op == '>=':
                    return left >= right
                if op == '<=':
                    return left <= right
                if op == '==':
                    return left == right
                if op == '!=':
                    return left != right
        return bool(self._evaluate_expression(condition, state))

    def _record_command(self, command: Dict, state: Dict, commands: List) -> None:
        command_index = self._command_counter
        self._command_counter += 1
        commands.append(command)
        self._save_snapshot(state, command_index)

    def _add_command_no_snapshot(self, command: Dict, commands: List) -> None:
        self._command_counter += 1
        commands.append(command)

    def _save_snapshot(self, state: Dict, command_index: int) -> None:
        raise NotImplementedError

    def _execute_step(self, step: Dict, state: Dict, settings: Dict, commands: List) -> None:
        for cmd in step['commands']:
            self._execute_command(cmd, state, settings, commands)

    def _execute_command(self, command: Dict, state: Dict, settings: Dict, commands: List) -> None:
        component = command['component']
        if component == 'while_loop':
            self._handle_while_loop(command, state, settings, commands)
        elif component == 'for_each':
            self._handle_for_each(command, state, settings, commands)
        elif component == 'condition':
            self._handle_condition(command, state, settings, commands)
        elif component == 'set_variable':
            self._handle_set_variable(command, state, settings, commands)
        elif component == 'wait':
            processed_params = self._substitute_templates(command['params'], state)
            processed_params = self._apply_settings(processed_params, settings)
            cmd = {'component': 'wait', 'params': processed_params}
            self._record_command(cmd, state, commands)
        else:
            self._handle_specific_command(command, state, settings, commands)

    def _handle_specific_command(self, command, state, settings, commands):
        raise ValueError(f"Unknown component: {command['component']}")

    def _handle_while_loop(self, command, state, settings, commands):
        condition = command['condition']
        while self._evaluate_condition(condition, state):
            for subcmd in command['commands']:
                self._execute_command(subcmd, state, settings, commands)

    def _handle_for_each(self, command, state, settings, commands):
        items_expr = command['items']
        variable = command['variable']
        items = self._evaluate_expression(items_expr, state)
        for item in items:
            state[variable] = item
            for subcmd in command['commands']:
                self._execute_command(subcmd, state, settings, commands)

    def _handle_condition(self, command, state, settings, commands):
        condition = command['condition']
        condition_result = self._evaluate_condition(condition, state)
        if condition_result and 'then' in command:
            self._add_command_no_snapshot({
                'component': 'condition_true',
                'params': {'condition': condition, 'result': True}
            }, commands)
            for subcmd in command['then']:
                self._execute_command(subcmd, state, settings, commands)
        elif 'else' in command:
            self._add_command_no_snapshot({
                'component': 'condition_false',
                'params': {'condition': condition, 'result': False}
            }, commands)
            for subcmd in command['else']:
                self._execute_command(subcmd, state, settings, commands)

    def _handle_set_variable(self, command, state, settings, commands):
        variable = command['variable']
        value_expr = command['value']
        value = self._evaluate_expression(value_expr, state)
        state[variable] = value
        cmd = {
            'component': 'set_variable',
            'params': {'variable': variable, 'value': value}
        }
        self._record_command(cmd, state, commands)

    def execute_algorithm(self, algorithm_definition: Dict, input_data: Dict, settings: Dict) -> Dict:
        state = {}
        self._snapshots = []
        self._command_counter = 0

        for key, value in input_data.items():
            state[key] = value

        if 'initial_state' in algorithm_definition:
            for key, value in algorithm_definition['initial_state'].items():
                if isinstance(value, str):
                    state[key] = self._evaluate_expression(value, state)
                else:
                    state[key] = value

        commands = []
        self._generate_commands(algorithm_definition, state, settings, commands)
        return {'commands': commands, 'snapshots': self._snapshots}

    def _generate_commands(self, algorithm_definition, state, settings, commands):
        raise NotImplementedError
