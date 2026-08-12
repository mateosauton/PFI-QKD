"""Local HTTP server for the guided QKD study application."""

from __future__ import annotations

import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from .catalog import MODULES, get_module
from .state import StateStore


MAX_BODY_BYTES = 1024 * 1024
STATIC_ROOT = Path(__file__).resolve().parent / "static"
PROJECT_ROOT = Path(__file__).resolve().parents[1]


class StudyRequestHandler(BaseHTTPRequestHandler):
    server: "StudyHTTPServer"

    def log_message(self, format: str, *args: object) -> None:
        return

    def _json(self, status: int, value: Any) -> None:
        body = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _error(self, status: int, message: str) -> None:
        self._json(status, {"error": message})

    def _read_json(self) -> dict[str, Any] | None:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._error(400, "invalid content length")
            return None
        if length > MAX_BODY_BYTES:
            self._error(413, "request body too large")
            return None
        try:
            value = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._error(400, "invalid json")
            return None
        if not isinstance(value, dict):
            self._error(400, "json object required")
            return None
        return value

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/"):
            self._handle_api_get(parsed.path, parse_qs(parsed.query))
            return
        self._serve_static(parsed.path)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if not parsed.path.startswith("/api/"):
            self._error(404, "not found")
            return
        payload = self._read_json()
        if payload is None:
            return
        self._handle_api_post(parsed.path, payload)

    def _handle_api_get(self, path: str, query: dict[str, list[str]]) -> None:
        if path == "/api/catalog":
            self._json(200, {"modules": [module.to_dict() for module in MODULES]})
            return
        if path == "/api/progress":
            self._json(200, self.server.state_store.load_progress())
            return
        if path == "/api/session":
            progress = self.server.state_store.load_progress()
            module = get_module(progress["current_module"])
            self._json(
                200,
                {
                    "progress": progress,
                    "module": module.to_dict() if module else None,
                    "draft": self.server.state_store.load_draft(),
                },
            )
            return
        if path.startswith("/api/attempts/"):
            attempt_id = path.rsplit("/", 1)[-1]
            attempt = self.server.state_store.get_attempt(attempt_id)
            if attempt is None:
                self._error(404, "attempt not found")
                return
            self._json(200, attempt)
            return
        if path == "/api/history":
            module_id = query.get("module_id", [None])[0]
            self._json(200, {"attempts": self.server.state_store.list_attempts(module_id)})
            return
        if path == "/api/errors":
            self._json(200, self.server.state_store.load_errors())
            return
        self._error(404, "not found")

    def _handle_api_post(self, path: str, payload: dict[str, Any]) -> None:
        try:
            if path == "/api/draft":
                if not payload.get("module_id"):
                    raise RequestError(422, "module_id is required")
                self._json(200, self.server.state_store.save_draft(payload))
                return
            if path == "/api/attempts":
                required = ("module_id", "prompt_id", "body", "help_level")
                missing = [field for field in required if not payload.get(field)]
                if missing:
                    raise RequestError(422, f"missing required fields: {', '.join(missing)}")
                attempt = self.server.state_store.submit_attempt(
                    payload["module_id"],
                    payload["prompt_id"],
                    payload["body"],
                    payload["help_level"],
                    payload.get("self_assessment"),
                )
                self._json(201, attempt)
                return
            if path == "/api/feedback":
                feedback = self.server.state_store.save_feedback(payload)
                self._json(201, feedback)
                return
            if path == "/api/progress/status":
                if not payload.get("module_id") or not payload.get("status"):
                    raise RequestError(422, "module_id and status are required")
                self._json(200, self.server.state_store.set_module_status(payload["module_id"], payload["status"]))
                return
            if path == "/api/errors":
                required = ("module_id", "concept", "status")
                missing = [field for field in required if not payload.get(field)]
                if missing:
                    raise RequestError(422, f"missing required fields: {', '.join(missing)}")
                self._json(200, self.server.state_store.record_error(payload["module_id"], payload["concept"], payload["status"]))
                return
            if path == "/api/export":
                summary = self.server.state_store.export_summary()
                self._json(200, {"summary": summary, "path": "exports/progress-summary.md"})
                return
            self._error(404, "not found")
        except RequestError as error:
            self._error(error.status, str(error))
        except FileExistsError:
            self._error(409, "immutable record already exists")
        except ValueError as error:
            self._error(422, str(error))

    def _serve_static(self, path: str) -> None:
        if path.startswith("/study/"):
            root = PROJECT_ROOT
            relative = path.removeprefix("/")
        else:
            root = STATIC_ROOT
            relative = "index.html" if path in ("", "/") else path.removeprefix("/")
        candidate = (root / relative).resolve()
        if root not in candidate.parents and candidate != root:
            self._error(404, "not found")
            return
        if not candidate.is_file():
            self._error(404, "not found")
            return
        body = candidate.read_bytes()
        content_type = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8" if content_type.startswith("text/") else content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class RequestError(ValueError):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status


class StudyHTTPServer(ThreadingHTTPServer):
    def __init__(self, address: tuple[str, int], state_root: Path):
        super().__init__(address, StudyRequestHandler)
        self.state_store = StateStore(state_root)


def create_server(host: str, port: int, state_root: Path) -> StudyHTTPServer:
    return StudyHTTPServer((host, port), Path(state_root))
