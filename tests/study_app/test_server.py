import json
import threading
import urllib.error
import urllib.request

import pytest

from study_app.server import create_server


class Response:
    def __init__(self, status: int, body: bytes):
        self.status = status
        self.body = body

    def json(self):
        return json.loads(self.body.decode("utf-8"))


class Client:
    def __init__(self, base_url: str):
        self.base_url = base_url

    def request(self, method: str, path: str, payload=None) -> Response:
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self.base_url + path,
            data=data,
            method=method,
            headers={"Content-Type": "application/json"} if data else {},
        )
        try:
            with urllib.request.urlopen(request) as response:
                return Response(response.status, response.read())
        except urllib.error.HTTPError as error:
            return Response(error.code, error.read())

    def get(self, path: str) -> Response:
        return self.request("GET", path)

    def post(self, path: str, payload: dict) -> Response:
        return self.request("POST", path, payload)


@pytest.fixture()
def client(tmp_path):
    server = create_server("127.0.0.1", 0, tmp_path)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield Client(f"http://127.0.0.1:{server.server_port}")
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()


def test_catalog_endpoint_returns_modules(client):
    response = client.get("/api/catalog")
    assert response.status == 200
    assert len(response.json()["modules"]) == 8


def test_submit_endpoint_persists_attempt(client):
    response = client.post(
        "/api/attempts",
        {
            "module_id": "bb84-bases",
            "prompt_id": "bb84-eve-qber-01",
            "body": "Eve introduce errores al medir en una base incorrecta.",
            "help_level": "none",
        },
    )
    assert response.status == 201
    attempt_id = response.json()["attempt_id"]
    assert client.get(f"/api/attempts/{attempt_id}").json()["body"].startswith("Eve")


def test_unknown_api_route_is_json_404(client):
    response = client.get("/api/not-a-route")
    assert response.status == 404
    assert response.json()["error"] == "not found"


def test_malformed_json_is_json_400(client):
    request = urllib.request.Request(
        client.base_url + "/api/draft",
        data=b"{broken",
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with pytest.raises(urllib.error.HTTPError) as error:
        urllib.request.urlopen(request)
    assert error.value.code == 400
    assert json.loads(error.value.read()) == {"error": "invalid json"}
