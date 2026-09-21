from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

import pytest

DEFAULT_TARGET = Path(r'''D:\2025_7_8\17\0707_agent_project\My_Mutil_Agent_7_fixed\My_Mutil_Agent0830\My_Mutil_Agent\.test_tmp\final-py-20260830\test_batch_generate_tests_for_0\sources\task_000.py''')
TARGET_PATH = Path(os.environ.get('STATEFLOW_TARGET', DEFAULT_TARGET)).resolve()

def _target_module_name():
    parts = [DEFAULT_TARGET.stem]
    cursor = DEFAULT_TARGET.parent
    while (cursor / '__init__.py').is_file():
        parts.insert(0, cursor.name)
        cursor = cursor.parent
    search_root = cursor if len(parts) > 1 else DEFAULT_TARGET.parent
    search_text = str(search_root)
    if search_text not in sys.path:
        sys.path.insert(0, search_text)
    return '.'.join(parts) if len(parts) > 1 else 'stateflow_target'

def _load_target():
    module_name = _target_module_name()
    spec = importlib.util.spec_from_file_location(module_name, TARGET_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

@pytest.fixture(scope='module')
def target():
    return _load_target()

def test_add_case_1(target):
    result = target.add(1, 1)
    assert result == 2

def test_add_case_2(target):
    result = target.add(0, 0)
    assert result == 0

def test_add_case_3(target):
    result = target.add(10, 10)
    assert result == 20

def test_add_case_4(target):
    result = target.add(-1, -1)
    assert result == -2

def test_add_case_5(target):
    result = target.add(60, 60)
    assert result == 120

def test_add_case_6(target):
    result = target.add(90, 90)
    assert result == 180

def test_add_case_7(target):
    result = target.add(0, 1)
    assert result == 1

def test_add_case_8(target):
    result = target.add(1, 0)
    assert result == 1

def test_add_case_9(target):
    result = target.add(-1, 1)
    assert result == 0

def test_add_case_10(target):
    result = target.add(60, 90)
    assert result == 150
