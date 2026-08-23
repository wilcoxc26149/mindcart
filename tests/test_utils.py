"""Unit tests for config load and glob walking."""

from src.utils import load_config, walk_globs


def test_load_config_reads_yaml_and_env(tmp_path, monkeypatch):
    cfg_path = tmp_path / "mindcart.yaml"
    cfg_path.write_text(
        "cognee_api_url: http://localhost:8000\ntenant_id: admin\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("COGNEE_API_URL", "http://example.test:9000/")
    monkeypatch.setenv("TENANT_ID", "teammate1")
    data = load_config(cfg_path)
    assert data["cognee_api_url"] == "http://example.test:9000"
    assert data["tenant_id"] == "teammate1"


def test_walk_globs_matches_files(tmp_path):
    (tmp_path / "README.md").write_text("# hi\n", encoding="utf-8")
    skills = tmp_path / "skills"
    skills.mkdir()
    (skills / "example.yaml").write_text("id: x\n", encoding="utf-8")
    (tmp_path / "skip.txt").write_text("nope\n", encoding="utf-8")
    found = walk_globs(tmp_path, ["README.md", "skills/*.yaml"])
    names = {path.name for path in found}
    assert names == {"README.md", "example.yaml"}
