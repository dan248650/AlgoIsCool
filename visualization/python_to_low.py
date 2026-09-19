import ast
from _ast import stmt
from typing import List, Dict, Any


class PythonToLowTransformer(ast.NodeVisitor):
    """
    Транслятор Python-кода в низкоуровневое JSON-описание.
    """

    def __init__(self):
        self.commands = []
        self.current_block = self.commands

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

    # ---------- Присваивание ----------
    def visit_Assign(self, node):
        if len(node.targets) != 1:
            raise SyntaxError("Поддерживается только присваивание одной переменной")
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            raise SyntaxError("Цель присваивания должна быть простым именем")
        var_name = target.id
        value_expr = ast.unparse(node.value).strip()
        self.current_block.append({
            "component": "set_variable",
            "variable": var_name,
            "value": value_expr
        })

    def visit_AugAssign(self, node):
        if isinstance(node.target, ast.Name):
            var = node.target.id
            # Преобразуем в эквивалентное присваивание: x = x + y
            left = ast.Name(id=var, ctx=ast.Load())
            right = node.value
            op = node.op
            # Создаём бинарное выражение
            binop = ast.BinOp(left=left, op=op, right=right)
            value = ast.unparse(binop).strip()
            self.current_block.append({
                "component": "set_variable",
                "variable": var,
                "value": value
            })
        else:
            # Не поддерживаем присваивания по индексу/атрибуту
            raise SyntaxError("Цель присваивания должна быть простым именем")

    # ---------- Вызовы функций (команды) ----------
    def visit_Expr(self, node):
        if isinstance(node.value, ast.Call):
            self._handle_call(node.value)

    # ---------- Обработка вызова ----------
    def _handle_call(self, call_node):
        func_name = ast.unparse(call_node.func).strip()
        mapping = {
            "create_elements": "create_elements",
            "highlight": "highlight",
            "unhighlight": "unhighlight",
            "swap_elements": "swap_elements",
            "move_straight": "move_straight",
            "set_opacity": "set_opacity",
            "wait": "wait",
            "create_graph": "create_graph",
            "highlight_node": "highlight_node",
            "unhighlight_node": "unhighlight_node",
            "highlight_edge": "highlight_edge",
            "unhighlight_edge": "unhighlight_edge",
            "set_node_label": "set_node_label",
        }
        if func_name not in mapping:
            # Неизвестная функция (возможно, это стандартная функция, например, print)
            raise SyntaxError(f"Неизвестная функция: {func_name}")

        component = mapping[func_name]
        args = call_node.args
        kwargs = {kw.arg: kw.value for kw in call_node.keywords}

        params = self._build_params(component, args, kwargs)
        self.current_block.append({
            "component": component,
            "params": params
        })

    # ---------- Построение параметров ----------
    def _build_params(self, component: str, args: list, kwargs: dict) -> dict:
        params = {}
        if component == "create_elements":
            params["array"] = self._expr_to_value(args[0]) if args else None
        elif component == "highlight":
            params["element_ids"] = self._extract_element_ids(args[0]) if args else []
            params["color"] = self._expr_to_value(kwargs.get("color", None))
            params["duration"] = self._expr_to_value(kwargs.get("duration", 600))
        elif component == "unhighlight":
            params["element_ids"] = self._extract_element_ids(args[0]) if args else []
            params["duration"] = self._expr_to_value(kwargs.get("duration", 400))
        elif component == "swap_elements":
            params["element1_id"] = self._expr_to_value(args[0]) if args else None
            params["element2_id"] = self._expr_to_value(args[1]) if len(args) > 1 else None
            params["duration"] = self._expr_to_value(kwargs.get("duration", 500))
        elif component == "move_straight":
            params["element_ids"] = self._extract_element_ids(args[0]) if args else []
            params["to_x"] = self._expr_to_value(args[1]) if len(args) > 1 else None
            params["to_y"] = self._expr_to_value(args[2]) if len(args) > 2 else None
            params["duration"] = self._expr_to_value(kwargs.get("duration", 500))
            params["easing"] = self._expr_to_value(kwargs.get("easing", "ease-in-out"))
        elif component == "set_opacity":
            params["element_ids"] = self._extract_element_ids(args[0]) if args else []
            params["opacity"] = self._expr_to_value(args[1]) if len(args) > 1 else None
            params["duration"] = self._expr_to_value(kwargs.get("duration", 300))
        elif component == "wait":
            params["duration"] = self._expr_to_value(args[0]) if args else 300
        elif component == "create_graph":
            params["nodes"] = self._expr_to_value(args[0]) if args else []
            params["edges"] = self._expr_to_value(args[1]) if len(args) > 1 else []
            params["directed"] = self._expr_to_value(kwargs.get("directed", False))
        elif component == "highlight_node":
            params["node_id"] = self._expr_to_value(args[0]) if args else None
            params["color"] = self._expr_to_value(kwargs.get("color", None))
            params["duration"] = self._expr_to_value(kwargs.get("duration", 600))
        elif component == "unhighlight_node":
            params["node_id"] = self._expr_to_value(args[0]) if args else None
            params["duration"] = self._expr_to_value(kwargs.get("duration", 400))
        elif component == "highlight_edge":
            params["from"] = self._expr_to_value(args[0]) if args else None
            params["to"] = self._expr_to_value(args[1]) if len(args) > 1 else None
            params["color"] = self._expr_to_value(kwargs.get("color", None))
            params["duration"] = self._expr_to_value(kwargs.get("duration", 600))
        elif component == "unhighlight_edge":
            params["from"] = self._expr_to_value(args[0]) if args else None
            params["to"] = self._expr_to_value(args[1]) if len(args) > 1 else None
            params["duration"] = self._expr_to_value(kwargs.get("duration", 400))
        elif component == "set_node_label":
            params["node_id"] = self._expr_to_value(args[0]) if args else None
            params["label"] = self._expr_to_value(args[1]) if len(args) > 1 else None
        return params

    # ---------- Вспомогательные методы ----------
    def _expr_to_value(self, node: Any) -> Any:
        """
        Преобразует AST-узел в значение.
        Если передан не-узел (число, строка), возвращает как есть.
        """
        if node is None:
            return None
        if isinstance(node, ast.AST):
            if isinstance(node, ast.Constant):
                return node.value
            return ast.unparse(node).strip()
        return node

    def _extract_element_ids(self, node: ast.AST) -> List[str]:
        """Извлекает список идентификаторов элементов, всегда возвращает список."""
        if isinstance(node, ast.List):
            return [self._expr_to_template(elt) for elt in node.elts]
        else:
            return [self._expr_to_template(node)]

    def _expr_to_template(self, node: ast.AST) -> str:
        """
        Преобразует AST-узел в шаблонную строку (с двойными фигурными скобками).
        Поддерживает f-строки и конкатенацию.
        """
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        if isinstance(node, ast.JoinedStr):
            parts = []
            for value in node.values:
                if isinstance(value, ast.Constant) and isinstance(value.value, str):
                    parts.append(value.value)
                elif isinstance(value, ast.FormattedValue):
                    expr = ast.unparse(value.value).strip()
                    parts.append(f"{{{{{expr}}}}}")
                else:
                    parts.append(ast.unparse(value).strip())
            return "".join(parts)
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            left = self._expr_to_template(node.left)
            right = self._expr_to_template(node.right)
            return left + right
        # Для всего остального используем unparse
        return ast.unparse(node).strip()

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

    # Определяем тип алгоритма (по наличию create_graph)
    algo_type = "array"
    for cmd in commands:
        if cmd["component"] == "create_graph":
            algo_type = "graph"
            break

    definition = {
        "type": algo_type,
        "initial_state": {},  # интерпретатор возьмёт всё из input_data
        "steps": [
            {
                "name": "Выполнение алгоритма",
                "commands": commands
            }
        ]
    }
    return definition
