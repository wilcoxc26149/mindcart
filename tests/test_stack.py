"""Unit tests for Docker Compose stack wrappers."""

import pytest

from src import stack


class _Proc:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_ensure_compose_requires_docker(monkeypatch):
    monkeypatch.setattr(stack.shutil, "which", lambda _name: None)
    with pytest.raises(RuntimeError, match="Docker is not installed"):
        stack.ensure_compose()


def test_ensure_compose_requires_compose_v2(monkeypatch):
    monkeypatch.setattr(stack.shutil, "which", lambda _name: "docker")
    monkeypatch.setattr(
        stack.subprocess,
        "run",
        lambda *args, **kwargs: _Proc(returncode=1, stderr="unknown command"),
    )
    with pytest.raises(RuntimeError, match="Docker Compose v2"):
        stack.ensure_compose()


def test_stack_up_compose_args(monkeypatch):
    monkeypatch.setattr(stack, "ensure_compose", lambda: None)
    captured: dict = {}

    def fake_run(args, **kwargs):
        captured["args"] = args
        return _Proc(returncode=0, stdout="started\n")

    monkeypatch.setattr(stack, "_run_compose", fake_run)
    assert stack.stack_up() == 0
    args = captured["args"]
    assert args[:3] == ["docker", "compose", "-f"]
    assert str(stack.COMPOSE_FILE) in args
    assert args[args.index("up") :][:6] == ["up", "-d", "--build", "--wait", "--wait-timeout", "300"]
    for service in stack.CORE_SERVICES:
        assert service in args
    assert "qdrant" not in args


def test_stack_up_port_conflict_prints_hint(monkeypatch, capsys):
    monkeypatch.setattr(stack, "ensure_compose", lambda: None)

    def fake_run(args, **kwargs):
        return _Proc(returncode=1, stderr="Bind for 0.0.0.0:8000 failed: port is already allocated\n")

    monkeypatch.setattr(stack, "_run_compose", fake_run)
    assert stack.stack_up() == 1
    err = capsys.readouterr().err
    assert "already in use" in err
    assert "8000" in err


def test_stack_down_uses_qdrant_profile_and_keeps_volumes(monkeypatch):
    monkeypatch.setattr(stack, "ensure_compose", lambda: None)
    captured: dict = {}

    def fake_run(args, **kwargs):
        captured["args"] = args
        return _Proc(returncode=0)

    monkeypatch.setattr(stack, "_run_compose", fake_run)
    assert stack.stack_down() == 0
    args = captured["args"]
    assert "--profile" in args
    assert "qdrant" in args
    assert "down" in args
    assert "-v" not in args
