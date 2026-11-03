def test_status_endpoint_ollama_down(client, monkeypatch):
    monkeypatch.setattr("app.routes.check_status", lambda: {
        "running": False, "model": "llama3.2:3b", "model_installed": False,
        "message": "Ollama is not running."})
    resp = client.get("/status")
    assert resp.status_code == 200
    assert resp.get_json()["running"] is False


def test_status_endpoint_ready(client, monkeypatch):
    monkeypatch.setattr("app.routes.check_status", lambda: {
        "running": True, "model": "llama3.2:3b", "model_installed": True,
        "message": "Ollama is ready."})
    assert client.get("/status").get_json()["model_installed"] is True