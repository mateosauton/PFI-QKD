import json
import threading
import urllib.request

from study_app.server import create_server


def request(base_url, method, path, payload=None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        base_url + path,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"} if data else {},
    )
    with urllib.request.urlopen(request) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


def test_guided_session_end_to_end(tmp_path):
    server = create_server("127.0.0.1", 0, tmp_path)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_port}"
    try:
        status, session = request(base_url, "GET", "/api/session")
        assert status == 200
        assert session["module"]["id"] == "crypto-keys"

        status, _ = request(base_url, "POST", "/api/draft", {"module_id": "crypto-keys", "body": "borrador"})
        assert status == 200
        status, attempt = request(
            base_url,
            "POST",
            "/api/attempts",
            {"module_id": "crypto-keys", "prompt_id": "crypto-keys-01", "body": "respuesta", "help_level": "none"},
        )
        assert status == 201

        feedback = {
            "attempt_id": attempt["attempt_id"],
            "criteria": {
                capability: {"status": "yellow", "note": "conectar con la tesis"}
                for capability in ("explain", "calculate", "connect", "defend")
            },
            "strengths": ["respuesta directa"],
            "errors": ["falta un ejemplo"],
            "next_action": "review",
            "hint": {"level": 1, "text": "agregá un ejemplo concreto"},
        }
        status, _ = request(base_url, "POST", "/api/feedback", feedback)
        assert status == 201
        request(base_url, "POST", "/api/progress/status", {"module_id": "crypto-keys", "status": "in_progress"})
        request(base_url, "POST", "/api/progress/status", {"module_id": "crypto-keys", "status": "submitted"})
        status, progress = request(base_url, "POST", "/api/progress/status", {"module_id": "crypto-keys", "status": "review"})
        assert status == 200
        assert progress["modules"]["crypto-keys"]["status"] == "review"

        status, history = request(base_url, "GET", "/api/history?module_id=crypto-keys")
        assert status == 200
        assert len(history["attempts"]) == 1
        status, exported = request(base_url, "POST", "/api/export", {})
        assert status == 200
        assert "Resumen de progreso QKD" in exported["summary"]
        assert (tmp_path / "exports/progress-summary.md").exists()
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()
