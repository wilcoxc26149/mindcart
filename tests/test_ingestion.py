"""Unit tests for repo ingest and incremental update (mocked Cognee)."""

import json

import pytest

from src import ingestion
from src.utils import file_hash


def _cfg() -> dict:
    return {
        "tenant_id": "admin",
        "datasets": {"shared": "repo_memory", "tenant": "tenant_memory"},
        "ingest": {"globs": ["README.md", "docs/**/*.md"]},
    }


def _seed_repo(tmp_path):
    (tmp_path / "README.md").write_text("# Hello\n", encoding="utf-8")
    nested = tmp_path / "docs" / "sub"
    nested.mkdir(parents=True)
    guide = nested / "guide.md"
    guide.write_text("guide body\n", encoding="utf-8")
    return tmp_path / "README.md", guide


def test_ingest_missing_path_raises(tmp_path, monkeypatch):
    monkeypatch.setattr(ingestion, "load_config", _cfg)
    missing = tmp_path / "no-such-dir"
    with pytest.raises(RuntimeError, match="does not exist"):
        ingestion.ingest(str(missing))


def test_ingest_no_glob_matches_raises(tmp_path, monkeypatch):
    monkeypatch.setattr(ingestion, "load_config", _cfg)
    monkeypatch.setattr(ingestion, "shared_dataset", lambda _tid: "repo_memory")
    with pytest.raises(RuntimeError, match="No files matched"):
        ingestion.ingest(str(tmp_path))


def test_ingest_posts_prefixed_docs_and_writes_index(tmp_path, monkeypatch):
    monkeypatch.setattr(ingestion, "load_config", _cfg)
    monkeypatch.setattr(ingestion, "shared_dataset", lambda _tid: "repo_memory")
    readme, guide = _seed_repo(tmp_path)
    captured: dict = {}

    def fake_remember(docs, dataset_name, filenames=None):
        captured["docs"] = docs
        captured["dataset_name"] = dataset_name
        captured["filenames"] = filenames
        return {
            "dataset_id": "ds-1",
            "items": [{"id": f"id-{name}", "name": name} for name in (filenames or [])],
        }

    monkeypatch.setattr(ingestion, "remember", fake_remember)
    ingestion.ingest(str(tmp_path))

    assert captured["dataset_name"] == "repo_memory"
    assert set(captured["filenames"]) == {"README.md", "docs/sub/guide.md"}
    prefixes = {doc.split("\n\n", 1)[0] for doc in captured["docs"]}
    assert prefixes == {"Source file: README.md", "Source file: docs/sub/guide.md"}

    index_path = tmp_path / ".mindcart" / "ingest_index.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    assert index["dataset"] == "repo_memory"
    assert index["dataset_id"] == "ds-1"
    assert index["files"]["README.md"]["data_id"] == "id-README.md"
    assert index["files"]["README.md"]["sha256"] == file_hash(readme)
    assert index["files"]["docs/sub/guide.md"]["data_id"] == "id-docs/sub/guide.md"
    assert index["files"]["docs/sub/guide.md"]["sha256"] == file_hash(guide)


def test_update_without_index_runs_ingest(tmp_path, monkeypatch):
    monkeypatch.setattr(ingestion, "load_config", _cfg)
    monkeypatch.setattr(ingestion, "shared_dataset", lambda _tid: "repo_memory")
    _seed_repo(tmp_path)
    called = {"remember": 0}

    def fake_remember(docs, dataset_name, filenames=None):
        called["remember"] += 1
        return {
            "dataset_id": "ds-1",
            "items": [{"id": f"id-{name}", "name": name} for name in (filenames or [])],
        }

    monkeypatch.setattr(ingestion, "remember", fake_remember)
    ingestion.update(str(tmp_path))
    assert called["remember"] == 1
    assert (tmp_path / ".mindcart" / "ingest_index.json").is_file()


