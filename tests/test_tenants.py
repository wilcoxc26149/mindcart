"""Unit tests for shared vs tenant dataset names."""

from src.tenants import shared_dataset, tenant_dataset


def test_shared_dataset_from_config(monkeypatch):
    monkeypatch.setattr(
        "src.tenants.load_config",
        lambda: {"datasets": {"shared": "repo_memory", "tenant": "tenant_memory"}, "tenant_id": "admin"},
    )
    assert shared_dataset("admin") == "repo_memory"


def test_tenant_dataset_suffixes_id(monkeypatch):
    monkeypatch.setattr(
        "src.tenants.load_config",
        lambda: {"datasets": {"shared": "repo_memory", "tenant": "tenant_memory"}, "tenant_id": "admin"},
    )
    assert tenant_dataset("teammate1") == "tenant_memory_teammate1"
    assert tenant_dataset("") == "tenant_memory_admin"
