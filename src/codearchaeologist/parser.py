from __future__ import annotations

import ast
import tokenize
from pathlib import Path
from .collector import module_name_for_path
from .models import ClassInfo, FunctionInfo, ImportInfo, ModuleInfo


def parse_python_file(root: str | Path, file_path: str | Path) -> ModuleInfo:
    path = Path(file_path).resolve()
    name = module_name_for_path(root, path)
    source = ''
    try:
        with tokenize.open(path) as stream:
            source = stream.read()
        tree = ast.parse(source, filename=str(path))
    except (SyntaxError, UnicodeError, OSError) as exc:
        return ModuleInfo(name=name, file=str(path), loc=len(source.splitlines()),
                          syntax_error=str(exc), is_package=path.name == '__init__.py')
    module = ModuleInfo(name=name, file=str(path), loc=len(source.splitlines()),
                        is_package=path.name == '__init__.py')
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for item in node.names:
                module.imports.append(ImportInfo(item.name, item.name.split('.')[-1], item.asname,
                                                 node.lineno, 'import'))
        elif isinstance(node, ast.ImportFrom):
            for item in node.names:
                module.imports.append(ImportInfo(node.module or '', item.name, item.asname,
                                                 node.lineno, 'from', node.level))

    class Definitions(ast.NodeVisitor):
        def __init__(self):
            self.scope = []
            self.class_stack = []

        def visit_ClassDef(self, node):
            qualified = '.'.join([*self.scope, node.name])
            cls = ClassInfo(f'{name}:{qualified}', node.name, qualified, name, str(path),
                            node.lineno, node.end_lineno or node.lineno,
                            [_unparse(base) for base in node.bases], docstring=ast.get_docstring(node) or '')
            module.classes.append(cls)
            self.scope.append(node.name)
            self.class_stack.append(cls)
            self.generic_visit(node)
            self.class_stack.pop()
            self.scope.pop()

        def visit_FunctionDef(self, node):
            qualified = '.'.join([*self.scope, node.name])
            is_method = bool(self.class_stack and self.scope[-1] == self.class_stack[-1].name)
            class_name = self.class_stack[-1].qualified_name if is_method else None
            nodes = list(_scoped_walk(node))
            calls = sorted({call_name(item.func) for item in nodes
                            if isinstance(item, ast.Call) and call_name(item.func)})
            bindings = {}
            for item in nodes:
                if isinstance(item, (ast.Assign, ast.AnnAssign)):
                    value = item.value
                    targets = item.targets if isinstance(item, ast.Assign) else [item.target]
                    target_type = call_name(value.func) if isinstance(value, ast.Call) else None
                    if isinstance(item, ast.AnnAssign) and not target_type:
                        target_type = _unparse(item.annotation)
                    if target_type:
                        for target in targets:
                            if isinstance(target, ast.Name):
                                bindings[target.id] = target_type
            kind = 'method' if is_method else 'function'
            if isinstance(node, ast.AsyncFunctionDef):
                kind = 'async_' + kind
            args = [item.arg for item in node.args.posonlyargs + node.args.args]
            if node.args.vararg:
                args.append('*' + node.args.vararg.arg)
            args.extend(item.arg for item in node.args.kwonlyargs)
            if node.args.kwarg:
                args.append('**' + node.args.kwarg.arg)
            end = node.end_lineno or node.lineno
            function = FunctionInfo(
                id=f'{name}:{qualified}', name=node.name, qualified_name=qualified, module=name,
                file=str(path), line_start=node.lineno, line_end=end, kind=kind,
                class_name=class_name, args=args,
                decorators=[_unparse(item) for item in node.decorator_list],
                docstring=ast.get_docstring(node) or '', returns=_unparse(node.returns),
                calls=calls, complexity=_complexity(nodes), loc=end-node.lineno+1,
                bindings=bindings)
            module.functions.append(function)
            if is_method:
                self.class_stack[-1].methods.append(function.id)
            self.scope.append(node.name)
            self.generic_visit(node)
            self.scope.pop()

        visit_AsyncFunctionDef = visit_FunctionDef

    Definitions().visit(tree)
    module.main_calls = sorted({call_name(item.func) for item in _scoped_walk(tree)
                                if isinstance(item, ast.Call) and call_name(item.func)})
    return module


def _scoped_walk(root):
    yield root
    for child in ast.iter_child_nodes(root):
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            continue
        yield from _scoped_walk(child)


def call_name(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = call_name(node.value)
        return f'{base}.{node.attr}' if base else None
    if isinstance(node, ast.Call):
        return call_name(node.func)
    return None


def _unparse(node):
    return ast.unparse(node) if node is not None else ''


def _complexity(nodes):
    score = 1
    for node in nodes:
        if isinstance(node, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.ExceptHandler, ast.IfExp)):
            score += 1
        elif isinstance(node, ast.BoolOp):
            score += len(node.values) - 1
        elif isinstance(node, ast.comprehension):
            score += 1 + len(node.ifs)
        elif isinstance(node, ast.Match):
            score += sum(1 for case in node.cases if not (
                isinstance(case.pattern, ast.MatchAs) and case.pattern.pattern is None))
            score += sum(case.guard is not None for case in node.cases)
    return score
