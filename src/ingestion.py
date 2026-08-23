"""Repo ingestion client: extract files, docs, skills, and rules, then push to Cognee."""

from __future__ import annotations

from pathlib import Path

from src.api import remember
from src.tenants import shared_dataset
from src.utils import load_config, walk_globs


def ingest(path: str) -> None:
    """Extract documentation and code structure from ``path`` and send them to Cognee."""
    root = Path(path).resolve()
    if not root.exists():
        raise RuntimeError(f"Ingest path does not exist: {root}")
    cfg = load_config()
    globs = list((cfg.get("ingest") or {}).get("globs") or [])
    files = walk_globs(root, globs)
    if not files:
        raise RuntimeError(f"No files matched ingest globs under {root}")

    tenant_id = str(cfg.get("tenant_id") or "admin")
    dataset = shared_dataset(tenant_id)
    docs: list[str] = []
    for file in files:
        try:
            rel = file.relative_to(root).as_posix()
        except ValueError:
            rel = file.name
        body = file.read_text(encoding="utf-8")
        docs.append(f"Source file: {rel}\n\n{body}")

    remember(docs, dataset_name=dataset)
    print(f"Ingested {len(docs)} file(s) into dataset '{dataset}'.")


def update() -> None:
    """Re-ingest changed repo files into Cognee."""
    raise NotImplementedError("update is not implemented yet")
