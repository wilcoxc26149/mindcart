"""Tenant routing: shared repo memory vs private per-user memory."""

from __future__ import annotations

from src.utils import load_config


def _tenant_id(tenant_id: str) -> str:
    tid = (tenant_id or "").strip()
    if tid:
        return tid
    cfg = load_config()
    return str(cfg.get("tenant_id") or "admin").strip() or "admin"


def shared_dataset(tenant_id: str) -> str:
    """Return the shared repo-memory dataset name for ``tenant_id``."""
    cfg = load_config()
    datasets = cfg.get("datasets") or {}
    return str(datasets.get("shared") or "repo_memory")


def tenant_dataset(tenant_id: str) -> str:
    """Return the private tenant-memory dataset name for ``tenant_id``."""
    cfg = load_config()
    datasets = cfg.get("datasets") or {}
    prefix = str(datasets.get("tenant") or "tenant_memory")
    return f"{prefix}_{_tenant_id(tenant_id)}"
