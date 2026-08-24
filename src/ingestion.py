"""Repo ingestion client: extract files, docs, skills, and rules, then push to Cognee."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.api import forget, remember, update_data
from src.tenants import shared_dataset
from src.utils import file_hash, load_config, walk_globs

INDEX_DIR = ".mindcart"
INDEX_NAME = "ingest_index.json"


def ingest(path: str) -> None:
    """Extract documentation and code structure from ``path`` and send them to Cognee."""
    root = Path(path).resolve()
    if not root.exists():
        raise RuntimeError(f"Ingest path does not exist: {root}")
    rows = _collect_files(root)
    if not rows:
        raise RuntimeError(f"No files matched ingest globs under {root}")

    dataset = _shared_dataset()
    payload = remember(
        [row[3] for row in rows],
        dataset_name=dataset,
        filenames=[row[0] for row in rows],
    )
    index = _empty_index(dataset)
    _merge_remember_into_index(index, payload, rows, dataset)
    _write_index(root, index)
    print(f"Ingested {len(rows)} file(s) into dataset '{dataset}'.")


def update(path: str = ".") -> None:
    """Re-ingest added/changed files and forget removed files using the local ingest index."""
    root = Path(path).resolve()
    if not root.exists():
        raise RuntimeError(f"Ingest path does not exist: {root}")
    if _read_index(root) is None:
        print("No ingest index found; running a full ingest.")
        ingest(str(root))
        return

    dataset = _shared_dataset()
    index = _read_index(root) or _empty_index(dataset)
    current_rows = _collect_files(root)
    current = {rel: (file_path, digest, doc) for rel, file_path, digest, doc in current_rows}
    previous = dict(index.get("files") or {})

    added = [rel for rel in current if rel not in previous]
    removed = [rel for rel in previous if rel not in current]
    changed = [
        rel for rel in current if rel in previous and previous[rel].get("sha256") != current[rel][1]
    ]
    skipped = len(current) - len(added) - len(changed)

    if added:
        added_rows = [(rel, current[rel][0], current[rel][1], current[rel][2]) for rel in added]
        payload = remember(
            [row[3] for row in added_rows],
            dataset_name=dataset,
            filenames=[row[0] for row in added_rows],
        )
        _merge_remember_into_index(index, payload, added_rows, dataset)

    dataset_id = index.get("dataset_id")
    for rel in changed:
        data_id = (index.get("files") or {}).get(rel, {}).get("data_id") or previous.get(rel, {}).get(
            "data_id"
        )
        if not data_id:
            raise RuntimeError(f"Ingest index has no data_id for {rel}; run `mindcart ingest` again.")
        if not dataset_id:
            raise RuntimeError("Ingest index has no dataset_id; run `mindcart ingest` again.")
        update_data(
            current[rel][2],
            data_id=str(data_id),
            dataset_id=str(dataset_id),
            filename=rel,
        )
        files = index.setdefault("files", {})
        files[rel] = {"sha256": current[rel][1], "data_id": str(data_id)}

    for rel in removed:
        data_id = previous.get(rel, {}).get("data_id")
        if data_id:
            forget(dataset=dataset, data_id=str(data_id))
        files = index.setdefault("files", {})
        files.pop(rel, None)

    index["dataset"] = dataset
    _write_index(root, index)
    print(
        f"Updated dataset '{dataset}': "
        f"added {len(added)}, changed {len(changed)}, removed {len(removed)}, skipped {skipped}."
    )


def _shared_dataset() -> str:
    cfg = load_config()
    return shared_dataset(str(cfg.get("tenant_id") or "admin"))


def _collect_files(root: Path) -> list[tuple[str, Path, str, str]]:
    cfg = load_config()
    globs = list((cfg.get("ingest") or {}).get("globs") or [])
    files = walk_globs(root, globs)
    rows: list[tuple[str, Path, str, str]] = []
    for file in files:
        try:
            rel = file.relative_to(root).as_posix()
        except ValueError:
            rel = file.name
        body = file.read_text(encoding="utf-8")
        rows.append((rel, file, file_hash(file), f"Source file: {rel}\n\n{body}"))
    return rows


def _index_path(root: Path) -> Path:
    return root / INDEX_DIR / INDEX_NAME


def _empty_index(dataset: str) -> dict[str, Any]:
    return {"dataset": dataset, "dataset_id": None, "files": {}}


def _read_index(root: Path) -> dict[str, Any] | None:
    path = _index_path(root)
    if not path.is_file():
        return None
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    return data if isinstance(data, dict) else None


def _write_index(root: Path, index: dict[str, Any]) -> None:
    path = _index_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(index, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _items_from_remember(payload: dict[str, Any]) -> list[dict[str, Any]]:
    items = payload.get("items") or payload.get("data") or []
    if isinstance(items, dict):
        items = items.get("items") or []
    if not isinstance(items, list):
        return []
    return [item for item in items if isinstance(item, dict)]


def _item_data_id(item: dict[str, Any]) -> str | None:
    value = item.get("id") or item.get("data_id") or item.get("dataId")
    return str(value) if value else None


def _item_name(item: dict[str, Any]) -> str:
    name = item.get("name") or item.get("filename") or ""
    return str(name).replace("\\", "/")


def _match_data_ids(relpaths: list[str], payload: dict[str, Any]) -> dict[str, str]:
    items = _items_from_remember(payload)
    by_name: dict[str, str] = {}
    for item in items:
        data_id = _item_data_id(item)
        name = _item_name(item)
        if not data_id or not name:
            continue
        by_name[name] = data_id
        by_name[Path(name).name] = data_id
    matched: dict[str, str] = {}
    for rel in relpaths:
        if rel in by_name:
            matched[rel] = by_name[rel]
        elif Path(rel).name in by_name:
            matched[rel] = by_name[Path(rel).name]
    if len(matched) < len(relpaths) and len(items) == len(relpaths):
        for rel, item in zip(relpaths, items):
            if rel in matched:
                continue
            data_id = _item_data_id(item)
            if data_id:
                matched[rel] = data_id
    return matched


def _merge_remember_into_index(
    index: dict[str, Any],
    payload: dict[str, Any],
    rows: list[tuple[str, Path, str, str]],
    dataset: str,
) -> None:
    index["dataset"] = dataset
    dataset_id = payload.get("dataset_id") or payload.get("datasetId")
    if dataset_id:
        index["dataset_id"] = str(dataset_id)
    matched = _match_data_ids([row[0] for row in rows], payload)
    files = index.setdefault("files", {})
    for rel, _path, digest, _doc in rows:
        entry = dict(files.get(rel) or {})
        entry["sha256"] = digest
        if rel in matched:
            entry["data_id"] = matched[rel]
        files[rel] = entry
