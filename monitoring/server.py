from __future__ import annotations

import argparse
import copy
import hashlib
import json
import mimetypes
import logging
import os
import sys
import time
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock, Thread
from urllib.parse import parse_qs, urlparse

from agents.test_knowledge_agent import TestKnowledgeAgent
from llm_client import OpenAICompatibleLLM
from llm_config import LLMConfig
from graph.experience_memory import resolve_knowledge_store_path

from .dashboard_data import build_snapshot, experiment_id, historical_duration_by_dataset, knowledge_snapshot, state_model_artifact
from .chat_store import ChatStore
from .job_queue import ExperimentJob, ExperimentJobQueue
from .learning_queue import PendingKnowledgeLearningQueue
from .registry import ExperimentRegistry
from .system_catalog import system_catalog


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist"
REGISTRY = ExperimentRegistry(PROJECT_ROOT / ".monitoring" / "experiments.json")
CHATS = ChatStore(PROJECT_ROOT / ".monitoring" / "chats.json")
LEARNING_QUEUE = PendingKnowledgeLearningQueue(PROJECT_ROOT / ".monitoring" / "pending_knowledge_learning.json")
RUNNING_PROCESSES: dict[str, object] = {}
JOBS = ExperimentJobQueue(REGISTRY, RUNNING_PROCESSES)
SNAPSHOT_CACHE: dict[str, tuple[float, str, dict[str, object]]] = {}
SNAPSHOT_LOCKS: dict[str, Lock] = {}
SNAPSHOT_LOCKS_LOCK = Lock()
EXPANDED_EXPERIMENTS_CACHE: tuple[str, tuple[list[dict[str, object]], list[dict[str, object]]]] | None = None
EXPERIMENT_CARDS_CACHE: tuple[str, list[dict[str, object]]] | None = None
EXPANDED_EXPERIMENTS_LOCK = Lock()
EXPERIMENT_CARDS_LOCK = Lock()


def _read_object(path: Path) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _dataset_scope(name: str) -> str:
    if name == "HumanEval":
        return "file_function"
    if name == "TestEval":
        return "file_function_class"
    if name == "HumanEvalJava":
        return "file_class"
    if name.startswith("Defects4J_"):
        return "class_project"
    return "project_file"


def _file_revision(path: Path) -> tuple[str, int, int]:
    try:
        stat = path.stat()
        return str(path), stat.st_mtime_ns, stat.st_size
    except OSError:
        return str(path), 0, 0


def _snapshot_revision(record: dict[str, object]) -> str:
    """Invalidate completed snapshots when their persisted result changes."""
    root = Path(str(record.get("output_dir") or "")).resolve()
    revisions = [
        _file_revision(root / name)
        for name in (
            "all_datasets_summary.json",
            "batch_summary.json",
            "batch_runtime.json",
            "dataset_completion.json",
            "stateflow_summary.json",
            "state_flow_graph.json",
            "experiment_round_progress.json",
            "task_runtime.json",
        )
    ]
    return hashlib.sha256(json.dumps(revisions, ensure_ascii=False).encode("utf-8")).hexdigest()


