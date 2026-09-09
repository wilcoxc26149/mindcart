"""Unit tests for env/cursor configure helpers."""

from src.configure import configure_env


def test_configure_env_copies_sample_when_missing(tmp_path):
    (tmp_path / ".env.sample").write_text("TENANT_ID=admin\n", encoding="utf-8")
    dest = configure_env(root=tmp_path)
    assert dest == tmp_path / ".env"
    assert dest.read_text(encoding="utf-8") == "TENANT_ID=admin\n"


def test_configure_env_keeps_existing_env(tmp_path):
    (tmp_path / ".env.sample").write_text("FROM=sample\n", encoding="utf-8")
    existing = tmp_path / ".env"
    existing.write_text("FROM=existing\n", encoding="utf-8")
    dest = configure_env(root=tmp_path)
    assert dest.read_text(encoding="utf-8") == "FROM=existing\n"