def test_update_skips_unchanged_files(tmp_path, monkeypatch):
    monkeypatch.setattr(ingestion, "load_config", _cfg)
    monkeypatch.setattr(ingestion, "shared_dataset", lambda _tid: "repo_memory")
    readme, guide = _seed_repo(tmp_path)
    index = {
        "dataset": "repo_memory",
        "dataset_id": "ds-1",
        "files": {
            "README.md": {"sha256": file_hash(readme), "data_id": "id-readme"},
            "docs/sub/guide.md": {"sha256": file_hash(guide), "data_id": "id-guide"},
        },
    }
    index_path = tmp_path / ".mindcart"
    index_path.mkdir()
    (index_path / "ingest_index.json").write_text(json.dumps(index), encoding="utf-8")

    monkeypatch.setattr(
        ingestion,
        "remember",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("remember should not run")),
    )
    monkeypatch.setattr(
        ingestion,
        "update_data",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("update_data should not run")),
    )
    monkeypatch.setattr(
        ingestion,
        "forget",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("forget should not run")),
    )
    ingestion.update(str(tmp_path))


def test_update_add_calls_remember(tmp_path, monkeypatch):
    monkeypatch.setattr(ingestion, "load_config", _cfg)
    monkeypatch.setattr(ingestion, "shared_dataset", lambda _tid: "repo_memory")
    readme, guide = _seed_repo(tmp_path)
    index = {
        "dataset": "repo_memory",
        "dataset_id": "ds-1",
        "files": {
            "README.md": {"sha256": file_hash(readme), "data_id": "id-readme"},
        },
    }
    (tmp_path / ".mindcart").mkdir()
    (tmp_path / ".mindcart" / "ingest_index.json").write_text(json.dumps(index), encoding="utf-8")
    captured: dict = {}

    def fake_remember(docs, dataset_name, filenames=None):
        captured["filenames"] = filenames
        return {
            "dataset_id": "ds-1",
            "items": [{"id": "id-guide", "name": "docs/sub/guide.md"}],
        }

    monkeypatch.setattr(ingestion, "remember", fake_remember)
    monkeypatch.setattr(
        ingestion,
        "update_data",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("update_data should not run")),
    )
    ingestion.update(str(tmp_path))
    assert captured["filenames"] == ["docs/sub/guide.md"]
    saved = json.loads((tmp_path / ".mindcart" / "ingest_index.json").read_text(encoding="utf-8"))
    assert saved["files"]["docs/sub/guide.md"]["data_id"] == "id-guide"
    assert saved["files"]["docs/sub/guide.md"]["sha256"] == file_hash(guide)


def test_update_change_calls_update_data_not_remember(tmp_path, monkeypatch):
    monkeypatch.setattr(ingestion, "load_config", _cfg)
    monkeypatch.setattr(ingestion, "shared_dataset", lambda _tid: "repo_memory")
    readme, guide = _seed_repo(tmp_path)
    index = {
        "dataset": "repo_memory",
        "dataset_id": "ds-1",
        "files": {
            "README.md": {"sha256": file_hash(readme), "data_id": "id-readme"},
            "docs/sub/guide.md": {"sha256": file_hash(guide), "data_id": "id-guide"},
        },
    }
    (tmp_path / ".mindcart").mkdir()
    (tmp_path / ".mindcart" / "ingest_index.json").write_text(json.dumps(index), encoding="utf-8")
    readme.write_text("# Hello changed\n", encoding="utf-8")
    captured: dict = {}

    def fake_update(data, data_id, dataset_id, filename):
        captured["data_id"] = data_id
        captured["dataset_id"] = dataset_id
        captured["filename"] = filename
        captured["data"] = data

    monkeypatch.setattr(ingestion, "update_data", fake_update)
    monkeypatch.setattr(
        ingestion,
        "remember",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("remember should not run")),
    )
    ingestion.update(str(tmp_path))
    assert captured["data_id"] == "id-readme"
    assert captured["dataset_id"] == "ds-1"
    assert captured["filename"] == "README.md"
    assert "Hello changed" in captured["data"]
    saved = json.loads((tmp_path / ".mindcart" / "ingest_index.json").read_text(encoding="utf-8"))
    assert saved["files"]["README.md"]["sha256"] == file_hash(readme)
    assert saved["files"]["README.md"]["data_id"] == "id-readme"


