"""Shared utilities: config load, hashing, and file-walk helpers."""

from pathlib import Path
from typing import Any


def load_config(path: Path | None = None) -> dict[str, Any]:
    """Load ``config/mindcart.yaml``, with env overrides for API URL and tenant."""
    raise NotImplementedError("load_config is not implemented yet")


def file_hash(path: Path) -> str:
    """Return a stable hash for ``path`` (used later for incremental ingest)."""
    raise NotImplementedError("file_hash is not implemented yet")


def walk_globs(root: Path, globs: list[str]) -> list[Path]:
    """Return files under ``root`` matching ``globs``."""
    raise NotImplementedError("walk_globs is not implemented yet")
