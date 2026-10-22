import app as appmod


def test_health():
    client = appmod.app.test_client()
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"


def test_index_lists_tasks(monkeypatch):
    monkeypatch.setattr(appmod, "list_tasks", lambda: [(1, "write jenkinsfile")])
    client = appmod.app.test_client()
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"write jenkinsfile" in resp.data
