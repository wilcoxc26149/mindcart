"""Unit tests for the mindcart CLI dispatch."""

from cli.mindcart import main


def test_cli_ingest_dispatches(monkeypatch):
    captured: dict = {}
    monkeypatch.setattr("cli.mindcart.ingest", lambda path: captured.setdefault("path", path))
    assert main(["ingest", "/tmp/repo"]) == 0
    assert captured["path"] == "/tmp/repo"


def test_cli_ingest_defaults_to_dot(monkeypatch):
    captured: dict = {}
    monkeypatch.setattr("cli.mindcart.ingest", lambda path: captured.setdefault("path", path))
    assert main(["ingest"]) == 0
    assert captured["path"] == "."


def test_cli_ask_prints_answer(monkeypatch, capsys):
    monkeypatch.setattr("cli.mindcart.load_config", lambda: {"tenant_id": "admin"})
    monkeypatch.setattr("cli.mindcart.ask", lambda q, tenant_id: f"answer:{q}:{tenant_id}")
    assert main(["ask", "How does ingest work?"]) == 0
    assert "answer:How does ingest work?:admin" in capsys.readouterr().out


def test_cli_remember_dispatches(monkeypatch):
    captured: dict = {}

    def fake_remember(text, tenant_id):
        captured["text"] = text
        captured["tenant_id"] = tenant_id

    monkeypatch.setattr("cli.mindcart.load_config", lambda: {"tenant_id": "admin"})
    monkeypatch.setattr("cli.mindcart.remember", fake_remember)
    assert main(["remember", "note"]) == 0
    assert captured == {"text": "note", "tenant_id": "admin"}


def test_cli_update_dispatches(monkeypatch):
    captured: dict = {}
    monkeypatch.setattr("cli.mindcart.update", lambda path: captured.setdefault("path", path))
    assert main(["update", "/tmp/repo"]) == 0
    assert captured["path"] == "/tmp/repo"


def test_cli_update_defaults_to_dot(monkeypatch):
    captured: dict = {}
    monkeypatch.setattr("cli.mindcart.update", lambda path: captured.setdefault("path", path))
    assert main(["update"]) == 0
    assert captured["path"] == "."


def test_cli_runtime_error_exits_one(monkeypatch, capsys):
    monkeypatch.setattr(
        "cli.mindcart.ingest",
        lambda path: (_ for _ in ()).throw(RuntimeError("No files matched")),
    )
    assert main(["ingest", "."]) == 1
    assert "No files matched" in capsys.readouterr().err
