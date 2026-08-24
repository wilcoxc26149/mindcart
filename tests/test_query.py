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

    def fake_api_remember(text, dataset_name):
        captured["text"] = text
        captured["dataset_name"] = dataset_name
        return {}

    monkeypatch.setattr(query, "api_remember", fake_api_remember)
    query.remember("use uv for local setup", tenant_id="admin")
    assert captured["text"] == "use uv for local setup"
    assert captured["dataset_name"] == "tenant_memory_admin"
