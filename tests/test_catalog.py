"""Unit tests for skill/rule YAML validation, PROJECT_ROOT, and install paths."""

import pytest

from src import catalog
from src.utils import ROOT


def _skill_yaml(**overrides) -> str:
    data = {
        "id": "ask",
        "name": "ask",
        "description": "Recall from MindCart.",
        "body": "# Ask\n\nmindcart ask \"question\"\n",
    }
    data.update(overrides)
    lines = [
        f"id: {data['id']}",
        f"name: {data['name']}",
        f"description: {data['description']}",
        "body: |",
    ]
    for line in data["body"].splitlines():
        lines.append(f"  {line}")
    if not data["body"].endswith("\n"):
        lines.append("  ")
    return "\n".join(lines) + "\n"


def _rule_yaml(**overrides) -> str:
    data = {
        "id": "recall-first",
        "name": "Recall first",
        "description": "Recall before answering.",
        "body": "# Recall first\n\nmindcart ask \"question\"\n",
        "always_apply": True,
    }
    data.update(overrides)
    lines = [
        f"id: {data['id']}",
        f"name: {data['name']}",
        f"description: {data['description']}",
        f"always_apply: {str(data['always_apply']).lower()}",
        "body: |",
    ]
    for line in data["body"].splitlines():
        lines.append(f"  {line}")
    return "\n".join(lines) + "\n"


