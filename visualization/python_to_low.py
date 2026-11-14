import ast
from _ast import stmt
from typing import List, Dict

from visualization.structure import STRUCTURE_REGISTRY

STRUCTURE_CTORS = {
    cls.python_class_name: (type_name, cls)
    for type_name, cls in STRUCTURE_REGISTRY.items()
}
# backward compat (для проверок "if name in STRUCTURE_CLASSES")
STRUCTURE_CLASSES = {n: t for n, (t, _) in STRUCTURE_CTORS.items()}

# Класс окна.
WINDOW_CLASS = 'Window'

# Методы окна: имя метода → компонент.
WINDOW_METHODS = {
    'show': 'show_window',
    'hide': 'hide_window',
    'attach': 'add_structure_to_window',
}

# Глобальные функции-команды: имя → компонент.
# (пока только wait; сюда же попадут print и т.п., когда появятся)
GLOBAL_FUNCTIONS = {
    'wait': 'wait',
}


class PythonToLowTransformer(ast.NodeVisitor):
    """
    Транслятор Python-кода в низкоуровневое JSON-описание.
    """

    def __init__(self):
        self.commands = []
        self.current_block = self.commands
        # {structure_name: type_name} — тип нужен для выбора класса-парсера
        self.structure_names = {}
        self.window_names = set()  # имена окон

    # ---------- Обход модуля ----------
    def visit_Module(self, node):
        module: stmt
        for module in node.body:
            self.visit(module)

    # ---------- Запрещённые конструкции ----------
    def visit_FunctionDef(self, node):
        raise SyntaxError(f"Определение функций не поддерживается (строка {node.lineno})")

    def visit_ClassDef(self, node):
        raise SyntaxError(f"Определение классов не поддерживается (строка {node.lineno})")

    def visit_Lambda(self, node):
        raise SyntaxError(f"Лямбда-выражения не поддерживаются (строка {node.lineno})")

    def visit_Try(self, node):
        raise SyntaxError(f"Блок try/except не поддерживается (строка {node.lineno})")

    def visit_With(self, node):
        raise SyntaxError(f"Блок with не поддерживается (строка {node.lineno})")

    def visit_AsyncFunctionDef(self, node):
        raise SyntaxError(f"Асинхронные функции не поддерживаются (строка {node.lineno})")

    def visit_Yield(self, node):
        raise SyntaxError(f"Yield не поддерживается (строка {node.lineno})")

    # ---------- Цикл for ----------
    def visit_For(self, node):
        items = ast.unparse(node.iter).strip()
        target = ast.unparse(node.target).strip()
        sub_commands = []
        old_block = self.current_block
        self.current_block = sub_commands
        module: stmt
        for module in node.body:
            self.visit(module)
        self.current_block = old_block
        self.current_block.append({
            "component": "for_each",
            "items": items,
            "variable": target,
            "commands": sub_commands
        })

    # ---------- Цикл while ----------
    def visit_While(self, node):
        condition = ast.unparse(node.test).strip()
        sub_commands = []
        old_block = self.current_block
        self.current_block = sub_commands
        module: stmt
        for module in node.body:
            self.visit(module)
        self.current_block = old_block
        self.current_block.append({
            "component": "while_loop",
            "condition": condition,
            "commands": sub_commands
        })

    # ---------- Условный оператор ----------
    def visit_If(self, node):
        condition = ast.unparse(node.test).strip()
        then_commands = []
        old_block = self.current_block
        self.current_block = then_commands
        module: stmt
        for module in node.body:
            self.visit(module)
        else_commands = []
        if node.orelse:
            self.current_block = else_commands
            for module in node.orelse:
                self.visit(module)
        self.current_block = old_block
        cmd = {
            "component": "condition",
            "condition": condition,
            "then": then_commands
        }
        if else_commands:
            cmd["else"] = else_commands
        self.current_block.append(cmd)

    # ---------- break / continue ----------
    def visit_Break(self, node):
        self.current_block.append({"component": "break_loop"})

    def visit_Continue(self, node):
        self.current_block.append({"component": "continue_loop"})

    # ---------- Присваивание ----------
    def visit_Assign(self, node):
        if len(node.targets) != 1:
            raise SyntaxError(
                f"Цепочка присваиваний (a = b = c) не поддерживается "
                f"(строка {node.lineno}). Разделите на отдельные строки."
            )

        target = node.targets[0]

        # 1. Конструктор структуры или окна — обрабатываем как раньше
        if (isinstance(target, ast.Name)
                and isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Name)):
            ctor_name = node.value.func.id
            if ctor_name in STRUCTURE_CLASSES:
                self._handle_create_structure(target.id, node.value, ctor_name)
                return
            if ctor_name == WINDOW_CLASS:
                self._handle_create_window(target.id, node.value)
                return

        # 2. Множественное присваивание: a, b, ... = expr1, expr2, ...
        if isinstance(target, ast.Tuple):
            if not isinstance(node.value, ast.Tuple):
                raise SyntaxError(
                    f"Ожидается кортеж значений справа от 'a, b, ...' "
                    f"(строка {node.lineno})"
                )
            if len(node.value.elts) != len(target.elts):
                raise SyntaxError(
                    f"Число целей ({len(target.elts)}) не совпадает "
                    f"с числом значений ({len(node.value.elts)}) "
                    f"(строка {node.lineno})"
                )
            targets = [self._describe_target(elt) for elt in target.elts]
            if any(t is None for t in targets):
                raise SyntaxError(
                    f"Неподдерживаемая цель в множественном присваивании "
                    f"(строка {node.lineno})"
                )
            values = [ast.unparse(v).strip() for v in node.value.elts]
            self.current_block.append({
                "component": "multi_assign",
                "targets": targets,
                "values": values,
            })
            return

        # 3. Одиночное присваивание
        t = self._describe_target(target)
        if t is None:
            raise SyntaxError(
                f"Неподдерживаемая цель присваивания (строка {node.lineno})"
            )
        value_expr = ast.unparse(node.value).strip()

        if t['kind'] == 'name':
            self.current_block.append({
                "component": "set_variable",
                "variable": t['name'],
                "value": value_expr,
            })
        elif t['kind'] == 'index':
            self.current_block.append({
                "component": "set_index",
                "target": t['target'],
                "index": t['index'],
                "value": value_expr,
            })
        elif t['kind'] == 'attr':
            self.current_block.append({
                "component": "set_attr",
                "target": t['target'],
                "attr": t['attr'],
                "value": value_expr,
            })

    def _handle_create_structure(self, name, call_node, ctor_name):
        type_name, cls = STRUCTURE_CTORS[ctor_name]
        data = cls.build_data(call_node, self._expr_to_data)
        self.structure_names[name] = type_name
        self.current_block.append({
            "component": "create_structure",
            "name": name,
            "type": type_name,
            "data": data,
        })

    def _handle_create_window(self, name, call_node):
        title = None
        if call_node.args:
            title = self._expr_to_data(call_node.args[0])
        self.window_names.add(name)
        self.current_block.append({
            "component": "create_window",
            "window_id": name,
            "title": title or name,
        })

    def _expr_to_data(self, node):
        """
        Литералы возвращаются как есть. Выражения (имена переменных,
        вызовы, арифметика) оборачиваются в {'$expr': ...}. Так интерпретатор
        не путает 'hierarchical' (литерал) с 'input_array' (имя переменной).
        """
        if node is None:
            return None
        try:
            return ast.literal_eval(node)
        except (ValueError, SyntaxError):
            return {"$expr": ast.unparse(node).strip()}

    def visit_AugAssign(self, node):
        op_str = self._op_to_str(node.op)
        if op_str is None:
            raise SyntaxError(
                f"Неподдерживаемый оператор присваивания (строка {node.lineno})"
            )

        left = ast.unparse(node.target).strip()
        right = ast.unparse(node.value).strip()
        value_expr = f"{left} {op_str} {right}"

        t = self._describe_target(node.target)
        if t is None:
            raise SyntaxError(
                f"Неподдерживаемая цель AugAssign (строка {node.lineno})"
            )

        if t['kind'] == 'name':
            self.current_block.append({
                "component": "set_variable",
                "variable": t['name'],
                "value": value_expr,
            })
        elif t['kind'] == 'index':
            self.current_block.append({
                "component": "set_index",
                "target": t['target'],
                "index": t['index'],
                "value": value_expr,
            })
        elif t['kind'] == 'attr':
            self.current_block.append({
                "component": "set_attr",
                "target": t['target'],
                "attr": t['attr'],
                "value": value_expr,
            })

    @staticmethod
    def _op_to_str(op):
        return {
            ast.Add: '+',
            ast.Sub: '-',
            ast.Mult: '*',
            ast.Div: '/',
            ast.FloorDiv: '//',
            ast.Mod: '%',
            ast.Pow: '**',
            ast.BitAnd: '&',
            ast.BitOr: '|',
            ast.BitXor: '^',
            ast.LShift: '<<',
            ast.RShift: '>>',
        }.get(type(op))

    def _describe_target(self, node):
        """
        Разбирает левую часть присваивания.
        Возвращает dict {'kind': 'name'|'index'|'attr', ...} или None.
        Проверяет, что obj.attr не указывает на структуру или окно.
        """
        if isinstance(node, ast.Name):
            return {'kind': 'name', 'name': node.id}

        if isinstance(node, ast.Subscript):
            if not isinstance(node.value, ast.Name):
                raise SyntaxError(
                    f"Поддерживается только простое имя слева от [ ] "
                    f"(строка {node.lineno}). Вложенные подписи arr[i][j] пока нет."
                )
            return {
                'kind': 'index',
                'target': node.value.id,
                'index': ast.unparse(node.slice).strip(),
            }

        if isinstance(node, ast.Attribute):
            if not isinstance(node.value, ast.Name):
                raise SyntaxError(
                    f"Поддерживается только obj.attr для простого obj "
                    f"(строка {node.lineno})"
                )
            obj_name = node.value.id
            if obj_name in self.structure_names or obj_name in self.window_names:
                raise SyntaxError(
                    f"Нельзя изменять атрибут структуры/окна: "
                    f"{obj_name}.{node.attr} (строка {node.lineno})"
                )
            return {'kind': 'attr', 'target': obj_name, 'attr': node.attr}

        return None

    # ---------- Вызовы функций (команды) ----------
    def visit_Expr(self, node):
        if isinstance(node.value, ast.Call):
            self._handle_call(node.value)

    # ---------- Обработка вызова ----------
    def _handle_call(self, call_node):
        func = call_node.func

        # ---- Метод: obj.method(...) ----
        if isinstance(func, ast.Attribute):
            obj_name = ast.unparse(func.value).strip()
            method_name = func.attr

            if obj_name in self.structure_names:
                self._handle_structure_method(obj_name, method_name, call_node)
                return

            if obj_name in self.window_names:
                self._handle_window_method(obj_name, method_name, call_node)
                return

            raise SyntaxError(
                f"Объект '{obj_name}' не опознан как структура или окно. "
                f"Перед вызовом метода его нужно создать конструктором "
                f"({', '.join(STRUCTURE_CLASSES)} или {WINDOW_CLASS})."
            )

        # ---- Простой вызов: func(...) ----
        if isinstance(func, ast.Name):
            func_name = func.id

            if func_name in STRUCTURE_CLASSES or func_name == WINDOW_CLASS:
                raise SyntaxError(
                    f"Конструктор '{func_name}(...)' должен стоять в правой части "
                    f"присваивания: '<имя> = {func_name}(...)'."
                )

            if func_name in GLOBAL_FUNCTIONS:
                component = GLOBAL_FUNCTIONS[func_name]
                params = self._build_global_params(func_name, call_node)
                self.current_block.append({
                    "component": component,
                    "params": params,
                })
                return

            raise SyntaxError(
                f"Функция '{func_name}(...)' не поддерживается. "
                f"Допустимые глобальные функции: {', '.join(GLOBAL_FUNCTIONS)}. "
                f"Для действий над структурой используйте метод: <структура>.{func_name}(...)."
            )

        raise SyntaxError(f"Неподдерживаемый вызов: {ast.unparse(call_node)}")

    def _handle_structure_method(self, structure_name, method_name, call_node):
        type_name = self.structure_names.get(structure_name)
        if type_name is None:
            raise SyntaxError(f"'{structure_name}' не является известной структурой")
        cls = STRUCTURE_REGISTRY[type_name]
        if method_name not in cls.COMMAND_METHODS:
            raise SyntaxError(
                f"У структуры '{structure_name}' ({type_name}) нет метода '{method_name}'. "
                f"Допустимые: {', '.join(sorted(cls.COMMAND_METHODS))}."
            )
        params = cls.parse_method(method_name, call_node, self._method_arg)
        self.current_block.append({
            "component": method_name,
            "structure": structure_name,
            "params": params,
        })

    def _handle_window_method(self, window_name, method_name, call_node):
        if method_name not in WINDOW_METHODS:
            raise SyntaxError(
                f"У окна '{window_name}' нет метода '{method_name}'. "
                f"Допустимые: {', '.join(sorted(WINDOW_METHODS))}."
            )

        component = WINDOW_METHODS[method_name]

        if method_name in ('show', 'hide'):
            self.current_block.append({
                "component": component,
                "window": window_name,
            })
            return

        if method_name == 'attach':
            if not call_node.args:
                raise SyntaxError(
                    f"{window_name}.attach(...) требует имя структуры аргументом."
                )
            arg = call_node.args[0]
            if not isinstance(arg, ast.Name):
                raise SyntaxError(
                    f"{window_name}.attach(...) принимает только имя структуры "
                    f"(простое имя, не выражение)."
                )
            structure_name = arg.id
            if structure_name not in self.structure_names:
                raise SyntaxError(
                    f"'{structure_name}' не является известной структурой — "
                    f"сначала создайте её конструктором."
                )
            self.current_block.append({
                "component": component,
                "window": window_name,
                "structure": structure_name,
            })
            return

    def _build_global_params(self, func_name, call_node):
        args = call_node.args
        kwargs = {kw.arg: kw.value for kw in call_node.keywords}

        if func_name == 'wait':
            if args:
                duration = self._method_arg(args[0])
            elif 'duration' in kwargs:
                duration = self._method_arg(kwargs['duration'])
            else:
                duration = 300
            return {'duration': duration}

        return {}

    def _method_arg(self, node):
        """
        Аргумент метода. Литералы возвращаются как есть; всё остальное
        оборачивается в шаблон {{...}}, чтобы интерпретатор подставил значение.
        """
        if node is None:
            return None
        try:
            return ast.literal_eval(node)
        except (ValueError, SyntaxError):
            return "{{" + ast.unparse(node).strip() + "}}"

    # ---------- Точка входа ----------
    def transform(self, code: str) -> List[Dict]:
        tree = ast.parse(code)
        self.visit(tree)
        return self.commands


# ---------- Функция-обёртка для генерации low-level ----------
def generate_low_level_from_python(python_code: str, input_data: Dict, settings: Dict) -> Dict:
    """
    Принимает Python-код, входные данные и настройки.
    Возвращает низкоуровневое definition в формате, совместимом с интерпретатором.
    """
    transformer = PythonToLowTransformer()
    try:
        commands = transformer.transform(python_code)
    except SyntaxError as e:
        raise RuntimeError(f"Ошибка синтаксиса: {e}")

    definition = {
        "initial_state": {},  # интерпретатор возьмёт всё из input_data
        "steps": [{"name": "Выполнение алгоритма", "commands": commands}],
    }
    return definition
