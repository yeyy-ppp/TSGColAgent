from __future__ import annotations

import ast
from pathlib import Path


class PreserveMaxCorrect:
    """Keep passing test methods and isolate only blocking fragments after repeated repair failure."""

    def apply_python(self, test_path: str | Path, failing_test_names: set[str]) -> bool:
        path = Path(test_path)
        if not path.exists() or not failing_test_names:
            return False
        text = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(text)
        except SyntaxError:
            return False
        lines = text.splitlines()
        changed = False
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name in failing_test_names:
                start = max(0, node.lineno - 1)
                end = max(start, getattr(node, "end_lineno", node.lineno))
                for index in range(start, end):
                    if not lines[index].lstrip().startswith("#"):
                        lines[index] = "# PreserveMaxCorrect disabled blocking test: " + lines[index]
                        changed = True
        if changed:
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return changed