def test_load_skill_requires_fields(tmp_path):
    path = tmp_path / "ask.yaml"
    path.write_text("id: ask\nname: ask\ndescription: d\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="missing required field: body"):
        catalog.load_skill(path)


def test_load_skill_rejects_invalid_yaml(tmp_path):
    path = tmp_path / "ask.yaml"
    path.write_text("id: [unterminated\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="Invalid YAML"):
        catalog.load_skill(path)


def test_load_rule_requires_fields(tmp_path):
    path = tmp_path / "rule.yaml"
    path.write_text("id: r\nname: r\nbody: text\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="missing required field: description"):
        catalog.load_rule(path)


def test_load_rule_always_apply_must_be_bool(tmp_path):
    path = tmp_path / "rule.yaml"
    path.write_text(
        "id: r\nname: r\ndescription: d\nbody: b\nalways_apply: yes-please\n",
        encoding="utf-8",
    )
    with pytest.raises(RuntimeError, match="always_apply must be a boolean"):
        catalog.load_rule(path)


def test_load_rule_globs_string_or_list(tmp_path):
    path = tmp_path / "rule.yaml"
    path.write_text(
        "id: r\nname: r\ndescription: d\nbody: b\nglobs: src/**/*.py\n",
        encoding="utf-8",
    )
    assert catalog.load_rule(path)["globs"] == "src/**/*.py"
    path.write_text(
        "id: r\nname: r\ndescription: d\nbody: b\nglobs:\n  - a.py\n  - b.py\n",
        encoding="utf-8",
    )
    assert catalog.load_rule(path)["globs"] == ["a.py", "b.py"]


def test_default_project_root_is_parent_of_cartridge(tmp_path, monkeypatch):
    cartridge = tmp_path / "mindcart"
    cartridge.mkdir()
    monkeypatch.setattr(catalog, "ROOT", cartridge)
    assert catalog.resolve_project_root(config={}) == tmp_path.resolve()


def test_project_root_target_overrides_config(tmp_path):
    host = tmp_path / "host"
    other = tmp_path / "other"
    host.mkdir()
    other.mkdir()
    assert catalog.resolve_project_root(host, config={"project_root": str(other)}) == host.resolve()


def test_project_root_uses_config_when_no_target(tmp_path):
    host = tmp_path / "host"
    host.mkdir()
    assert catalog.resolve_project_root(config={"project_root": str(host)}) == host.resolve()


def test_project_root_missing_raises(tmp_path):
    missing = tmp_path / "nope"
    with pytest.raises(RuntimeError, match="does not exist") as exc:
        catalog.resolve_project_root(missing)
    assert "--target" in str(exc.value)


def test_install_writes_cursor_skill_and_rule(tmp_path, monkeypatch, capsys):
    cartridge = tmp_path / "cartridge"
    host = tmp_path / "host"
    (cartridge / "skills").mkdir(parents=True)
    (cartridge / "rules").mkdir()
    host.mkdir()
    (cartridge / "skills" / "ask.yaml").write_text(_skill_yaml(), encoding="utf-8")
    (cartridge / "rules" / "recall-first.yaml").write_text(_rule_yaml(), encoding="utf-8")
    monkeypatch.setattr(catalog, "ROOT", cartridge)

    dest = catalog.install(target=host)
    assert dest == host.resolve()
    captured = capsys.readouterr()
    assert f"Installing into {host.resolve()}" in captured.out
    assert "1 skill(s) and 1 rule(s)" in captured.out
    assert str(host.resolve() / ".cursor") in captured.out
    assert "standalone checkouts" not in captured.err

    skill_md = host / ".cursor" / "skills" / "ask" / "SKILL.md"
    rule_mdc = host / ".cursor" / "rules" / "recall-first.mdc"
    assert skill_md.is_file()
    assert rule_mdc.is_file()
    skill_text = skill_md.read_text(encoding="utf-8")
    assert skill_text.startswith("---\n")
    assert "name: ask" in skill_text
    assert "mindcart ask" in skill_text
    rule_text = rule_mdc.read_text(encoding="utf-8")
    assert "alwaysApply: true" in rule_text
    assert "mindcart ask" in rule_text


def test_install_warns_on_implicit_parent_default(tmp_path, monkeypatch, capsys):
    cartridge = tmp_path / "mindcart"
    (cartridge / "skills").mkdir(parents=True)
    (cartridge / "rules").mkdir()
    (cartridge / "skills" / "ask.yaml").write_text(_skill_yaml(), encoding="utf-8")
    monkeypatch.setattr(catalog, "ROOT", cartridge)
    monkeypatch.setattr(catalog, "load_config", lambda: {})

    dest = catalog.install()
    assert dest == tmp_path.resolve()
    captured = capsys.readouterr()
    assert f"Installing into {tmp_path.resolve()}" in captured.out
    assert "1 skill(s) and 0 rule(s)" in captured.out
    assert "standalone checkouts should pass --target or PROJECT_ROOT=." in captured.err


def test_install_rejects_invalid_skill(tmp_path, monkeypatch):
    cartridge = tmp_path / "cartridge"
    host = tmp_path / "host"
    (cartridge / "skills").mkdir(parents=True)
    host.mkdir()
    (cartridge / "skills" / "bad.yaml").write_text("id: bad\nname: bad\n", encoding="utf-8")
    monkeypatch.setattr(catalog, "ROOT", cartridge)
    with pytest.raises(RuntimeError, match="missing required field"):
        catalog.install(target=host)


def test_shipped_catalog_is_valid():
    skills = [catalog.load_skill(path) for path in catalog.iter_yaml_files(ROOT / "skills")]
    rules = [catalog.load_rule(path) for path in catalog.iter_yaml_files(ROOT / "rules")]
    assert {skill["id"] for skill in skills} == {"ask", "remember", "improve"}
    assert {rule["id"] for rule in rules} == {"recall-first"}
    assert rules[0]["always_apply"] is True


def test_ingest_document_skill_is_structured(tmp_path):
    path = tmp_path / "ask.yaml"
    path.write_text(_skill_yaml(), encoding="utf-8")
    text = catalog.ingest_document(path, "skills/ask.yaml")
    assert text.startswith("MindCart skill (skills/ask.yaml)")
    assert "id: ask" in text
    assert "Source file:" not in text
    assert "body: |" not in text


def test_ingest_document_regular_file_is_prefixed(tmp_path):
    path = tmp_path / "README.md"
    path.write_text("# Hello\n", encoding="utf-8")
    text = catalog.ingest_document(path, "README.md")
    assert text.startswith("Source file: README.md")
    assert "# Hello" in text