def _expanded_experiments(records: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    """Expose every dataset in a master run as a first-class selectable view."""
    global EXPANDED_EXPERIMENTS_CACHE
    revisions = []
    for record in records:
        summary_path = Path(str(record.get("output_dir") or "")) / "all_datasets_summary.json"
        try:
            revisions.append((str(summary_path), summary_path.stat().st_mtime_ns))
        except OSError:
            revisions.append((str(summary_path), 0))
    cache_key = hashlib.sha256(json.dumps({"records": records, "revisions": revisions}, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")).hexdigest()
    with EXPANDED_EXPERIMENTS_LOCK:
        if EXPANDED_EXPERIMENTS_CACHE and EXPANDED_EXPERIMENTS_CACHE[0] == cache_key:
            return copy.deepcopy(EXPANDED_EXPERIMENTS_CACHE[1])
    visible: list[dict[str, object]] = []
    masters: list[dict[str, object]] = []
    seen: set[str] = set()
    for original in records:
        record = dict(original)
        root = Path(str(record.get("output_dir") or "")).resolve()
        lifecycle = str(record.get("execution_status") or "")
        if not root.exists() and lifecycle not in {"running", "queued"}:
            continue
        master = _read_object(root / "all_datasets_summary.json")
        entries = master.get("results") if isinstance(master.get("results"), list) else []
        if entries:
            master_record = {**record, "label": "全部数据集实验", "master_experiment": True}
            masters.append(master_record)
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                dataset = entry.get("dataset") if isinstance(entry.get("dataset"), dict) else {}
                embedded = entry.get("summary") if isinstance(entry.get("summary"), dict) else {}
                name = str(dataset.get("name") or "").strip()
                if not name:
                    continue
                output_dir = root / name
                if not output_dir.exists():
                    summary_path = Path(str(entry.get("summary_path") or ""))
                    if summary_path.exists():
                        output_dir = summary_path.parent
                if not output_dir.exists():
                    continue
                child_id = experiment_id(output_dir)
                if child_id in seen:
                    continue
                seen.add(child_id)
                language = str(dataset.get("language") or embedded.get("language") or "auto")
                visible.append(
                    {
                        "id": child_id,
                        "parent_id": record.get("id"),
                        "output_dir": str(output_dir.resolve()),
                        "label": name,
                        "registered_at": record.get("registered_at"),
                        "execution_status": entry.get("status") or lifecycle or "completed",
                        "started_at": embedded.get("started_at") or record.get("started_at"),
                        "finished_at": embedded.get("finished_at") or record.get("finished_at"),
                        "knowledge_store": record.get("knowledge_store"),
                        "language": language,
                        "scope": _dataset_scope(name),
                        "virtual_dataset": True,
                    }
                )
            continue
        item_id = str(record.get("id") or experiment_id(root))
        if item_id not in seen:
            seen.add(item_id)
            visible.append(record)
    result = (visible, masters)
    with EXPANDED_EXPERIMENTS_LOCK:
        EXPANDED_EXPERIMENTS_CACHE = (cache_key, copy.deepcopy(result))
    return result


class DashboardHandler(BaseHTTPRequestHandler):
    server_version = "TSGDashboard/1.0"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            self._json({"ok": True, "frontend_ready": (FRONTEND_DIST / "index.html").exists()})
            return
        if parsed.path == "/api/runtime":
            self._json(self._snapshot(parse_qs(parsed.query).get("experiment", [None])[0]))
            return
        if parsed.path == "/api/knowledge":
            item_id = parse_qs(parsed.query).get("experiment", [None])[0]
            self._json(knowledge_snapshot(self._knowledge_store(item_id)))
            return
        if parsed.path == "/api/catalog":
            self._json(system_catalog())
            return
        if parsed.path == "/api/chats":
            self._json({"chats": CHATS.list()})
            return
        if parsed.path.startswith("/api/chats/"):
            chat_id = parsed.path.split("/")[3]
            chat = CHATS.get(chat_id)
            self._json(chat if chat else {"error": "conversation not found"}, HTTPStatus.OK if chat else HTTPStatus.NOT_FOUND)
            return
        if parsed.path == "/api/artifact":
            query = parse_qs(parsed.query)
            self._artifact(query.get("experiment", [None])[0], query.get("path", [""])[0])
            return
        if parsed.path == "/api/artifact/raw":
            query = parse_qs(parsed.query)
            self._raw_artifact(query.get("experiment", [None])[0], query.get("path", [""])[0])
            return
        if parsed.path == "/api/events":
            self._events(parse_qs(parsed.query).get("experiment", [None])[0])
            return
        self._static(parsed.path)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        payload = self._body()
        if parsed.path == "/api/register":
            output_dir = str(payload.get("output_dir", "")).strip()
            if not output_dir:
                self._json({"error": "output_dir is required"}, HTTPStatus.BAD_REQUEST)
                return
            config = payload.get("llm_config") if isinstance(payload.get("llm_config"), dict) else None
            requested_metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
            metadata = {
                key: requested_metadata.get(key)
                for key in ["execution_status", "started_at", "knowledge_store"]
                if requested_metadata.get(key) is not None
            }
            self._json(REGISTRY.register(output_dir, str(payload.get("label") or "") or None, config, metadata), HTTPStatus.CREATED)
            return
        if parsed.path == "/api/chat":
            self._chat(payload)
            return
        if parsed.path == "/api/chats":
            self._json(CHATS.create(str(payload.get("title") or "") or None), HTTPStatus.CREATED)
            return
        if parsed.path.startswith("/api/chats/"):
            parts = parsed.path.strip("/").split("/")
            if len(parts) == 4 and parts[3] == "messages":
                self._chat_message(parts[2], payload)
                return
            if len(parts) == 4 and parts[3] == "rename":
                chat = CHATS.rename(parts[2], str(payload.get("title") or ""))
                self._json(chat if chat else {"error": "conversation not found"}, HTTPStatus.OK if chat else HTTPStatus.NOT_FOUND)
                return
        if parsed.path == "/api/experiments/start":
            self._start_experiment(payload)
            return
        if parsed.path == "/api/experiments/finish":
            self._finish_experiment(payload)
            return
        self._json({"error": "not found"}, HTTPStatus.NOT_FOUND)

    def do_DELETE(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/chats/"):
            chat_id = parsed.path.strip("/").split("/")[2]
            deleted = CHATS.delete(chat_id)
            self._json({"deleted": deleted}, HTTPStatus.OK if deleted else HTTPStatus.NOT_FOUND)
            return
        self._json({"error": "not found"}, HTTPStatus.NOT_FOUND)

    def _snapshot(self, item_id: str | None) -> dict[str, object]:
        experiments, masters = _expanded_experiments(REGISTRY.list())
        if item_id in {None, "all"} and masters:
            master = masters[0]
            snapshot = self._record_snapshot(master, experiments)
            cards = self._experiment_cards(experiments)
            duration_by_dataset = historical_duration_by_dataset(
                [item for item in snapshot.get("tasks", []) if isinstance(item, dict)],
                Path(str(master.get("output_dir") or "")).resolve(),
            )
            for card in cards:
                recovered = duration_by_dataset.get(str(card.get("label") or ""), 0.0)
                if recovered > float(card.get("duration_seconds") or 0.0):
                    card["duration_seconds"] = recovered
                    card["duration_source"] = "historical_task_runtime"
            status = str((snapshot.get("overview") or {}).get("status") or "completed")
            snapshot["experiment"] = {**master, "id": "all", "label": "实验总览", "status": status}
            snapshot["experiments"] = cards
            snapshot["portfolio"] = {
                "view": "all",
                "experiments": cards,
                "counts": {key: sum(1 for card in cards if card.get("status") == key) for key in ["running", "completed", "queued", "failed"]},
            }
            overview = snapshot.get("overview") if isinstance(snapshot.get("overview"), dict) else {}
            overview.update({"language": "mixed", "scope": "mixed_scope", "dataset_count": len(cards), "completed_datasets": sum(1 for card in cards if card.get("status") == "completed")})
            self._apply_control(snapshot, master)
            return snapshot
        if item_id in {"all", "running", "completed", "queued"}:
            return self._portfolio_snapshot(item_id or "all", experiments)
        record = next((record for record in [*experiments, *masters] if str(record.get("id")) == str(item_id)), None)
        if record is None:
            return self._empty_snapshot(experiments)
        snapshot = self._record_snapshot(record, experiments)
        snapshot["experiments"] = self._experiment_cards(experiments)
        if record.get("virtual_dataset") and isinstance(snapshot.get("overview"), dict):
            snapshot["overview"]["scope"] = record.get("scope") or "project_file"
            snapshot["overview"]["language"] = record.get("language") or snapshot["overview"].get("language")
        self._apply_control(snapshot, record)
        return snapshot

    def _record_snapshot(self, record: dict[str, object], experiments: list[dict[str, object]]) -> dict[str, object]:
        item_id = str(record.get("id"))
        execution_status = str(record.get("execution_status") or "")
        revision = _snapshot_revision(record)
        cached = SNAPSHOT_CACHE.get(item_id)
        ttl = 3600.0 if execution_status == "completed" else 1.0
        if cached and cached[1] == revision and time.monotonic() - cached[0] < ttl:
            return copy.deepcopy(cached[2])
        with SNAPSHOT_LOCKS_LOCK:
            lock = SNAPSHOT_LOCKS.setdefault(item_id, Lock())
        with lock:
            revision = _snapshot_revision(record)
            cached = SNAPSHOT_CACHE.get(item_id)
            if cached and cached[1] == revision and time.monotonic() - cached[0] < ttl:
                return copy.deepcopy(cached[2])
            snapshot = build_snapshot(record, experiments)
            SNAPSHOT_CACHE[item_id] = (time.monotonic(), revision, copy.deepcopy(snapshot))
            return snapshot

    def _apply_control(self, snapshot: dict[str, object], record: dict[str, object]) -> None:
        item_id = str(record.get("id"))
        process = RUNNING_PROCESSES.get(item_id)
        queue_state = JOBS.state(item_id)
        persisted_status = str(record.get("execution_status") or "")
        execution_status = str(queue_state.get("status") or (persisted_status if persisted_status != "running" or process else (snapshot.get("overview") or {}).get("status")) or "")
        snapshot["control"] = {
            "can_start": True,
            "process_id": getattr(process, "pid", None) if process else record.get("process_id"),
            "process_running": bool(process and process.poll() is None),
            "queue_position": queue_state.get("position"),
            "execution_status": execution_status or snapshot.get("overview", {}).get("status"),
            "log_path": str(Path(str(record.get("output_dir"))) / "experiment_process.log"),
        }
        config = self._llm_config(item_id)
        snapshot["assistant"] = {**config.public_dict(), "backend_managed": True, "api_key_configured": bool(config.api_key)}
        if process and process.poll() is None:
            snapshot["experiment"]["status"] = "running"
            snapshot["overview"]["status"] = "running"
        elif execution_status in {"queued", "failed", "completed"}:
            snapshot["experiment"]["status"] = execution_status
            snapshot["overview"]["status"] = execution_status

    def _experiment_cards(self, experiments: list[dict[str, object]]) -> list[dict[str, object]]:
        global EXPERIMENT_CARDS_CACHE
        revisions = []
        has_live_experiment = False
        for record in experiments:
            batch_path = Path(str(record.get("output_dir") or "")) / "batch_summary.json"
            queue_state = JOBS.state(str(record.get("id")))
            live_status = str(queue_state.get("status") or record.get("execution_status") or "")
            has_live_experiment = has_live_experiment or live_status in {"running", "queued"}
            try:
                revisions.append((str(record.get("id")), str(record.get("execution_status")), queue_state.get("status"), queue_state.get("position"), batch_path.stat().st_mtime_ns))
            except OSError:
                revisions.append((str(record.get("id")), str(record.get("execution_status")), queue_state.get("status"), queue_state.get("position"), 0))
        cache_key = hashlib.sha256(json.dumps(revisions, sort_keys=True).encode("utf-8")).hexdigest()
        if not has_live_experiment:
            with EXPERIMENT_CARDS_LOCK:
                if EXPERIMENT_CARDS_CACHE and EXPERIMENT_CARDS_CACHE[0] == cache_key:
                    return copy.deepcopy(EXPERIMENT_CARDS_CACHE[1])
        cards = []
        for record in experiments:
            item_id = str(record.get("id"))
            queue_state = JOBS.state(item_id)
            process = RUNNING_PROCESSES.get(item_id)
            raw_status = str(record.get("execution_status") or "")
            persisted = str(queue_state.get("status") or (raw_status if raw_status != "running" or process else "") or "")
            if persisted == "queued":
                cards.append({**record, "status": "queued", "language": _request_language(record), "scope": _request_scope(record), "total_tasks": 0, "completed_execution": 0, "not_completed_execution": 0, "progress": 0.0, "queue_position": queue_state.get("position"), "started_at": None, "finished_at": None, "duration_seconds": None})
                continue
            if record.get("virtual_dataset"):
                batch = _read_object(Path(str(record.get("output_dir"))) / "batch_summary.json")
                outcome = batch.get("outcome_summary") if isinstance(batch.get("outcome_summary"), dict) else {}
                total = int(outcome.get("total_tasks") or batch.get("total") or 0)
                completed = int(outcome.get("completed_execution") or 0)
                not_completed = int(outcome.get("not_completed_execution") or 0)
                status = str(record.get("execution_status") or "completed")
                cards.append({**record, "status": status, "language": batch.get("language") or record.get("language"), "scope": record.get("scope") or "project_file", "total_tasks": total, "completed_execution": completed, "not_completed_execution": not_completed, "progress": (completed + not_completed) / total if total else 0.0, "started_at": batch.get("first_started_at") or batch.get("started_at") or record.get("started_at"), "finished_at": batch.get("finished_at") or record.get("finished_at"), "duration_seconds": batch.get("cumulative_duration_seconds") or batch.get("duration_seconds")})
                continue
            snapshot = self._record_snapshot(record, experiments)
            overview = snapshot.get("overview") if isinstance(snapshot.get("overview"), dict) else {}
            status = persisted if persisted in {"running", "completed", "failed"} else str(overview.get("status") or persisted or "waiting")
            total = int(overview.get("total_tasks") or 0)
            completed = int(overview.get("completed_execution") or 0)
            not_completed = int(overview.get("not_completed_execution") or 0)
            progress = (completed + not_completed) / total if total else (1.0 if status == "completed" else 0.0)
            cards.append({**record, "status": status, "language": overview.get("language") or _request_language(record), "scope": overview.get("scope") or _request_scope(record), "total_tasks": total, "completed_execution": completed, "not_completed_execution": not_completed, "progress": progress, "queue_position": queue_state.get("position"), "started_at": overview.get("started_at"), "finished_at": overview.get("finished_at"), "duration_seconds": overview.get("duration_seconds")})
        if not has_live_experiment:
            with EXPERIMENT_CARDS_LOCK:
                EXPERIMENT_CARDS_CACHE = (cache_key, copy.deepcopy(cards))
        return cards

    def _portfolio_snapshot(self, view: str, experiments: list[dict[str, object]]) -> dict[str, object]:
        cards = self._experiment_cards(experiments)
        wanted = cards if view == "all" else [card for card in cards if card.get("status") == view]
        wanted_ids = {str(card.get("id")) for card in wanted if card.get("status") != "queued"}
        records = [record for record in experiments if str(record.get("id")) in wanted_ids]
        snapshots = []
        for record in records:
            snapshot = self._record_snapshot(record, experiments)
            self._apply_control(snapshot, record)
            snapshots.append(snapshot)
        focus = next((item for item in snapshots if (item.get("overview") or {}).get("status") == "running"), snapshots[0] if snapshots else None)
        tasks, events, failures = [], [], {}
        for snapshot in snapshots:
            experiment = snapshot.get("experiment") if isinstance(snapshot.get("experiment"), dict) else {}
            for task in snapshot.get("tasks", []):
                if isinstance(task, dict):
                    tasks.append({**task, "experiment_id": experiment.get("id"), "experiment_label": experiment.get("label")})
            for event in snapshot.get("flow_events", []):
                if isinstance(event, dict):
                    events.append({**event, "experiment_id": experiment.get("id"), "experiment_label": experiment.get("label")})
            if snapshot.get("failures"):
                failures[str(experiment.get("id"))] = snapshot.get("failures")
        if focus and isinstance(focus.get("experiment"), dict):
            focus_id = str((focus.get("experiment") or {}).get("id") or "")
            events.sort(key=lambda event: 1 if str(event.get("experiment_id") or "") == focus_id else 0)
        events = events[-240:]
        grade_counts = {
            grade: sum(1 for task in tasks if task.get("grade") == grade and task.get("status") != "running")
            for grade in "ABCDE"
        }
        completed = sum(grade_counts[grade] for grade in "ABC")
        not_completed = sum(grade_counts[grade] for grade in "DE")
        graded_total = completed + not_completed
        overall_quality_index = (
            sum(grade_counts[grade] * weight for grade, weight in {"A": 1.0, "B": 0.82, "C": 0.62, "D": 0.2, "E": 0.0}.items()) / graded_total
            if graded_total else 0.0
        )
        total = sum(int(card.get("total_tasks") or 0) for card in wanted)
        languages = {str(card.get("language")) for card in wanted if card.get("language")}
        catalog = system_catalog()
        status = "running" if any(card.get("status") == "running" for card in wanted) else ("queued" if any(card.get("status") == "queued" for card in wanted) else "completed" if wanted and all(card.get("status") == "completed" for card in wanted) else "waiting")
        timing = _portfolio_timing(wanted, status)
        focus_state = focus.get("state_model") if focus else {"nodes": [], "edges": [], "metadata": {}}
        focus_parallel = focus.get("parallel_execution") if focus and isinstance(focus.get("parallel_execution"), dict) else {}
        focus_experiment = focus.get("experiment") if focus and isinstance(focus.get("experiment"), dict) else {}
        config = self._llm_config(str(focus_experiment.get("id") or "") or None)
        return {
            "schema_version": 1,
            "generated_at": time.time(),
            "experiment": {"id": view, "label": _portfolio_label(view), "output_dir": "", "registered_at": "", "status": status},
            "experiments": cards,
            "portfolio": {"view": view, "experiments": wanted, "counts": {key: sum(1 for card in cards if card.get("status") == key) for key in ["running", "completed", "queued", "failed"]}},
            "overview": {"language": next(iter(languages)) if len(languages) == 1 else "mixed", "mode": "portfolio", "status": status, "scope": "portfolio", "total_tasks": total, "completed_execution": completed, "not_completed_execution": not_completed, "grade_counts": grade_counts, "completion_rate": (completed + not_completed) / total if total else 0.0, "followup_task_count": sum(1 for task in tasks if int(task.get("round") or 1) > 1), "followup_attempts": sum(max(0, int(task.get("round") or 1) - 1) for task in tasks), "quality_averages": _task_averages(tasks, total), "overall_quality_index": round(overall_quality_index, 4), "dataset_count": len(wanted), "completed_datasets": sum(1 for card in wanted if card.get("status") == "completed"), "task_workers": focus_parallel.get("task_workers", 1), "active_task_count": focus_parallel.get("active_task_count", 0), "queued_task_count": focus_parallel.get("queued_task_count", 0), **timing},
            "parallel_execution": focus_parallel,
            "catalog": catalog,
            "phase_states": _merge_phases(snapshots, catalog.get("phases", []), focus),
            "toolchain": focus.get("toolchain", []) if focus else [],
            "agents": _merge_agents(snapshots, focus),
            "current_task": focus.get("current_task") if focus else None,
            "tasks": tasks[:1000],
            "state_model": {**focus_state, "metadata": {**(focus_state.get("metadata", {}) if isinstance(focus_state, dict) else {}), "portfolio_focus": (focus.get("experiment") or {}).get("label") if focus else None}},
            "flow_events": events,
            "failures": failures,
            "assistant": {**config.public_dict(), "backend_managed": True, "api_key_configured": bool(config.api_key)},
            "control": {"can_start": True, "process_running": any(card.get("status") == "running" for card in cards), "execution_status": status, "queue_size": sum(1 for card in cards if card.get("status") == "queued")},
        }

    def _empty_snapshot(self, experiments: list[dict[str, object]] | None = None) -> dict[str, object]:
        return {"schema_version": 1, "generated_at": time.time(), "experiments": experiments or [], "experiment": None, "overview": {"status": "waiting"}, "catalog": system_catalog(), "phase_states": [], "toolchain": [], "agents": [], "tasks": [], "state_model": {"nodes": [], "edges": [], "metadata": {}}, "flow_events": [], "control": {"can_start": True, "process_running": False}}

    def _events(self, item_id: str | None) -> None:
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()
        previous = ""
        try:
            for _ in range(1800):
                snapshot = self._snapshot(item_id)
                body = json.dumps(snapshot, ensure_ascii=False, separators=(",", ":"))
                digest_payload = dict(snapshot)
                digest_payload.pop("generated_at", None)
                digest = hashlib.sha256(json.dumps(digest_payload, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")).hexdigest()
                if digest != previous:
                    self.wfile.write(f"event: snapshot\ndata: {body}\n\n".encode("utf-8"))
                    self.wfile.flush()
                    previous = digest
                else:
                    self.wfile.write(b": keepalive\n\n")
                    self.wfile.flush()
                time.sleep(1)
        except ConnectionError:
            return

    def _chat(self, payload: dict[str, object]) -> None:
        question = str(payload.get("question", "")).strip()
        if not question:
            self._json({"error": "question is required"}, HTTPStatus.BAD_REQUEST)
            return
        snapshot = self._snapshot(str(payload.get("experiment") or "") or None)
        config = self._llm_config(str(payload.get("experiment") or "") or None)
        llm = OpenAICompatibleLLM(config)
        store = self._knowledge_store(str(payload.get("experiment") or "") or None)
        try:
            answer = TestKnowledgeAgent.answer_question(question, snapshot=snapshot, knowledge=knowledge_snapshot(store), llm=llm)
        except Exception as exc:
            self._json(
                {"error": f"测试知识智能体未完成模型+知识库联合回答：{exc.__class__.__name__}: {exc}"},
                HTTPStatus.BAD_GATEWAY,
            )
            return
        learning = None
        if answer.get("model_used"):
            learning = TestKnowledgeAgent.learn_from_conversation(
                question,
                str(answer.get("answer", "")),
                model=config.model,
                conversation_id=None,
                knowledge_store=store,
            )
        elif answer.get("response_mode") == "knowledge_autonomous":
            learning = TestKnowledgeAgent.learn_from_conversation(
                question,
                str(answer.get("answer", "")),
                model="knowledge-autonomous",
                conversation_id=None,
                knowledge_store=store,
            )
        answer["knowledge_learning"] = learning
        if answer.get("needs_learning"):
            answer["pending_learning"] = LEARNING_QUEUE.enqueue(
                question,
                chat_id=None,
                experiment_id=str((snapshot.get("experiment") or {}).get("id") or "") or None,
                knowledge_store=store,
                context_label=str((snapshot.get("current_task") or {}).get("name") or (snapshot.get("experiment") or {}).get("label") or "通用单元测试知识"),
            )
        self._json(answer)

    def _chat_message(self, chat_id: str, payload: dict[str, object]) -> None:
        chat = CHATS.get(chat_id)
        if chat is None:
            self._json({"error": "conversation not found"}, HTTPStatus.NOT_FOUND)
            return
        question = str(payload.get("question", "")).strip()
        if not question:
            self._json({"error": "question is required"}, HTTPStatus.BAD_REQUEST)
            return
        snapshot = self._resolve_conversation_context(question, chat, str(payload.get("experiment") or "") or None)
        experiment = snapshot.get("experiment") if isinstance(snapshot.get("experiment"), dict) else {}
        task = snapshot.get("current_task") if isinstance(snapshot.get("current_task"), dict) else {}
        experiment_id = str(experiment.get("id") or "") or None
        config = self._llm_config(experiment_id)
        llm = OpenAICompatibleLLM(config)
        CHATS.append(chat_id, "user", question)
        store = self._knowledge_store(experiment_id)
        try:
            answer = TestKnowledgeAgent.answer_question(
                question, snapshot=snapshot, knowledge=knowledge_snapshot(store), llm=llm,
                conversation_history=chat.get("messages", []),
            )
        except Exception as exc:
            self._json(
                {"error": f"测试知识智能体未完成模型+知识库联合回答：{exc.__class__.__name__}: {exc}"},
                HTTPStatus.BAD_GATEWAY,
            )
            return
        learning = None
        if answer.get("model_used"):
            learning = TestKnowledgeAgent.learn_from_conversation(
                question,
                str(answer.get("answer", "")),
                model=config.model,
                conversation_id=chat_id,
                knowledge_store=store,
            )
        elif answer.get("response_mode") == "knowledge_autonomous":
            learning = TestKnowledgeAgent.learn_from_conversation(
                question,
                str(answer.get("answer", "")),
                model="knowledge-autonomous",
                conversation_id=chat_id,
                knowledge_store=store,
            )
        answer["knowledge_learning"] = learning
        context_label = str(task.get("name") or experiment.get("label") or "通用单元测试知识")
        pending_learning = None
        if answer.get("needs_learning"):
            pending_learning = LEARNING_QUEUE.enqueue(
                question,
                chat_id=chat_id,
                experiment_id=experiment_id,
                knowledge_store=store,
                context_label=context_label,
            )
            answer["pending_learning"] = pending_learning
        CHATS.bind(chat_id, experiment_id, str(task.get("id") or "") or None, context_label)
        message = CHATS.append(
            chat_id,
            "assistant",
            str(answer.get("answer", "")),
            agent="测试知识智能体",
            sources=answer.get("sources", []),
            model_used=answer.get("model_used", False),
            knowledge_used=answer.get("knowledge_used", False),
            response_mode=answer.get("response_mode"),
            needs_learning=answer.get("needs_learning", False),
            pending_learning=pending_learning,
            learning=learning,
            context={"experiment_id": experiment_id, "task_id": task.get("id"), "label": context_label},
        )
        self._json({"conversation": CHATS.get(chat_id), "message": message, "answer": answer})

    def _resolve_conversation_context(self, question: str, chat: dict[str, object], explicit_id: str | None) -> dict[str, object]:
        experiments = REGISTRY.list()
        if explicit_id:
            return self._snapshot(explicit_id)
        normalized = question.casefold()
        bound = str(chat.get("bound_experiment") or "") or None
        snapshot = self._snapshot(bound) if bound else self._snapshot(None)
        best_task: tuple[int, dict[str, object]] | None = None
        for task in snapshot.get("tasks", []):
            if not isinstance(task, dict):
                continue
            terms = {str(task.get("name") or "").casefold(), Path(str(task.get("source") or "")).name.casefold()}
            score = sum(max(2, len(term) // 3) for term in terms if len(term) >= 3 and term in normalized)
            if score and (best_task is None or score > best_task[0]):
                best_task = (score, task)
        if best_task:
            snapshot = dict(snapshot)
            snapshot["current_task"] = best_task[1]
            return snapshot
        bound_task = str(chat.get("bound_task") or "")
        if bound_task:
            task = next((item for item in snapshot.get("tasks", []) if str(item.get("id")) == bound_task), None)
            if task:
                snapshot = {**snapshot, "current_task": task}
        for record in experiments:
            terms = {str(record.get("label") or "").casefold(), Path(str(record.get("output_dir") or "")).name.casefold()}
            if any(len(term) >= 3 and term in normalized for term in terms):
                return self._snapshot(str(record.get("id")))
        return snapshot

    def _llm_config(self, experiment_id: str | None) -> LLMConfig:
        resolved_id = None if experiment_id in {None, "all", "running", "completed", "queued"} else experiment_id
        registered = REGISTRY.runtime_config(resolved_id)
        record = REGISTRY.get(resolved_id)
        if not registered and resolved_id:
            visible, _masters = _expanded_experiments(REGISTRY.list())
            virtual = next((item for item in visible if str(item.get("id")) == resolved_id), None)
            parent_id = str((virtual or {}).get("parent_id") or "") or None
            if parent_id:
                registered = REGISTRY.runtime_config(parent_id)
                record = REGISTRY.get(parent_id) or virtual
        if not registered:
            root = Path(str((record or {}).get("output_dir") or ""))
            for name in ("all_datasets_summary.json", "batch_summary.json", "stateflow_summary.json"):
                artifact = _read_object(root / name)
                artifact_config = artifact.get("llm") if isinstance(artifact.get("llm"), dict) else {}
                if artifact_config:
                    registered = dict(artifact_config)
                    break
        config = LLMConfig.from_env(
            enabled=registered.get("enabled") if registered else None,
            required=False,
            provider=registered.get("provider") if registered else None,
            base_url=registered.get("base_url") if registered else None,
            model=registered.get("model") if registered else None,
            api_key=registered.get("api_key") if registered else None,
            timeout=registered.get("timeout") if registered else None,
            temperature=registered.get("temperature") if registered else None,
        )
        # The experiment-generation switch does not disable the conversational
        # Test Knowledge Agent.  Its design always requires model + retrieval.
        config.enabled = True
        config.required = True
        return config

    def _knowledge_store(self, experiment_id: str | None) -> Path:
        record = REGISTRY.get(experiment_id) if experiment_id not in {"all", "running", "completed", "queued"} else REGISTRY.get()
        if record is None and experiment_id:
            visible, _masters = _expanded_experiments(REGISTRY.list())
            virtual = next((item for item in visible if str(item.get("id")) == str(experiment_id)), None)
            parent_id = str((virtual or {}).get("parent_id") or "") or None
            record = REGISTRY.get(parent_id) if parent_id else virtual
        configured = (record or {}).get("knowledge_store")
        return Path(str(configured)).expanduser().resolve() if configured else resolve_knowledge_store_path()

    def _start_experiment(self, payload: dict[str, object]) -> None:
        mode = str(payload.get("mode") or "single")
        source_text = str(payload.get("source") or "").strip()
        output_text = str(payload.get("output") or "").strip()
        if not source_text or not output_text:
            self._json({"error": "source and output paths are required"}, HTTPStatus.BAD_REQUEST)
            return
        source = Path(source_text).expanduser().resolve()
        output = Path(output_text).expanduser().resolve()
        if mode not in {"single", "directory", "datasets"}:
            self._json({"error": "unsupported experiment mode"}, HTTPStatus.BAD_REQUEST)
            return
        if not source.exists():
            self._json({"error": f"source path does not exist: {source}"}, HTTPStatus.BAD_REQUEST)
            return
        output.mkdir(parents=True, exist_ok=True)
        knowledge_store = str(resolve_knowledge_store_path())
        command = [sys.executable, "-B"]
        if mode == "single":
            if not source.is_file() or source.suffix.lower() not in {".py", ".java"}:
                self._json({"error": "single mode requires a .py or .java source file"}, HTTPStatus.BAD_REQUEST)
                return
            command += [str(PROJECT_ROOT / "main.py"), "--source", str(source), "--out", str(output), "--knowledge-store", knowledge_store, "--no-ui"]
        elif mode == "directory":
            if not source.is_dir():
                self._json({"error": "directory mode requires a source directory"}, HTTPStatus.BAD_REQUEST)
                return
            command += [str(PROJECT_ROOT / "batch_generate_tests.py"), "--source-dir", str(source), "--out", str(output), "--execute", "--recursive", "--language", str(payload.get("language") or "auto"), "--knowledge-store", knowledge_store, "--no-ui"]
        else:
            if not source.is_dir():
                self._json({"error": "datasets mode requires a datasets root directory"}, HTTPStatus.BAD_REQUEST)
                return
            command += [str(PROJECT_ROOT / "run_all_datasets.py"), "--datasets-root", str(source), "--out-root", str(output), "--knowledge-store", knowledge_store, "--no-ui"]
        config = LLMConfig.from_env(
            enabled=bool(payload.get("llm")),
            provider=str(payload.get("llm_provider") or "") or None,
            base_url=str(payload.get("llm_base_url") or "") or None,
            model=str(payload.get("llm_model") or "") or None,
            api_key=str(payload.get("llm_api_key") or "") or None,
        )
        env = os.environ.copy()
        if config.enabled:
            command.append("--llm")
            env.update({"STATEFLOW_LLM_ENABLED": "1", "STATEFLOW_LLM_PROVIDER": config.provider, "STATEFLOW_LLM_BASE_URL": config.base_url, "STATEFLOW_LLM_MODEL": config.model, "STATEFLOW_LLM_API_KEY": config.api_key, "STATEFLOW_LLM_TIMEOUT": str(config.timeout), "STATEFLOW_LLM_TEMPERATURE": str(config.temperature)})
        label = str(payload.get("label") or source.name or output.name)
        launch_request = {"mode": mode, "source": str(source), "output": str(output), "language": str(payload.get("language") or "auto"), "label": label, "llm": bool(payload.get("llm")), "llm_model": config.model, "llm_provider": config.provider, "llm_base_url": config.base_url, "knowledge_store": knowledge_store}
        record = REGISTRY.register(
            str(output),
            label,
            {**config.public_dict(), "api_key": config.api_key},
            {"execution_status": "queued", "launch_request": launch_request, "knowledge_store": knowledge_store},
        )
        log_path = output / "experiment_process.log"
        try:
            position = JOBS.enqueue(ExperimentJob(str(record["id"]), command, env, log_path))
        except ValueError as exc:
            self._json({"error": str(exc)}, HTTPStatus.CONFLICT)
            return
        self._json({"experiment": {**record, "status": "queued"}, "process_id": None, "queue_position": position, "command": [Path(part).name if index < 2 else part for index, part in enumerate(command)], "log_path": str(log_path)}, HTTPStatus.ACCEPTED)

    def _finish_experiment(self, payload: dict[str, object]) -> None:
        output_text = str(payload.get("output_dir") or "").strip()
        if not output_text:
            self._json({"error": "output_dir is required"}, HTTPStatus.BAD_REQUEST)
            return
        item_id = experiment_id(Path(output_text).resolve())
        if REGISTRY.get(item_id) is None:
            self._json({"error": "experiment not found"}, HTTPStatus.NOT_FOUND)
            return
        success = bool(payload.get("success"))
        updated = REGISTRY.update(
            item_id,
            execution_status="completed" if success else "failed",
            finished_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            last_error=None if success else str(payload.get("error") or "experiment interrupted or failed"),
        )
        SNAPSHOT_CACHE.pop(item_id, None)
        self._json({"experiment": updated, "status": "completed" if success else "failed"})

    def _artifact(self, experiment_id: str | None, requested_path: str) -> None:
        record = REGISTRY.get(experiment_id)
        if not requested_path:
            self._json({"error": "experiment and path are required"}, HTTPStatus.BAD_REQUEST)
            return
        candidate = Path(requested_path).resolve()
        if record is None and experiment_id in {"all", "running", "completed", "queued"}:
            record = next((item for item in REGISTRY.list() if Path(str(item.get("output_dir"))).resolve() == candidate or Path(str(item.get("output_dir"))).resolve() in candidate.parents), None)
        if record is None:
            self._json({"error": "experiment not found"}, HTTPStatus.NOT_FOUND)
            return
        output_root = Path(str(record.get("output_dir"))).resolve()
        allowed = candidate == output_root or output_root in candidate.parents
        if not allowed:
            snapshot = build_snapshot(record, REGISTRY.list())
            exact_paths = set()
            for task in snapshot.get("tasks", []):
                if isinstance(task, dict):
                    exact_paths.update(str(task.get(key) or "") for key in ["source", "test_path", "summary_path", "graph_path", "failure_report"])
            allowed = str(candidate) in exact_paths
        if not allowed or not candidate.is_file():
            self._json({"error": "artifact path is outside the selected experiment"}, HTTPStatus.FORBIDDEN)
            return
        if candidate.name == "state_flow_graph.json":
            model = state_model_artifact(candidate)
            self._json({
                "path": str(candidate),
                "name": candidate.name,
                "size": candidate.stat().st_size,
                "kind": "state_model",
                "state_model": model,
            })
            return
        if candidate.stat().st_size > 2_000_000:
            try:
                with candidate.open("r", encoding="utf-8", errors="replace") as handle:
                    content = handle.read(200_000)
            except OSError as exc:
                self._json({"error": str(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR)
                return
            self._json({"path": str(candidate), "name": candidate.name, "size": candidate.stat().st_size, "content": content, "truncated": True})
            return
        try:
            content = candidate.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            self._json({"error": str(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR)
            return
        payload = {"path": str(candidate), "name": candidate.name, "size": candidate.stat().st_size}
        if candidate.suffix.lower() == ".json":
            try:
                payload.update({"kind": "data", "data": json.loads(content)})
            except json.JSONDecodeError:
                payload.update({"content": content})
        elif candidate.suffix.lower() in {".html", ".htm"}:
            payload.update({"kind": "html", "content": content})
        else:
            payload.update({"content": content})
        self._json(payload)

    def _raw_artifact(self, experiment_id: str | None, requested_path: str) -> None:
        if not requested_path:
            self._json({"error": "experiment and path are required"}, HTTPStatus.BAD_REQUEST)
            return
        candidate = Path(requested_path).resolve()
        record = REGISTRY.get(experiment_id)
        if record is None and experiment_id in {"all", "running", "completed", "queued"}:
            record = next((item for item in REGISTRY.list() if Path(str(item.get("output_dir"))).resolve() == candidate or Path(str(item.get("output_dir"))).resolve() in candidate.parents), None)
        if record is None:
            self._json({"error": "experiment not found"}, HTTPStatus.NOT_FOUND)
            return
        output_root = Path(str(record.get("output_dir"))).resolve()
        if output_root not in candidate.parents or not candidate.is_file() or candidate.suffix.lower() not in {".html", ".htm"}:
            self._json({"error": "HTML report is outside the selected experiment"}, HTTPStatus.FORBIDDEN)
            return
        content = candidate.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Content-Disposition", f'inline; filename="{candidate.name}"')
        self.send_header("Content-Security-Policy", "sandbox allow-scripts; default-src 'self' data:; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src 'self' data:")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(content)

    def _static(self, url_path: str) -> None:
        relative = url_path.lstrip("/") or "index.html"
        candidate = (FRONTEND_DIST / relative).resolve()
        if FRONTEND_DIST.resolve() not in candidate.parents and candidate != FRONTEND_DIST.resolve():
            self.send_error(HTTPStatus.FORBIDDEN)
            return
        if not candidate.is_file():
            candidate = FRONTEND_DIST / "index.html"
        if not candidate.is_file():
            self._json({"error": "Frontend is not built. Run npm install and npm run build in frontend/."}, HTTPStatus.SERVICE_UNAVAILABLE)
            return
        content = candidate.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", mimetypes.guess_type(candidate.name)[0] or "application/octet-stream")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-cache" if candidate.name == "index.html" else "public, max-age=3600")
        self.end_headers()
        self.wfile.write(content)

    def _body(self) -> dict[str, object]:
        try:
            length = min(int(self.headers.get("Content-Length", "0")), 1_000_000)
            data = json.loads(self.rfile.read(length).decode("utf-8"))
            return data if isinstance(data, dict) else {}
        except (ValueError, json.JSONDecodeError, UnicodeDecodeError):
            return {}

    def _json(self, payload: object, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        if os.environ.get("TSG_UI_LOG_REQUESTS") == "1":
            super().log_message(format, *args)


def _request_language(record: dict[str, object]) -> str:
    request = record.get("launch_request") if isinstance(record.get("launch_request"), dict) else {}
    language = str(request.get("language") or "")
    source = str(request.get("source") or "").lower()
    if language not in {"", "auto", "all"}:
        return language
    if source.endswith(".java"):
        return "java"
    if source.endswith(".py"):
        return "python"
    return "mixed" if language == "all" else "auto"


def _request_scope(record: dict[str, object]) -> str:
    request = record.get("launch_request") if isinstance(record.get("launch_request"), dict) else {}
    return {"single": "file", "directory": "project", "datasets": "datasets"}.get(str(request.get("mode") or ""), "project")


def _portfolio_label(view: str) -> str:
    return {"all": "全部实验", "running": "正在运行", "completed": "已完成实验", "queued": "排队中实验"}.get(view, "全部实验")


def _portfolio_timing(cards: list[dict[str, object]], status: str) -> dict[str, object]:
    starts = [_parse_timestamp(card.get("started_at")) for card in cards]
    starts = [value for value in starts if value is not None]
    finishes = [_parse_timestamp(card.get("finished_at")) for card in cards]
    finishes = [value for value in finishes if value is not None]
    started = min(starts) if starts else None
    all_terminal = bool(cards) and all(card.get("status") in {"completed", "failed"} for card in cards)
    finished = max(finishes) if all_terminal and len(finishes) == len(cards) else None
    end = finished or (datetime.now(timezone.utc) if started and status == "running" else None)
    return {
        "started_at": started.isoformat() if started else None,
        "finished_at": finished.isoformat() if finished else None,
        "duration_seconds": round(max(0.0, (end - started).total_seconds()), 3) if started and end else None,
    }


def _parse_timestamp(value: object) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed
    except (TypeError, ValueError):
        return None


def _task_averages(tasks: list[dict[str, object]], selected_tasks: int | None = None) -> dict[str, object]:
    from .dashboard_data import _task_quality_averages
    return _task_quality_averages(tasks, selected_tasks)


def _merge_phases(snapshots: list[dict[str, object]], definitions: list[dict[str, object]], focus: dict[str, object] | None) -> list[dict[str, object]]:
    result = []
    for definition in definitions:
        states = [phase for snapshot in snapshots for phase in snapshot.get("phase_states", []) if isinstance(phase, dict) and phase.get("id") == definition.get("id")]
        focus_states = [phase for phase in (focus or {}).get("phase_states", []) if isinstance(phase, dict) and phase.get("id") == definition.get("id")]
        statuses = {str(state.get("status")) for state in states}
        status = "active" if statuses & {"active", "running"} else "done" if statuses & {"done", "completed"} else "pending"
        last = next((state.get("last_event") for state in focus_states if state.get("last_event")), next((state.get("last_event") for state in states if state.get("last_event")), None))
        result.append({**definition, "status": status, "event_count": sum(int(state.get("event_count") or 0) for state in states), "last_event": last})
    return result


def _merge_agents(snapshots: list[dict[str, object]], focus: dict[str, object] | None) -> list[dict[str, object]]:
    names = ["测试状态智能体", "测试生成智能体", "测试知识智能体"]
    result = []
    for name in names:
        agents = [agent for snapshot in snapshots for agent in snapshot.get("agents", []) if isinstance(agent, dict) and agent.get("name") == name]
        focus_agents = [agent for agent in (focus or {}).get("agents", []) if isinstance(agent, dict) and agent.get("name") == name]
        latest = next((agent for agent in focus_agents if agent.get("last_event")), next((agent for agent in agents if agent.get("last_event")), agents[0] if agents else {}))
        module_names = []
        for agent in agents:
            for task in agent.get("internal_tasks", []) or []:
                if isinstance(task, dict) and task.get("name") not in module_names:
                    module_names.append(task.get("name"))
        internal = []
        for module_name in module_names:
            tasks = [task for agent in agents for task in agent.get("internal_tasks", []) or [] if isinstance(task, dict) and task.get("name") == module_name]
            latest_tasks = [task for task in latest.get("internal_tasks", []) or [] if isinstance(task, dict) and task.get("name") == module_name]
            statuses = {str(task.get("status")) for task in tasks}
            last_event = next((task.get("last_event") for task in latest_tasks if task.get("last_event")), next((task.get("last_event") for task in tasks if task.get("last_event")), None))
            internal.append({"name": module_name, "status": "active" if "active" in statuses else "done" if statuses & {"done", "completed"} else "pending", "event_count": sum(int(task.get("event_count") or 0) for task in tasks), "last_event": last_event})
        statuses = {str(agent.get("status")) for agent in agents}
        result.append({"id": str(latest.get("id") or name), "name": name, "status": "active" if statuses & {"active", "running"} else "done" if agents else "standby", "modules": module_names, "internal_tasks": internal, "current_action": latest.get("current_action"), "interaction_role": latest.get("interaction_role"), "last_event": latest.get("last_event"), "event_count": sum(int(agent.get("event_count") or 0) for agent in agents)})
    return result


def _restore_queued_jobs() -> None:
    for record in REGISTRY.list():
        if record.get("execution_status") != "queued":
            continue
        request = record.get("launch_request") if isinstance(record.get("launch_request"), dict) else {}
        try:
            source = Path(str(request.get("source") or "")).resolve()
            output = Path(str(request.get("output") or record.get("output_dir") or "")).resolve()
            mode = str(request.get("mode") or "single")
            if not source.exists() or mode not in {"single", "directory", "datasets"}:
                raise OSError("queued experiment source is unavailable")
            command = [sys.executable, "-B"]
            knowledge_store = str(request.get("knowledge_store") or resolve_knowledge_store_path())
            if mode == "single":
                command += [str(PROJECT_ROOT / "main.py"), "--source", str(source), "--out", str(output), "--knowledge-store", knowledge_store, "--no-ui"]
            elif mode == "directory":
                command += [str(PROJECT_ROOT / "batch_generate_tests.py"), "--source-dir", str(source), "--out", str(output), "--execute", "--recursive", "--language", str(request.get("language") or "auto"), "--knowledge-store", knowledge_store, "--no-ui"]
            else:
                command += [str(PROJECT_ROOT / "run_all_datasets.py"), "--datasets-root", str(source), "--out-root", str(output), "--knowledge-store", knowledge_store, "--no-ui"]
            config = LLMConfig.from_env(
                enabled=bool(request.get("llm")),
                provider=str(request.get("llm_provider") or "") or None,
                base_url=str(request.get("llm_base_url") or "") or None,
                model=str(request.get("llm_model") or "") or None,
            )
            env = os.environ.copy()
            if config.enabled:
                command.append("--llm")
                env.update({"STATEFLOW_LLM_ENABLED": "1", "STATEFLOW_LLM_PROVIDER": config.provider, "STATEFLOW_LLM_BASE_URL": config.base_url, "STATEFLOW_LLM_MODEL": config.model, "STATEFLOW_LLM_API_KEY": config.api_key, "STATEFLOW_LLM_TIMEOUT": str(config.timeout), "STATEFLOW_LLM_TEMPERATURE": str(config.temperature)})
            JOBS.enqueue(ExperimentJob(str(record["id"]), command, env, output / "experiment_process.log"))
        except (OSError, ValueError) as exc:
            REGISTRY.update(str(record.get("id")), execution_status="failed", last_error=str(exc), finished_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Serve the interactive TSG experiment dashboard.")
    parser.add_argument("--host", default=os.environ.get("TSG_UI_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("TSG_UI_PORT", "8765")))
    return parser.parse_args()


def _process_pending_learning_once() -> int:
    completed = 0
    handler = object.__new__(DashboardHandler)
    for item in LEARNING_QUEUE.due(limit=5):
        item_id = str(item.get("id") or "")
        try:
            experiment_id = str(item.get("experiment_id") or "") or None
            config = handler._llm_config(experiment_id)
            snapshot = handler._snapshot(experiment_id)
            store = Path(str(item.get("knowledge_store") or resolve_knowledge_store_path())).expanduser().resolve()
            answer = TestKnowledgeAgent.answer_question(
                str(item.get("question") or ""),
                snapshot=snapshot,
                knowledge=knowledge_snapshot(store),
                llm=OpenAICompatibleLLM(config),
            )
            if not answer.get("model_used"):
                raise RuntimeError(str(answer.get("model_error") or "模型仍不可用"))
            learning = TestKnowledgeAgent.learn_from_conversation(
                str(item.get("question") or ""),
                str(answer.get("answer") or ""),
                model=config.model,
                conversation_id=str(item.get("chat_id") or "") or None,
                knowledge_store=store,
                force=True,
            )
            completed_item = LEARNING_QUEUE.complete(
                item_id,
                answer=str(answer.get("answer") or ""),
                record_id=str((learning or {}).get("record_id") or "") or None,
            )
            chat_id = str(item.get("chat_id") or "")
            if chat_id and completed_item:
                CHATS.append(
                    chat_id,
                    "assistant",
                    "我已在模型恢复后完成自动补学：\n" + str(answer.get("answer") or ""),
                    agent="测试知识智能体",
                    sources=answer.get("sources", []),
                    model_used=True,
                    knowledge_used=True,
                    response_mode="autonomous_learning_completed",
                    needs_learning=False,
                    learning=learning,
                    context={"experiment_id": experiment_id, "task_id": None, "label": item.get("context_label")},
                )
            completed += 1
        except Exception as exc:
            LEARNING_QUEUE.retry_later(item_id, f"{exc.__class__.__name__}: {exc}")
    return completed


def _knowledge_learning_loop() -> None:
    while True:
        try:
            _process_pending_learning_once()
        except Exception:
            logging.exception("测试知识智能体后台补学失败，将在下一周期继续")
        time.sleep(15)


def main() -> None:
    args = parse_args()
    _restore_queued_jobs()
    Thread(target=_knowledge_learning_loop, name="test-knowledge-auto-learning", daemon=True).start()
    ThreadingHTTPServer((args.host, args.port), DashboardHandler).serve_forever()


if __name__ == "__main__":
    main()