def test_ingest_sends_structured_skill_not_raw_yaml(tmp_path, monkeypatch):
    def cfg():
        return {
            "tenant_id": "admin",
            "datasets": {"shared": "repo_memory", "tenant": "tenant_memory"},
            "ingest": {"globs": ["skills/*.yaml"]},
        }

    monkeypatch.setattr(ingestion, "load_config", cfg)
    monkeypatch.setattr(ingestion, "shared_dataset", lambda _tid: "repo_memory")
    skills = tmp_path / "skills"
    skills.mkdir()
    (skills / "ask.yaml").write_text(
        "id: ask\nname: ask\ndescription: Recall from MindCart.\nbody: |\n  Run mindcart ask.\n",
        encoding="utf-8",
    )
    captured: dict = {}

    def fake_remember(docs, dataset_name, filenames=None):
        captured["docs"] = docs
        captured["filenames"] = filenames
        return {
            "dataset_id": "ds-1",
            "items": [{"id": "id-ask", "name": "skills/ask.yaml"}],
        }

    monkeypatch.setattr(ingestion, "remember", fake_remember)
    ingestion.ingest(str(tmp_path))
    assert captured["filenames"] == ["skills/ask.yaml"]
    doc = captured["docs"][0]
    assert doc.startswith("MindCart skill (skills/ask.yaml)")
    assert "id: ask" in doc
    assert "Run mindcart ask." in doc
    assert "Source file:" not in doc
    assert "body: |" not in doc


def test_ingest_rejects_invalid_skill_yaml(tmp_path, monkeypatch):
    def cfg():
        return {
            "tenant_id": "admin",
            "datasets": {"shared": "repo_memory", "tenant": "tenant_memory"},
            "ingest": {"globs": ["skills/*.yaml"]},
        }

    monkeypatch.setattr(ingestion, "load_config", cfg)
    monkeypatch.setattr(ingestion, "shared_dataset", lambda _tid: "repo_memory")
    skills = tmp_path / "skills"
    skills.mkdir()
    (skills / "bad.yaml").write_text("id: bad\nname: bad\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="missing required field"):
        ingestion.ingest(str(tmp_path))


def test_update_remove_calls_forget(tmp_path, monkeypatch):
    monkeypatch.setattr(ingestion, "load_config", _cfg)
    monkeypatch.setattr(ingestion, "shared_dataset", lambda _tid: "repo_memory")
    readme, guide = _seed_repo(tmp_path)
    index = {
        "dataset": "repo_memory",
        "dataset_id": "ds-1",
        "files": {
            "README.md": {"sha256": file_hash(readme), "data_id": "id-readme"},
            "docs/sub/guide.md": {"sha256": file_hash(guide), "data_id": "id-guide"},
            "gone.md": {"sha256": "abc", "data_id": "id-gone"},
        },
    }
    (tmp_path / ".mindcart").mkdir()
    (tmp_path / ".mindcart" / "ingest_index.json").write_text(json.dumps(index), encoding="utf-8")
    captured: dict = {}

    def fake_forget(*, dataset, data_id):
        captured["dataset"] = dataset
        captured["data_id"] = data_id

    monkeypatch.setattr(ingestion, "forget", fake_forget)
    monkeypatch.setattr(
        ingestion,
        "remember",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("remember should not run")),
    )
    monkeypatch.setattr(
        ingestion,
        "update_data",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("update_data should not run")),
    )
    ingestion.update(str(tmp_path))
    assert captured == {"dataset": "repo_memory", "data_id": "id-gone"}
    saved = json.loads((tmp_path / ".mindcart" / "ingest_index.json").read_text(encoding="utf-8"))
    assert "gone.md" not in saved["files"]
    assert "README.md" in saved["files"]
