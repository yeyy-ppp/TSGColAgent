from __future__ import annotations

from pathlib import Path
from typing import Any

from executor.coverage_runner import CoverageRunner
from executor.mutation_runner import MutationRunner
from executor.pytest_runner import PytestRunner
from executor.runtime_observer import RuntimeObserver


class PythonToolchain:
    language = "python"

    def __init__(self):
        self.pytest = PytestRunner()
        self.coverage = CoverageRunner()
        self.mutation = MutationRunner()
        self.runtime_observer = RuntimeObserver()

    def run(self, source_path: str | Path, test_path: str | Path, cwd: str | Path | None = None) -> dict[str, Any]:
        cwd = Path(cwd or Path(test_path).parent)
        pytest_result = self.pytest.run(test_path, cwd=cwd)
        if not pytest_result.passed:
            return {"language": self.language, "pytest": pytest_result.to_dict() if hasattr(pytest_result, "to_dict") else pytest_result.__dict__, "passed": False}
        coverage_result = self.coverage.run(source_path, test_path, cwd=cwd)
        mutation_result = self.mutation.run(source_path, test_path, cwd=cwd)
        observations = self.runtime_observer.collect(source_path, test_path)
        return {
            "language": self.language,
            "passed": True,
            "line_coverage": coverage_result.line_coverage,
            "branch_coverage": coverage_result.branch_coverage,
            "method_coverage": None,
            "mutation_score": mutation_result.score,
            "runtime_observations": [item.to_dict() for item in observations],
        }

