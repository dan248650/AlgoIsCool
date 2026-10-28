import re
from typing import Dict, Any, List

from visualization.window import Window
from visualization.structure import create_structure


class BaseInterpreter:
    def __init__(self):
        self.functions = {
            'str': lambda x: str(x),
            'int': lambda x: int(x),
            'length': lambda x: len(x),
            'range': lambda *args: list(range(*args)),
            'increment': lambda x: x + 1,
            'decrement': lambda x: x - 1,
            'get_element_position': self.get_element_position,
            'swap': self._swap_array_elements,
            'neighbors': self._get_neighbors
        }
        self._base_element_size = 40
        self._command_counter = 0
        self._snapshots = []

        # Хранилища экземпляров
        self.variables = {}  # пользовательские переменные (int, str, list, dict, ...)
        self.windows = {}  # {window_id: Window}
        self.structures = {}  # {structure_name: Structure}

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
                # Полное совпадение: '{{expr}}' → сырое значение (int/list/...)
                stripped = value.strip()
                full = re.fullmatch(r'\{\{(.+?)\}\}', stripped, re.DOTALL)
                if full:
                    return self._evaluate_expression(full.group(1).strip(), state)

                # Частичное: 'elem_{{i}}' → склейка строк (прежнее поведение)
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

        # Литерал списка
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

        # Вызов функции.
        # Вызов функции или метода структуры — парсим вручную, чтобы
        # поддержать вложенные скобки (range(len(x))) и точечную
        # нотацию (g.neighbors(u)).
        call = self._parse_call(expr)
        if call is not None:
            head, method, args_exprs = call
            args = [self._evaluate_expression(a, state) for a in args_exprs]

            if method is not None:
                # name.method(...) — метод структуры.
                structure = self.structures.get(head)
                if structure is None:
                    raise ValueError(
                        f"Обращение к методу '{method}' у неизвестной "
                        f"структуры '{head}'"
                    )
                if not hasattr(structure, method):
                    raise ValueError(
                        f"Структура '{head}' не имеет метода '{method}'"
                    )
                return getattr(structure, method)(*args)

            # name(...) — глобальная функция.
            if head in self.functions:
                if head == 'neighbors':
                    return self.functions[head](state, *args)
                return self.functions[head](*args)
            if head == 'len':
                if len(args) != 1:
                    raise ValueError("len() takes exactly one argument")
                return len(args[0])

        for op in ['+', '*']:
            if op in expr:
                parts = expr.rsplit(op, 1)
                if len(parts) == 2:
                    left = self._evaluate_expression(parts[0].strip(), state)
                    right = self._evaluate_expression(parts[1].strip(), state)
                    if op == '+':
                        if isinstance(left, str) and isinstance(right, str):
                            return left + right
                    elif op == '*':
                        if isinstance(left, str) and isinstance(right, int):
                            return left * right
                        if isinstance(left, int) and isinstance(right, str):
                            return right * left

        return expr

    @staticmethod
    def _parse_call(expr: str):
        """
        Разбирает вызов целиком:
          name(arg1, arg2, ...)           → ('name', None, [args])
          name.method(arg1, arg2, ...)    → ('name', 'method', [args])
        Возвращает None, если expr не является вызовом целиком.
        Корректно обрабатывает вложенные скобки и запятые внутри скобок.
        """
        expr = expr.strip()
        m = re.match(r'^([A-Za-z_]\w*)\s*(?:\.\s*([A-Za-z_]\w*))?\s*\(', expr)
        if not m:
            return None

        head = m.group(1)
        method = m.group(2)
        open_idx = m.end() - 1

        depth = 0
        close_idx = -1
        for i in range(open_idx, len(expr)):
            c = expr[i]
            if c == '(':
                depth += 1
            elif c == ')':
                depth -= 1
                if depth == 0:
                    close_idx = i
                    break

        if close_idx == -1 or close_idx != len(expr) - 1:
            return None

        inner = expr[open_idx + 1:close_idx]
        if not inner.strip():
            return head, method, []

        args = []
        depth = 0
        current = ''
        for c in inner:
            if c in '([':
                depth += 1
                current += c
            elif c in ')]':
                depth -= 1
                current += c
            elif c == ',' and depth == 0:
                args.append(current.strip())
                current = ''
            else:
                current += c
        if current.strip():
            args.append(current.strip())

        return head, method, args

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

        # Если в текущем прогоне уже появились окна/структуры — мы в новом
        # стиле, снапшот должен быть глобальным. Иначе — legacy-путь для
        # старых описаний (linear-search, bubble-sort и т.п.), которые
        # работают через _handle_specific_command и не создают Structure.
        if self.structures or self.windows:
            self._save_global_snapshot(command_index)
        else:
            self._save_snapshot(state, command_index)

    def _save_global_snapshot(self, command_index: int) -> None:
        """
        Полная картина после команды с номером command_index:
        все окна + все структуры. Формат отличается от легаси-снапшота
        (там был один 'type' сверху). Различать их фронт будет по наличию
        ключа 'structures'.
        """
        snapshot = {
            'commandIndex': command_index,
            'windows': {
                wid: w.build_snapshot_dict() for wid, w in self.windows.items()
            },
            'structures': {
                name: s.build_snapshot_dict() for name, s in self.structures.items()
            },
        }
        self._snapshots.append(snapshot)

    def _record_structure_commands(self, raw_commands: List[Dict], commands: List) -> None:
        """
        Принимает «сырые» команды от структуры (у каждой уже проставлено
        поле 'structure' именем экземпляра). Присваивает глобальные номера,
        кладёт команды в общий поток и после каждой сохраняет ГЛОБАЛЬНЫЙ
        снапшот (все окна, все структуры).
        """
        if not raw_commands:
            return
        for raw in raw_commands:
            idx = self._command_counter
            self._command_counter += 1
            commands.append(raw)
            self._save_global_snapshot(idx)

    def _record_scene_command(self, command: Dict, commands: List) -> None:
        """Оконная команда верхнего уровня: пишет команду и глобальный снапшот."""
        idx = self._command_counter
        self._command_counter += 1
        commands.append(command)
        self._save_global_snapshot(idx)

    def _add_command_no_snapshot(self, command: Dict, commands: List) -> None:
        self._command_counter += 1
        commands.append(command)

    def _save_snapshot(self, state: Dict, command_index: int) -> None:
        raise NotImplementedError

    def _execute_step(self, step: Dict, state: Dict, settings: Dict, commands: List) -> None:
        for cmd in step['commands']:
            self._execute_command(cmd, state, settings, commands)

    def _execute_command(self, command: Dict, state: Dict, settings: Dict, commands: List) -> None:
        """Команды верхнего уровня"""
        component = command['component']
        if component == 'while_loop':
            self._handle_while_loop(command, state, settings, commands)
        elif component == 'for_each':
            self._handle_for_each(command, state, settings, commands)
        elif component == 'condition':
            self._handle_condition(command, state, settings, commands)
        elif component == 'set_variable':
            self._handle_set_variable(command, state, settings, commands)
        elif component == 'set_index':
            self._handle_set_index(command, state, settings, commands)
        elif component == 'set_attr':
            self._handle_set_attr(command, state, settings, commands)
        elif component == 'multi_assign':
            self._handle_multi_assign(command, state, settings, commands)
        elif component == 'wait':
            processed_params = self._substitute_templates(command['params'], state)
            processed_params = self._apply_settings(processed_params, settings)
            cmd = {'component': 'wait', 'params': processed_params}
            self._record_command(cmd, state, commands)
        elif component == 'create_window':
            self._handle_create_window(command, state, settings, commands)
        elif component == 'create_structure':
            self._handle_create_structure(command, state, settings, commands)
        elif component == 'add_structure_to_window':
            self._handle_add_structure_to_window(command, state, settings, commands)
        elif component == 'show_window':
            self._handle_show_window(command, state, settings, commands)
        elif component == 'hide_window':
            self._handle_hide_window(command, state, settings, commands)
        elif 'structure' in command:
            structure_name = command['structure']
            structure = self.structures.get(structure_name)
            if structure is None:
                raise ValueError(
                    f"Structure '{structure_name}' not found. "
                    f"Available: {list(self.structures.keys())}"
                )
            params = self._substitute_templates(command['params'], state)
            params = self._apply_settings(params, settings)
            raw = structure.handle(command['component'], params)
            self._record_structure_commands(raw, commands)
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
        if not variable.startswith('_'):
            self.variables[variable] = value
        cmd = {
            'component': 'set_variable',
            'params': {'variable': variable, 'value': value}
        }
        self._record_command(cmd, state, commands)

    def _handle_set_index(self, command, state, settings, commands):
        target = command['target']
        index_expr = command['index']
        value_expr = command['value']

        if target not in state:
            raise ValueError(
                f"set_index: переменная '{target}' не найдена в state. "
                f"Доступные: {sorted(state.keys())}"
            )
        container = state[target]
        if not isinstance(container, (list, dict)):
            raise ValueError(
                f"set_index: '{target}' имеет тип {type(container).__name__}, "
                f"индексация невозможна"
            )

        index = self._evaluate_expression(index_expr, state)
        value = self._evaluate_expression(value_expr, state)

        if isinstance(container, list):
            if not isinstance(index, int):
                raise ValueError(
                    f"set_index: индекс списка должен быть int, получено "
                    f"{type(index).__name__} ({index!r})"
                )
        container[index] = value

        cmd = {
            'component': 'set_index',
            'params': {'target': target, 'index': index, 'value': value}
        }
        self._record_command(cmd, state, commands)

    def _handle_set_attr(self, command, state, settings, commands):
        target = command['target']
        attr = command['attr']
        value_expr = command['value']

        if target not in state:
            raise ValueError(
                f"set_attr: переменная '{target}' не найдена в state. "
                f"Доступные: {sorted(state.keys())}"
            )
        obj = state[target]
        value = self._evaluate_expression(value_expr, state)

        if isinstance(obj, dict):
            obj[attr] = value
        else:
            try:
                setattr(obj, attr, value)
            except AttributeError as e:
                raise ValueError(
                    f"set_attr: не удалось установить {target}.{attr}: {e}"
                )

        cmd = {
            'component': 'set_attr',
            'params': {'target': target, 'attr': attr, 'value': value}
        }
        self._record_command(cmd, state, commands)

    def _handle_multi_assign(self, command, state, settings, commands):
        targets = command['targets']       # список dict-ов
        values_exprs = command['values']   # список строк-выражений

        # Python-семантика: сначала считаем все значения по старому состоянию,
        # потом присваиваем. Это важно для a, b = b, a.
        values = [self._evaluate_expression(v, state) for v in values_exprs]

        for t, value in zip(targets, values):
            kind = t['kind']
            if kind == 'name':
                state[t['name']] = value
                if not t['name'].startswith('_'):
                    self.variables[t['name']] = value
            elif kind == 'index':
                container = state.get(t['target'])
                if container is None:
                    raise ValueError(
                        f"multi_assign: переменная '{t['target']}' не найдена"
                    )
                if not isinstance(container, (list, dict)):
                    raise ValueError(
                        f"multi_assign: '{t['target']}' не индексируем "
                        f"({type(container).__name__})"
                    )
                idx = self._evaluate_expression(t['index'], state)
                if isinstance(container, list) and not isinstance(idx, int):
                    raise ValueError(
                        f"multi_assign: индекс списка должен быть int, "
                        f"получено {type(idx).__name__}"
                    )
                container[idx] = value
            elif kind == 'attr':
                obj = state.get(t['target'])
                if obj is None:
                    raise ValueError(
                        f"multi_assign: переменная '{t['target']}' не найдена"
                    )
                if isinstance(obj, dict):
                    obj[t['attr']] = value
                else:
                    try:
                        setattr(obj, t['attr'], value)
                    except AttributeError as e:
                        raise ValueError(
                            f"multi_assign: не удалось установить "
                            f"{t['target']}.{t['attr']}: {e}"
                        )

        cmd = {
            'component': 'multi_assign',
            'params': {'targets': targets, 'values': values}
        }
        self._record_command(cmd, state, commands)

    def _handle_create_structure(self, command, state, settings, commands):
        name = command['name']
        type_name = command['type']
        data = command.get('data', {})

        if name in self.structures:
            raise ValueError(f"Structure '{name}' already exists")

        # data может прийти:
        #   * готовым литералом (список / dict) — от python_to_low;
        #   * строкой-выражением («input_array», «my_nodes») — от python_to_low,
        #     если пользователь передал переменную в конструктор;
        #   * dict-ом со строковыми значениями (для графа) — прошерстим значения.
        if isinstance(data, str):
            data = self._evaluate_expression(data, state)
        elif isinstance(data, dict):
            data = {
                k: (self._evaluate_expression(v, state) if isinstance(v, str) else v)
                for k, v in data.items()
            }

        structure = create_structure(type_name, data, name=name)
        self.structures[name] = structure

        initial_component = 'create_graph' if type_name == 'graph' else 'create_elements'
        raw = structure.handle(initial_component, {})
        self._record_structure_commands(raw, commands)

    def _handle_create_window(self, command, state, settings, commands):
        window_id = command['window_id']
        if window_id in self.windows:
            raise ValueError(f"Window '{window_id}' already exists")
        title = command.get('title', window_id)
        self.windows[window_id] = Window(window_id, title)
        self._record_scene_command({
            'component': 'create_window',
            'window': window_id,
            'title': title,
        }, commands)

    def _handle_add_structure_to_window(self, command, state, settings, commands):
        structure_name = command['structure']
        window_id = command['window']

        structure = self.structures.get(structure_name)
        if structure is None:
            raise ValueError(f"Structure '{structure_name}' not found")
        window = self.windows.get(window_id)
        if window is None:
            raise ValueError(f"Window '{window_id}' not found")

        window.add_structure(structure)
        self._record_scene_command({
            'component': 'add_structure_to_window',
            'window': window_id,
            'structure': structure_name,
        }, commands)

    def _handle_show_window(self, command, state, settings, commands):
        window_id = command['window']
        window = self.windows.get(window_id)
        if window is None:
            raise ValueError(f"Window '{window_id}' not found")
        window.show()
        self._record_scene_command({
            'component': 'show_window',
            'window': window_id,
        }, commands)

    def _handle_hide_window(self, command, state, settings, commands):
        window_id = command['window']
        window = self.windows.get(window_id)
        if window is None:
            raise ValueError(f"Window '{window_id}' not found")
        window.hide()
        self._record_scene_command({
            'component': 'hide_window',
            'window': window_id,
        }, commands)

    def execute_algorithm(self, algorithm_definition: Dict, input_data: Dict, settings: Dict) -> Dict:
        state = {}
        self._snapshots = []
        self._command_counter = 0

        # Сброс хранилищ между запусками
        self.variables = {}
        self.windows = {}
        self.structures = {}

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
        """Базовая реализация: просто выполняет шаги по порядку.
        Legacy-интерпретаторы (Array/Graph) переопределяют это для своей
        подготовки — layout, _adjacency и т.п."""
        for step in algorithm_definition['steps']:
            self._execute_step(step, state, settings, commands)
