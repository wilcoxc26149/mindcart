"""Unit tests for ask/remember query helpers (mocked Cognee)."""

import pytest

from src import query


def test_ask_recalls_shared_and_tenant_datasets(monkeypatch):
    monkeypatch.setattr(query, "shared_dataset", lambda tid: "repo_memory")
    monkeypatch.setattr(query, "tenant_dataset", lambda tid: f"tenant_memory_{tid}")
    captured: dict = {}

    def fake_recall(question, datasets):
        captured["question"] = question
        captured["datasets"] = datasets
        return "[1] merged answer"

    monkeypatch.setattr(query, "recall", fake_recall)
    result = query.ask("How does ingest work?", tenant_id="admin")
    assert result == "[1] merged answer"
    assert captured["question"] == "How does ingest work?"
    assert captured["datasets"] == ["repo_memory", "tenant_memory_admin"]


def test_remember_rejects_empty_text(monkeypatch):
    monkeypatch.setattr(query, "tenant_dataset", lambda tid: f"tenant_memory_{tid}")
    with pytest.raises(RuntimeError, match="non-empty"):
        query.remember("   ", tenant_id="admin")


def test_remember_writes_tenant_dataset(monkeypatch):
    monkeypatch.setattr(query, "tenant_dataset", lambda tid: f"tenant_memory_{tid}")
    captured: dict = {}

    def fake_api_remember(text, dataset_name, filenames=None):
        captured["text"] = text
        captured["dataset_name"] = dataset_name
        captured["filenames"] = filenames
        return {}

    monkeypatch.setattr(query, "api_remember", fake_api_remember)
    query.remember("use uv for local setup", tenant_id="admin")
    assert captured["text"] == "use uv for local setup"
    assert captured["dataset_name"] == "tenant_memory_admin"
    assert captured["filenames"] is None


def test_remember_file_passes_filename(tmp_path, monkeypatch):
    monkeypatch.setattr(query, "tenant_dataset", lambda tid: f"tenant_memory_{tid}")
    note = tmp_path / "note.md"
    note.write_text("We use uv for local setup.\n", encoding="utf-8")
    captured: dict = {}

    def fake_api_remember(text, dataset_name, filenames=None):
        captured["text"] = text
        captured["dataset_name"] = dataset_name
        captured["filenames"] = filenames
        return {}

    monkeypatch.setattr(query, "api_remember", fake_api_remember)
    query.remember(None, tenant_id="admin", file=note)
    assert captured["text"] == "We use uv for local setup."
    assert captured["dataset_name"] == "tenant_memory_admin"
    assert captured["filenames"] == ["note.md"]


def test_remember_rejects_text_and_file_together(tmp_path):
    note = tmp_path / "note.md"
    note.write_text("hi\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="not both"):
        query.remember("also text", tenant_id="admin", file=note)


def test_remember_rejects_missing_file(tmp_path):
    missing = tmp_path / "gone.md"
    with pytest.raises(RuntimeError, match="not found"):
        query.remember(None, tenant_id="admin", file=missing)


def test_improve_uses_shared_dataset(monkeypatch):
    monkeypatch.setattr(query, "shared_dataset", lambda tid: "repo_memory")
    captured: dict = {}

    def fake_improve(dataset_name):
        captured["dataset_name"] = dataset_name
        return {}

    monkeypatch.setattr(query, "api_improve", fake_improve)
    query.improve("admin")
    assert captured["dataset_name"] == "repo_memory"
