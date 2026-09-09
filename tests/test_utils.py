"""Unit tests for config load, hashing, and glob walking."""

from src.utils import file_hash, load_config, walk_globs


def test_load_config_reads_yaml_and_env(tmp_path, monkeypatch):
    cfg_path = tmp_path / "mindcart.yaml"
    cfg_path.write_text(
        "cognee_api_url: http://localhost:8000\ntenant_id: admin\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("COGNEE_API_URL", "http://example.test:9000/")
    monkeypatch.setenv("TENANT_ID", "teammate1")
    monkeypatch.setenv("PROJECT_ROOT", "C:/from-env")
    data = load_config(cfg_path)
    assert data["cognee_api_url"] == "http://example.test:9000"
    assert data["tenant_id"] == "teammate1"
    assert data["project_root"] == "C:/from-env"


def test_load_config_project_root_env_overrides_yaml(tmp_path, monkeypatch):
    cfg_path = tmp_path / "mindcart.yaml"
    cfg_path.write_text("project_root: C:/from-yaml\n", encoding="utf-8")
    monkeypatch.setenv("PROJECT_ROOT", "C:/from-env")
    assert load_config(cfg_path)["project_root"] == "C:/from-env"


def test_load_config_project_root_from_yaml(tmp_path, monkeypatch):
    cfg_path = tmp_path / "mindcart.yaml"
    cfg_path.write_text("project_root: C:/from-yaml\n", encoding="utf-8")
    monkeypatch.delenv("PROJECT_ROOT", raising=False)
    assert load_config(cfg_path)["project_root"] == "C:/from-yaml"


def test_file_hash_is_stable_sha256_of_contents(tmp_path):
    path = tmp_path / "note.md"
    path.write_bytes(b"hello\n")
    digest = file_hash(path)
    assert digest == "5891b5b522d5df086d0ff0b110fbd9d21bb4fc7163af34d08286a2e846f6be03"
    assert file_hash(path) == digest
    path.write_bytes(b"hello\nworld\n")
    assert file_hash(path) != digest


def test_walk_globs_matches_files(tmp_path):
    (tmp_path / "README.md").write_text("# hi\n", encoding="utf-8")
    skills = tmp_path / "skills"
    skills.mkdir()
    (skills / "example.yaml").write_text("id: x\n", encoding="utf-8")
    (tmp_path / "skip.txt").write_text("nope\n", encoding="utf-8")
    found = walk_globs(tmp_path, ["README.md", "skills/*.yaml"])
    names = {path.name for path in found}
    assert names == {"README.md", "example.yaml"}
