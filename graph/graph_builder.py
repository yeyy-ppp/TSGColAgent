from __future__ import annotations

import ast
from pathlib import Path
from typing import Iterable

from .edge import StateEdge
from .node import StateNode
from .state_graph import StateFlowGraph


class StateGraphBuilder(ast.NodeVisitor):
    """Builds a practical state-flow graph from Python AST structures."""

    def __init__(self, source_path: str | Path):
        self.source_path = str(Path(source_path).resolve())
        self.source_text = Path(source_path).read_text(encoding="utf-8")
        self.source_lines = self.source_text.splitlines()
        self.graph = StateFlowGraph(source_path=self.source_path)
        self._counter = 0
        self._scope_stack: list[str] = []
        self._last_node_stack: list[str | None] = []
        self._ast_node_cache: dict[int, StateNode] = {}
        self._function_exit_stack: list[str] = []
        self._loop_stack: list[dict[str, object]] = []

    def build(self) -> StateFlowGraph:
        tree = ast.parse(self.source_text, filename=self.source_path)
        self.graph.metadata["module_docstring"] = ast.get_docstring(tree)
        self.graph.metadata["graph_kind"] = "Program-Test Evidence Graph"
        self.visit(tree)
        self._connect_orphans_to_end()
        self.graph.bump_version("source analysis completed")
        return self.graph

    def _new_id(self, prefix: str) -> str:
        self._counter += 1
        return f"{prefix}_{self._counter}"

    def _code_segment(self, node: ast.AST) -> str:
        try:
            return ast.get_source_segment(self.source_text, node) or ""
        except Exception:
            return ""

    def _node(self, node_type: str, ast_node: ast.AST, name: str = "") -> StateNode:
        cache_key = id(ast_node)
        if cache_key in self._ast_node_cache:
            return self._ast_node_cache[cache_key]
        lineno = getattr(ast_node, "lineno", 1)
        end_lineno = getattr(ast_node, "end_lineno", lineno)
        priority = {
            "Function": 0.8,
            "Class": 0.75,
            "Branch": 0.95,
            "Loop": 0.9,
            "Raise": 1.0,
            "Exception": 1.0,
            "Return": 0.75,
            "Call": 0.65,
            "Assert": 0.6,
            "Decorator": 0.55,
            "Async": 0.8,
            "Generator": 0.8,
            "With": 0.75,
            "Match": 0.95,
            "Lambda": 0.7,
            "End": 0.3,
            "Break": 0.7,
            "Continue": 0.7,
        }.get(node_type, 0.5)
        state_node = StateNode(
            node_id=self._stable_node_id(node_type, name or node_type, lineno),
            node_type=node_type,
            name=name or node_type,
            file_path=self.source_path,
            line_start=lineno,
            line_end=end_lineno,
            code=self._code_segment(ast_node).strip(),
            priority=priority,
            metadata={"scope": "::".join(self._scope_stack)},
        )
        self.graph.add_node(state_node)
        self._ast_node_cache[cache_key] = state_node
        return state_node

    def _stable_node_id(self, node_type: str, name: str, lineno: int) -> str:
        scope = "::".join(self._scope_stack)
        raw = f"program:{node_type.lower()}:{scope}:{name}:{lineno}"
        safe = "".join(ch if ch.isalnum() or ch in {":", "_", "-"} else "_" for ch in raw)
        if safe not in self.graph.nodes:
            return safe
        suffix = 2
        while f"{safe}:{suffix}" in self.graph.nodes:
            suffix += 1
        return f"{safe}:{suffix}"

    def _edge(self, source: str | None, target: str | None, edge_type: str = "flow", **metadata: object) -> None:
        if source and target and source != target:
            self.graph.add_edge(StateEdge(source=source, target=target, edge_type=edge_type, metadata=dict(metadata)))

    def _current_last(self) -> str | None:
        return self._last_node_stack[-1] if self._last_node_stack else None

    def _set_current_last(self, node_id: str | None) -> None:
        if self._last_node_stack:
            self._last_node_stack[-1] = node_id

    def _visit_sequence(self, statements: Iterable[ast.stmt], previous: str | None = None) -> str | None:
        self._last_node_stack.append(previous)
        for statement in statements:
            self.visit(statement)
        return self._last_node_stack.pop()

    def _visit_nested_block(self, start_from: str, statements: list[ast.stmt], edge_type: str) -> str | None:
        if not statements:
            return start_from
        first = self._peek_state_node(statements[0])
        if first:
            self._edge(start_from, first, edge_type)
        return self._visit_sequence(statements, start_from)

    def _peek_state_node(self, statement: ast.AST) -> str | None:
        node = self._state_node_for_statement(statement)
        return node.node_id if node else None

    def _state_node_for_statement(self, statement: ast.AST) -> StateNode | None:
        if id(statement) in self._ast_node_cache:
            return self._ast_node_cache[id(statement)]
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return self._node("Async" if isinstance(statement, ast.AsyncFunctionDef) else "Function", statement, statement.name)
        if isinstance(statement, ast.ClassDef):
            return self._node("Class", statement, statement.name)
        if isinstance(statement, ast.If):
            return self._node("Branch", statement, ast.unparse(statement.test))
        if isinstance(statement, (ast.For, ast.While)):
            name = f"while {ast.unparse(statement.test)}" if isinstance(statement, ast.While) else f"for {ast.unparse(statement.target)} in {ast.unparse(statement.iter)}"
            return self._node("Loop", statement, name)
        if isinstance(statement, ast.Try):
            return self._node("Exception", statement, "try")
        if isinstance(statement, (ast.With, ast.AsyncWith)):
            return self._node("With", statement, "with")
        if isinstance(statement, ast.Match):
            return self._node("Match", statement, f"match {ast.unparse(statement.subject)}")
        if isinstance(statement, ast.Return):
            return self._node("Return", statement, ast.unparse(statement.value) if statement.value else "return")
        if isinstance(statement, ast.Raise):
            return self._node("Raise", statement, ast.unparse(statement.exc) if statement.exc else "raise")
        if isinstance(statement, ast.Break):
            return self._node("Break", statement, "break")
        if isinstance(statement, ast.Continue):
            return self._node("Continue", statement, "continue")
        if isinstance(statement, ast.Assert):
            return self._node("Assert", statement, ast.unparse(statement.test))
        if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Call):
            return self._node("Call", statement.value, ast.unparse(statement.value.func))
        return None

    def _connect_orphans_to_end(self) -> None:
        if not self.graph.nodes:
            return
        end_node = StateNode(
            node_id="program:end:module",
            node_type="End",
            name="ModuleEnd",
            file_path=self.source_path,
            line_start=max(1, len(self.source_lines)),
            line_end=max(1, len(self.source_lines)),
            code="",
            priority=0.2,
        )
        self.graph.add_node(end_node)
        targets = {edge.source for edge in self.graph.edges}
        for node_id, node in list(self.graph.nodes.items()):
            if node_id != end_node.node_id and node_id not in targets and node.node_type in {"Return", "Raise", "Function"}:
                self._edge(node_id, end_node.node_id, "end")

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_function(node, async_function=False)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_function(node, async_function=True)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        class_node = self._node("Class", node, node.name)
        class_node.metadata.update(
            {
                "bases": [ast.unparse(base) for base in node.bases],
                "decorators": [ast.unparse(item) for item in node.decorator_list],
            }
        )
        self._edge(self._current_last(), class_node.node_id, "defines")
        previous = self._current_last()
        self._set_current_last(class_node.node_id)
        self._scope_stack.append(node.name)
        end = self._visit_sequence(node.body, class_node.node_id)
        if end:
            self._edge(end, class_node.node_id, "class_exit")
        self._scope_stack.pop()
        self._set_current_last(class_node.node_id if previous is None else class_node.node_id)

    def _visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef, async_function: bool) -> None:
        fn = self._node("Async" if async_function else "Function", node, node.name)
        inferred_annotations = {
            arg.arg: ast.unparse(arg.annotation) if arg.annotation else self._infer_argument_type(node, arg.arg)
            for arg in node.args.args
        }
        fn.metadata.update(
            {
                "args": [arg.arg for arg in node.args.args],
                "arg_annotations": inferred_annotations,
                "inferred_arg_types": {
                    arg.arg: inferred_annotations[arg.arg]
                    for arg in node.args.args
                    if arg.annotation is None and inferred_annotations[arg.arg]
                },
                "returns": ast.unparse(node.returns) if node.returns else None,
                "decorators": [ast.unparse(item) for item in node.decorator_list],
                "is_generator": any(isinstance(child, (ast.Yield, ast.YieldFrom)) for child in ast.walk(node)),
            }
        )
        self._edge(self._current_last(), fn.node_id, "defines")
        previous = self._current_last()
        self._set_current_last(fn.node_id)
        self._scope_stack.append(node.name)
        exit_node = StateNode(
            node_id=self._stable_node_id("End", f"{node.name}_exit", getattr(node, "end_lineno", node.lineno)),
            node_type="End",
            name=f"{node.name} exit",
            file_path=self.source_path,
            line_start=getattr(node, "end_lineno", node.lineno),
            line_end=getattr(node, "end_lineno", node.lineno),
            code="",
            priority=0.35,
            metadata={"scope": "::".join(self._scope_stack), "function": node.name},
        )
        self.graph.add_node(exit_node)
        self._function_exit_stack.append(exit_node.node_id)
        for decorator in node.decorator_list:
            dec = self._node("Decorator", decorator, ast.unparse(decorator))
            self._edge(fn.node_id, dec.node_id, "decorator")
        end = self._visit_sequence(node.body, fn.node_id)
        if end:
            self._edge(end, exit_node.node_id, "function_exit")
        self._function_exit_stack.pop()
        self._scope_stack.pop()
        self._set_current_last(fn.node_id if previous is None else fn.node_id)

    def _infer_argument_type(self, function: ast.FunctionDef | ast.AsyncFunctionDef, arg_name: str) -> str | None:
        """Infer only high-confidence categories for an unannotated parameter."""
        lower = arg_name.lower()
        if any(token in lower for token in {"text", "string", "word", "message", "name", "path", "sentence"}):
            return "str"
        if any(token in lower for token in {"items", "values", "numbers", "nums", "array", "list", "strings"}):
            return "list"
        if any(token in lower for token in {"mapping", "config", "options", "dictionary"}):
            return "dict"
        if lower in {"flag", "enabled", "active", "valid"} or lower.startswith(("is_", "has_")):
            return "bool"

        string_methods = {
            "lower", "upper", "strip", "lstrip", "rstrip", "split", "rsplit", "replace",
            "swapcase", "startswith", "endswith", "isdigit", "isalpha", "isalnum", "find",
            "rfind", "encode", "casefold", "capitalize", "title", "join",
        }
        mapping_methods = {"items", "keys", "values", "get", "setdefault", "update"}
        sequence_methods = {"append", "extend", "insert", "pop", "remove", "sort", "reverse", "count", "index"}
        for child in ast.walk(function):
            if isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute):
                if isinstance(child.func.value, ast.Name) and child.func.value.id == arg_name:
                    if child.func.attr in string_methods:
                        return "str"
                    if child.func.attr in mapping_methods:
                        return "dict"
                    if child.func.attr in sequence_methods:
                        return "list"
            if isinstance(child, ast.BinOp) and isinstance(child.op, ast.Add):
                operands = (child.left, child.right)
                if any(isinstance(item, ast.Name) and item.id == arg_name for item in operands):
                    other = operands[1] if isinstance(operands[0], ast.Name) and operands[0].id == arg_name else operands[0]
                    if isinstance(other, ast.Constant) and isinstance(other.value, str):
                        return "str"
            if isinstance(child, ast.For) and isinstance(child.iter, ast.Name) and child.iter.id == arg_name:
                return "list"
        return None

    def visit_If(self, node: ast.If) -> None:
        branch = self._node("Branch", node, ast.unparse(node.test))
        self._edge(self._current_last(), branch.node_id, "flow")
        join = self._join_node("if_join", node)
        body_end = self._visit_nested_block(branch.node_id, node.body, "true")
        else_end = self._visit_nested_block(branch.node_id, node.orelse, "false")
        if body_end:
            self._edge(body_end, join.node_id, "join")
        if node.orelse and else_end:
            self._edge(else_end, join.node_id, "join")
        else:
            self._edge(branch.node_id, join.node_id, "false")
        self._set_current_last(join.node_id)

    def visit_For(self, node: ast.For) -> None:
        loop = self._node("Loop", node, f"for {ast.unparse(node.target)} in {ast.unparse(node.iter)}")
        self._edge(self._current_last(), loop.node_id, "flow")
        exit_node = self._join_node("loop_exit", node)
        loop_context = {"continue": loop.node_id, "breaks": []}
        self._loop_stack.append(loop_context)
        body_end = self._visit_nested_block(loop.node_id, node.body, "loop_body")
        if body_end:
            self._edge(body_end, loop.node_id, "loop_back")
        else_end = self._visit_nested_block(loop.node_id, node.orelse, "loop_else")
        self._edge(loop.node_id, exit_node.node_id, "loop_exit")
        if else_end:
            self._edge(else_end, exit_node.node_id, "join")
        for break_node in loop_context["breaks"]:
            self._edge(str(break_node), exit_node.node_id, "loop_exit")
        self._loop_stack.pop()
        self._set_current_last(exit_node.node_id)

    def visit_While(self, node: ast.While) -> None:
        loop = self._node("Loop", node, f"while {ast.unparse(node.test)}")
        self._edge(self._current_last(), loop.node_id, "flow")
        exit_node = self._join_node("loop_exit", node)
        loop_context = {"continue": loop.node_id, "breaks": []}
        self._loop_stack.append(loop_context)
        body_end = self._visit_nested_block(loop.node_id, node.body, "loop_body")
        if body_end:
            self._edge(body_end, loop.node_id, "loop_back")
        else_end = self._visit_nested_block(loop.node_id, node.orelse, "loop_else")
        self._edge(loop.node_id, exit_node.node_id, "loop_exit")
        if else_end:
            self._edge(else_end, exit_node.node_id, "join")
        for break_node in loop_context["breaks"]:
            self._edge(str(break_node), exit_node.node_id, "loop_exit")
        self._loop_stack.pop()
        self._set_current_last(exit_node.node_id)

    def visit_Try(self, node: ast.Try) -> None:
        try_node = self._node("Exception", node, "try")
        self._edge(self._current_last(), try_node.node_id, "flow")
        body_end = self._visit_nested_block(try_node.node_id, node.body, "try_body")
        handler_ends: list[str] = []
        for handler in node.handlers:
            name = ast.unparse(handler.type) if handler.type else "Exception"
            handler_node = self._node("Exception", handler, f"except {name}")
            self._edge(try_node.node_id, handler_node.node_id, "except")
            end = self._visit_sequence(handler.body, handler_node.node_id)
            if end:
                handler_ends.append(end)
        else_end = self._visit_nested_block(body_end or try_node.node_id, node.orelse, "try_else")
        final_entry = self._peek_state_node(node.finalbody[0]) if node.finalbody else None
        if final_entry:
            for predecessor in [else_end, body_end, *handler_ends, try_node.node_id]:
                self._edge(predecessor, final_entry, "finally")
        final_end = self._visit_nested_block(else_end or body_end or try_node.node_id, node.finalbody, "finally")
        self._set_current_last(final_end or else_end or (handler_ends[-1] if handler_ends else None) or body_end or try_node.node_id)

    def visit_With(self, node: ast.With) -> None:
        with_node = self._node("With", node, "with")
        with_node.metadata["items"] = [ast.unparse(item.context_expr) for item in node.items]
        self._edge(self._current_last(), with_node.node_id, "flow")
        self._set_current_last(self._visit_sequence(node.body, with_node.node_id) or with_node.node_id)

    def visit_AsyncWith(self, node: ast.AsyncWith) -> None:
        self.visit_With(node)

    def visit_Match(self, node: ast.Match) -> None:
        match_node = self._node("Match", node, f"match {ast.unparse(node.subject)}")
        self._edge(self._current_last(), match_node.node_id, "flow")
        join = self._join_node("match_join", node)
        for case in node.cases:
            case_name = ast.unparse(case.pattern)
            case_node = self._node("Branch", case.pattern, f"case {case_name}")
            self._edge(match_node.node_id, case_node.node_id, "case")
            case_end = self._visit_sequence(case.body, case_node.node_id) or case_node.node_id
            self._edge(case_end, join.node_id, "join")
        self._set_current_last(join.node_id)

    def visit_Return(self, node: ast.Return) -> None:
        ret = self._node("Return", node, ast.unparse(node.value) if node.value else "return")
        self._edge(self._current_last(), ret.node_id, "return")
        if self._function_exit_stack:
            self._edge(ret.node_id, self._function_exit_stack[-1], "function_exit")
        self._set_current_last(None)

    def visit_Raise(self, node: ast.Raise) -> None:
        raise_node = self._node("Raise", node, ast.unparse(node.exc) if node.exc else "raise")
        self._edge(self._current_last(), raise_node.node_id, "raise")
        if self._function_exit_stack:
            self._edge(raise_node.node_id, self._function_exit_stack[-1], "exception_exit")
        self._set_current_last(None)

    def visit_Break(self, node: ast.Break) -> None:
        break_node = self._node("Break", node, "break")
        self._edge(self._current_last(), break_node.node_id, "break")
        if self._loop_stack:
            self._loop_stack[-1]["breaks"].append(break_node.node_id)
        self._set_current_last(None)

    def visit_Continue(self, node: ast.Continue) -> None:
        continue_node = self._node("Continue", node, "continue")
        self._edge(self._current_last(), continue_node.node_id, "continue")
        if self._loop_stack:
            self._edge(continue_node.node_id, str(self._loop_stack[-1]["continue"]), "loop_continue")
        self._set_current_last(None)

    def visit_Assert(self, node: ast.Assert) -> None:
        assert_node = self._node("Assert", node, ast.unparse(node.test))
        self._edge(self._current_last(), assert_node.node_id, "assert")
        self._set_current_last(assert_node.node_id)

    def visit_Expr(self, node: ast.Expr) -> None:
        if isinstance(node.value, ast.Call):
            self.visit(node.value)
        elif isinstance(node.value, ast.Lambda):
            self.visit(node.value)

    def visit_Call(self, node: ast.Call) -> None:
        call = self._node("Call", node, ast.unparse(node.func))
        call.metadata["args"] = [ast.unparse(arg) for arg in node.args]
        self._edge(self._current_last(), call.node_id, "call")
        self._set_current_last(call.node_id)
        self.generic_visit(node)

    def visit_Lambda(self, node: ast.Lambda) -> None:
        lambda_node = self._node("Lambda", node, "lambda")
        self._edge(self._current_last(), lambda_node.node_id, "lambda")
        self._set_current_last(lambda_node.node_id)

    def visit_Yield(self, node: ast.Yield) -> None:
        gen = self._node("Generator", node, ast.unparse(node.value) if node.value else "yield")
        self._edge(self._current_last(), gen.node_id, "yield")
        self._set_current_last(gen.node_id)

    def visit_YieldFrom(self, node: ast.YieldFrom) -> None:
        gen = self._node("Generator", node, ast.unparse(node.value))
        self._edge(self._current_last(), gen.node_id, "yield_from")
        self._set_current_last(gen.node_id)

    def _join_node(self, name: str, node: ast.AST) -> StateNode:
        lineno = getattr(node, "end_lineno", getattr(node, "lineno", 1))
        join = StateNode(
            node_id=self._stable_node_id("End", name, lineno),
            node_type="End",
            name=name,
            file_path=self.source_path,
            line_start=lineno,
            line_end=lineno,
            code="",
            priority=0.25,
            metadata={"scope": "::".join(self._scope_stack), "kind": name},
        )
        self.graph.add_node(join)
        return join
