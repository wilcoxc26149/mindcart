"""Shared utilities: config load, hashing, and file-walk helpers."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]


def load_config(path: Path | None = None) -> dict[str, Any]:
    """Load ``config/mindcart.yaml``, with env overrides for API URL and tenant."""
    load_dotenv(ROOT / ".env", override=False)
    cfg_path = path or ROOT / "config" / "mindcart.yaml"
    if not cfg_path.is_file():
        raise RuntimeError(f"MindCart config not found: {cfg_path}")
    with cfg_path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise RuntimeError(f"MindCart config must be a mapping: {cfg_path}")
    if os.getenv("COGNEE_API_URL"):
        data["cognee_api_url"] = os.environ["COGNEE_API_URL"].rstrip("/")
    if os.getenv("TENANT_ID"):
        data["tenant_id"] = os.environ["TENANT_ID"]
    data.setdefault("cognee_api_url", "http://localhost:8000")
    data.setdefault("tenant_id", "admin")
    data["cognee_api_url"] = str(data["cognee_api_url"]).rstrip("/")
    return data


def file_hash(path: Path) -> str:
    """Return a stable hash for ``path`` (used later for incremental ingest)."""
    raise NotImplementedError("file_hash is not implemented yet")


def walk_globs(root: Path, globs: list[str]) -> list[Path]:
    """Return files under ``root`` matching ``globs``."""
    base = root.resolve()
    found: set[Path] = set()
    for pattern in globs:
        found.update(candidate for candidate in base.glob(pattern) if candidate.is_file())
    return sorted(found)
