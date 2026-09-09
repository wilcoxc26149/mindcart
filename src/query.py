"""Query client: ask Cognee and merge shared repo memory with tenant memory."""

from __future__ import annotations

from pathlib import Path

from src.api import improve as api_improve
from src.api import recall
from src.api import remember as api_remember
from src.tenants import shared_dataset, tenant_dataset


def ask(question: str, tenant_id: str) -> str:
    """Return a contextual answer from shared repo memory plus tenant memory."""
    datasets = [shared_dataset(tenant_id), tenant_dataset(tenant_id)]
    return recall(question, datasets)


def remember(
    text: str | None,
    tenant_id: str,
    *,
    file: str | Path | None = None,
) -> None:
    """Store a personal note or file in the tenant's private memory layer.

    Pass ``text`` or ``file``, not both.
    """
    if text is not None and file is not None:
        raise RuntimeError("remember accepts text or --file, not both")
    filename: str | None = None
    if file is not None:
        path = Path(file)
        if not path.is_file():
            raise RuntimeError(f"remember file not found: {path}")
        note = path.read_text(encoding="utf-8").strip()
        filename = path.name
    elif text is not None:
        note = text.strip()
    else:
        raise RuntimeError("remember requires text or --file")
    if not note:
        raise RuntimeError("remember text must be non-empty")
    dataset = tenant_dataset(tenant_id)
    if filename:
        api_remember(note, dataset_name=dataset, filenames=[filename])
        print(f"Remembered '{filename}' in dataset '{dataset}'.")
        return
    api_remember(note, dataset_name=dataset)
    print(f"Remembered note in dataset '{dataset}'.")


def improve(tenant_id: str) -> None:
    """Enrich shared repo memory (``repo_memory`` by default)."""
    dataset = shared_dataset(tenant_id)
    api_improve(dataset)
    print(f"Improved dataset '{dataset}'.")
