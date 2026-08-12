"""Private, file-backed state for the guided QKD study application."""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .catalog import MODULES, get_module


SCHEMA_VERSION = 1
STATUSES = {"locked", "available", "in_progress", "submitted", "recovery", "review", "mastered"}
ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "locked": {"available"},
    "available": {"in_progress"},
    "in_progress": {"submitted"},
    "submitted": {"recovery", "review"},
    "recovery": {"in_progress", "review"},
    "review": {"mastered", "recovery"},
    "mastered": {"review"},
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


class StateStore:
    """Read and write local study state without overwriting submitted work."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.attempts_dir = self.root / "attempts"
        self.feedback_dir = self.root / "feedback"
        self.exports_dir = self.root / "exports"
        for directory in (self.root, self.attempts_dir, self.feedback_dir, self.exports_dir):
            directory.mkdir(parents=True, exist_ok=True)
        if not (self.root / "progress.json").exists():
            self._write_json(self.root / "progress.json", self._default_progress())
        if not (self.root / "errors.json").exists():
            self._write_json(self.root / "errors.json", {"schema_version": SCHEMA_VERSION, "items": []})
        if not (self.root / "defense.json").exists():
            self._write_json(self.root / "defense.json", {"schema_version": SCHEMA_VERSION, "items": []})

    @staticmethod
    def _default_progress() -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "current_module": "crypto-keys",
            "updated_at": _now(),
            "modules": {
                module.id: {
                    "status": "available" if module.order == 1 else "locked",
                    "explain": "red",
                    "calculate": "red",
                    "connect": "red",
                    "defend": "red",
                    "next_review_at": None,
                }
                for module in MODULES
            },
        }

    @staticmethod
    def _read_json(path: Path, default: Any = None) -> Any:
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def _write_json(path: Path, value: Any, overwrite: bool = True) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        if not overwrite and path.exists():
            raise FileExistsError(path)
        temp_path = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
        try:
            with temp_path.open("w", encoding="utf-8") as handle:
                json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            if not overwrite and path.exists():
                raise FileExistsError(path)
            os.replace(temp_path, path)
        finally:
            temp_path.unlink(missing_ok=True)

    def load_progress(self) -> dict[str, Any]:
        return self._read_json(self.root / "progress.json", self._default_progress())

    def save_draft(self, draft: dict[str, Any]) -> dict[str, Any]:
        value = {"schema_version": SCHEMA_VERSION, "updated_at": _now(), **draft}
        self._write_json(self.root / "session.json", value)
        return value

    def load_draft(self) -> dict[str, Any] | None:
        return self._read_json(self.root / "session.json")

    def create_attempt_file(self, attempt_id: str, attempt: dict[str, Any]) -> dict[str, Any]:
        path = self.attempts_dir / f"{attempt_id}.json"
        if path.exists():
            raise FileExistsError(path)
        self._write_json(path, attempt, overwrite=False)
        return attempt

    def submit_attempt(
        self,
        module_id: str,
        prompt_id: str,
        body: str,
        help_level: str,
        self_assessment: str | None = None,
    ) -> dict[str, Any]:
        if get_module(module_id) is None:
            raise ValueError(f"unknown module: {module_id}")
        if not body.strip():
            raise ValueError("body is required")
        attempt_id = f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"
        attempt = {
            "schema_version": SCHEMA_VERSION,
            "attempt_id": attempt_id,
            "module_id": module_id,
            "prompt_id": prompt_id,
            "body": body,
            "help_level": help_level,
            "self_assessment": self_assessment,
            "submitted_at": _now(),
            "source": "guided-web",
        }
        return self.create_attempt_file(attempt_id, attempt)

    def get_attempt(self, attempt_id: str) -> dict[str, Any] | None:
        return self._read_json(self.attempts_dir / f"{attempt_id}.json")

    def list_attempts(self, module_id: str | None = None) -> list[dict[str, Any]]:
        attempts = [self._read_json(path) for path in sorted(self.attempts_dir.glob("*.json"))]
        values = [item for item in attempts if item is not None]
        if module_id is not None:
            values = [item for item in values if item.get("module_id") == module_id]
        return sorted(values, key=lambda item: item.get("submitted_at", ""))

    def save_feedback(self, feedback: dict[str, Any]) -> dict[str, Any]:
        attempt_id = feedback.get("attempt_id")
        if not attempt_id or self.get_attempt(attempt_id) is None:
            raise ValueError("attempt_id must reference an existing attempt")
        value = {"schema_version": SCHEMA_VERSION, "reviewed_at": _now(), **feedback}
        self._write_json(self.feedback_dir / f"{attempt_id}.json", value)
        return value

    def get_feedback(self, attempt_id: str) -> dict[str, Any] | None:
        return self._read_json(self.feedback_dir / f"{attempt_id}.json")

    def set_module_status(self, module_id: str, status: str) -> dict[str, Any]:
        if get_module(module_id) is None:
            raise ValueError(f"unknown module: {module_id}")
        if status not in STATUSES:
            raise ValueError(f"unknown module status: {status}")
        progress = self.load_progress()
        current = progress["modules"][module_id]["status"]
        if status != current and status not in ALLOWED_TRANSITIONS[current]:
            raise ValueError(f"invalid module transition: {current} -> {status}")
        progress["modules"][module_id]["status"] = status
        progress["updated_at"] = _now()
        if status == "available" and progress.get("current_module") == "crypto-keys":
            ordered = sorted(MODULES, key=lambda module: module.order)
            current_order = get_module(progress["current_module"]).order if get_module(progress["current_module"]) else 0
            if get_module(module_id).order > current_order:
                progress["current_module"] = module_id
        self._write_json(self.root / "progress.json", progress)
        return progress

    def load_errors(self) -> dict[str, Any]:
        return self._read_json(self.root / "errors.json", {"schema_version": SCHEMA_VERSION, "items": []})

    def record_error(self, module_id: str, concept: str, status: str) -> dict[str, Any]:
        errors = self.load_errors()
        now = _now()
        existing = next(
            (item for item in errors["items"] if item["module_id"] == module_id and item["concept"] == concept),
            None,
        )
        if existing is None:
            errors["items"].append(
                {
                    "module_id": module_id,
                    "concept": concept,
                    "status": status,
                    "count": 1,
                    "first_seen": now,
                    "last_seen": now,
                }
            )
        else:
            existing["status"] = status
            existing["count"] += 1
            existing["last_seen"] = now
        errors["updated_at"] = now
        self._write_json(self.root / "errors.json", errors)
        return errors

    def load_defense(self) -> dict[str, Any]:
        return self._read_json(self.root / "defense.json", {"schema_version": SCHEMA_VERSION, "items": []})

    def save_defense_record(self, record: dict[str, Any]) -> dict[str, Any]:
        if not record.get("kind") or record["kind"] not in ("presentation", "questions", "full_rehearsal"):
            raise ValueError("kind must be presentation, questions or full_rehearsal")
        defense = self.load_defense()
        value = {"schema_version": SCHEMA_VERSION, "recorded_at": _now(), **record}
        defense["items"].append(value)
        defense["updated_at"] = value["recorded_at"]
        self._write_json(self.root / "defense.json", defense)
        return value

    def create_backup(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "progress": self.load_progress(),
            "draft": self.load_draft(),
            "errors": self.load_errors(),
            "defense": self.load_defense(),
            "attempts": self.list_attempts(),
            "feedback": [self._read_json(path) for path in sorted(self.feedback_dir.glob("*.json"))],
        }

    def import_draft(self, backup: dict[str, Any]) -> dict[str, Any]:
        if backup.get("schema_version") != SCHEMA_VERSION:
            raise ValueError("unsupported backup schema")
        draft = backup.get("draft")
        if not isinstance(draft, dict) or not draft.get("module_id"):
            raise ValueError("backup does not contain a valid draft")
        return self.save_draft({key: value for key, value in draft.items() if key not in ("schema_version", "updated_at")})

    def export_summary(self) -> str:
        progress = self.load_progress()
        errors = self.load_errors()["items"]
        attempts = self.list_attempts()
        lines = [
            "# Resumen de progreso QKD",
            "",
            f"Módulo activo: `{progress['current_module']}`",
            f"Actualizado: {progress.get('updated_at', 'sin fecha')}",
            f"Intentos registrados: {len(attempts)}",
            "",
            "## Módulos",
            "",
            "| Módulo | Estado | Próxima revisión |",
            "|---|---|---|",
        ]
        for module in MODULES:
            item = progress["modules"][module.id]
            lines.append(f"| `{module.id}` | {item['status']} | {item.get('next_review_at') or 'por definir'} |")
        lines.extend(["", "## Errores registrados", ""])
        if errors:
            lines.extend(f"- `{item['module_id']}`: {item['concept']} ({item['count']} veces, {item['status']})" for item in errors)
        else:
            lines.append("- Sin errores registrados.")
        lines.extend(["", "## Defensa", "", "- Exposición: 30 minutos.", "- Preguntas: 15 minutos.", ""])
        export = "\n".join(lines)
        path = self.exports_dir / "progress-summary.md"
        path.write_text(export, encoding="utf-8")
        return export
