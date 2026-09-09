"""Unit tests for the mindcart CLI dispatch."""

import pytest

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

    def fake_remember(text, tenant_id, file=None):
        captured["text"] = text
        captured["tenant_id"] = tenant_id
        captured["file"] = file

    monkeypatch.setattr("cli.mindcart.load_config", lambda: {"tenant_id": "admin"})
    monkeypatch.setattr("cli.mindcart.remember", fake_remember)
    assert main(["remember", "note"]) == 0
    assert captured == {"text": "note", "tenant_id": "admin", "file": None}


def test_cli_remember_file_dispatches(monkeypatch):
    captured: dict = {}

    def fake_remember(text, tenant_id, file=None):
        captured["text"] = text
        captured["tenant_id"] = tenant_id
        captured["file"] = file

    monkeypatch.setattr("cli.mindcart.load_config", lambda: {"tenant_id": "admin"})
    monkeypatch.setattr("cli.mindcart.remember", fake_remember)
    assert main(["remember", "--file", "docs/note.md"]) == 0
    assert captured == {"text": None, "tenant_id": "admin", "file": "docs/note.md"}


def test_cli_improve_dispatches(monkeypatch):
    captured: dict = {}
    monkeypatch.setattr("cli.mindcart.load_config", lambda: {"tenant_id": "admin"})
    monkeypatch.setattr("cli.mindcart.improve", lambda tenant_id: captured.setdefault("tenant_id", tenant_id))
    assert main(["improve"]) == 0
    assert captured["tenant_id"] == "admin"


def test_cli_install_dispatches(monkeypatch):
    captured: dict = {}
    monkeypatch.setattr("cli.mindcart.install", lambda target=None: captured.setdefault("target", target))
    assert main(["install", "--target", "/tmp/host"]) == 0
    assert captured["target"] == "/tmp/host"


def test_cli_remember_rejects_text_and_file(tmp_path, capsys):
    note = tmp_path / "note.md"
    note.write_text("hi\n", encoding="utf-8")
    assert main(["remember", "hello", "--file", str(note)]) == 1
    assert "not both" in capsys.readouterr().err


def test_cli_remember_requires_text_or_file(capsys):
    assert main(["remember"]) == 1
    assert "text or --file" in capsys.readouterr().err


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
    err = capsys.readouterr().err
    assert err.startswith("mindcart: ")
    assert "No files matched" in err


def test_cli_keyboard_interrupt_exits_130(monkeypatch):
    monkeypatch.setattr(
        "cli.mindcart.ingest",
        lambda path: (_ for _ in ()).throw(KeyboardInterrupt()),
    )
    assert main(["ingest", "."]) == 130


def test_cli_no_args_prints_help(capsys):
    assert main([]) == 0
    out = capsys.readouterr().out
    assert "usage: mindcart" in out
    assert "mindcart stack up" in out


def test_cli_help_includes_example(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
    assert "mindcart stack up" in capsys.readouterr().out


def test_cli_install_help_mentions_project_root(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["install", "--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "PROJECT_ROOT" in out
    assert "--target" in out


def test_cli_stack_without_subcommand_prints_help(capsys):
    assert main(["stack"]) == 0
    out = capsys.readouterr().out
    assert "up" in out
    assert "down" in out
