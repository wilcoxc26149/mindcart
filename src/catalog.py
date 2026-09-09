"""Skill/rule YAML catalog: validate, render Cursor files, resolve PROJECT_ROOT."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml

from src.utils import ROOT, load_config

_SKILL_FIELDS = ("id", "name", "description", "body")
_RULE_FIELDS = ("id", "name", "description", "body")


def resolve_project_root(
    target: str | Path | None = None,
    *,
    config: dict[str, Any] | None = None,
) -> Path:
    """Return the host project Cursor should see.

    Order: ``--target`` / ``target``, then config ``project_root`` (already
    overlaid by ``PROJECT_ROOT`` env in ``load_config``), then parent of the
    MindCart cartridge.
    """
    if target is not None:
        return _existing_dir(Path(target), label="PROJECT_ROOT")
    cfg = config if config is not None else load_config()
    configured = str(cfg.get("project_root") or "").strip()
    if configured:
        return _existing_dir(Path(configured), label="PROJECT_ROOT")
    return ROOT.parent


def load_skill(path: Path) -> dict[str, Any]:
    """Load and validate one skill YAML file."""
    data = _load_mapping(path, kind="Skill")
    skill = {
        "id": _require_id(data, path, "Skill"),
        "name": _require_str(data, "name", path, "Skill"),
        "description": _require_str(data, "description", path, "Skill"),
        "body": _require_str(data, "body", path, "Skill"),
    }
    return skill


def load_rule(path: Path) -> dict[str, Any]:
    """Load and validate one rule YAML file."""
    data = _load_mapping(path, kind="Rule")
    rule: dict[str, Any] = {
        "id": _require_id(data, path, "Rule"),
        "name": _require_str(data, "name", path, "Rule"),
        "description": _require_str(data, "description", path, "Rule"),
        "body": _require_str(data, "body", path, "Rule"),
    }
    if "always_apply" in data:
        value = data["always_apply"]
        if not isinstance(value, bool):
            raise RuntimeError(f"Rule {path} field always_apply must be a boolean")
        rule["always_apply"] = value
    if "globs" in data and data["globs"] is not None:
        rule["globs"] = _parse_globs(data["globs"], path)
    return rule


def iter_yaml_files(directory: Path) -> list[Path]:
    """Return ``*.yaml`` / ``*.yml`` files directly under ``directory``."""
    if not directory.is_dir():
        return []
    return sorted(
        path
        for path in directory.iterdir()
        if path.is_file() and path.suffix.lower() in {".yaml", ".yml"}
    )


def render_skill_md(skill: dict[str, Any]) -> str:
    """Render a Cursor ``SKILL.md`` (frontmatter + body)."""
    header = _frontmatter({"name": skill["name"], "description": skill["description"]})
    return f"{header}\n{skill['body'].strip()}\n"


def render_rule_mdc(rule: dict[str, Any]) -> str:
    """Render a Cursor ``.mdc`` rule (frontmatter + body)."""
    front: dict[str, Any] = {"description": rule["description"]}
    if "always_apply" in rule:
        front["alwaysApply"] = rule["always_apply"]
    if "globs" in rule:
        globs = rule["globs"]
        front["globs"] = ", ".join(globs) if isinstance(globs, list) else globs
    header = _frontmatter(front)
    return f"{header}\n{rule['body'].strip()}\n"


def ingest_document(path: Path, rel: str) -> str:
    """Return ingest text: structured skill/rule blurbs, else a prefixed source dump."""
    posix = rel.replace("\\", "/")
    suffix = path.suffix.lower()
    if posix.startswith("skills/") and suffix in {".yaml", ".yml"}:
        return format_skill_ingest(load_skill(path), posix)
    if posix.startswith("rules/") and suffix in {".yaml", ".yml"}:
        return format_rule_ingest(load_rule(path), posix)
    body = path.read_text(encoding="utf-8")
    return f"Source file: {posix}\n\n{body}"


def format_skill_ingest(skill: dict[str, Any], rel: str) -> str:
    """Structured skill text for Cognee (not a raw YAML dump)."""
    return (
        f"MindCart skill ({rel})\n"
        f"id: {skill['id']}\n"
        f"name: {skill['name']}\n"
        f"description: {skill['description'].strip()}\n\n"
        f"{skill['body'].strip()}\n"
    )


def format_rule_ingest(rule: dict[str, Any], rel: str) -> str:
    """Structured rule text for Cognee (not a raw YAML dump)."""
    lines = [
        f"MindCart rule ({rel})",
        f"id: {rule['id']}",
        f"name: {rule['name']}",
        f"description: {rule['description'].strip()}",
    ]
    if rule.get("always_apply") is True:
        lines.append("always_apply: true")
    if "globs" in rule:
        globs = rule["globs"]
        rendered = ", ".join(globs) if isinstance(globs, list) else globs
        lines.append(f"globs: {rendered}")
    lines.append("")
    lines.append(rule["body"].strip())
    return "\n".join(lines) + "\n"


def install(*, target: str | Path | None = None) -> Path:
    """Validate cartridge YAML and write Cursor skills/rules under PROJECT_ROOT."""
    implicit_parent = False
    if target is None:
        cfg = load_config()
        implicit_parent = not str(cfg.get("project_root") or "").strip()
        project_root = resolve_project_root(target, config=cfg)
    else:
        project_root = resolve_project_root(target)

    print(f"Installing into {project_root}")
    if implicit_parent:
        print(
            "warning: using parent of this cartridge as PROJECT_ROOT; "
            "standalone checkouts should pass --target or PROJECT_ROOT=.",
            file=sys.stderr,
        )

    skills_root = project_root / ".cursor" / "skills"
    rules_root = project_root / ".cursor" / "rules"
    skill_count = 0
    rule_count = 0

    for path in iter_yaml_files(ROOT / "skills"):
        skill = load_skill(path)
        dest = skills_root / skill["id"] / "SKILL.md"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(render_skill_md(skill), encoding="utf-8")
        print(f"Installed skill {skill['id']} -> {dest}")
        skill_count += 1

    for path in iter_yaml_files(ROOT / "rules"):
        rule = load_rule(path)
        dest = rules_root / f"{rule['id']}.mdc"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(render_rule_mdc(rule), encoding="utf-8")
        print(f"Installed rule {rule['id']} -> {dest}")
        rule_count += 1

    if skill_count == 0 and rule_count == 0:
        print(f"No skills or rules to install under {ROOT}")
    print(
        f"Installed {skill_count} skill(s) and {rule_count} rule(s) into {project_root / '.cursor'}"
    )
    return project_root


_PROJECT_ROOT_HINT = "Set --target, PROJECT_ROOT, or project_root in config."


def _existing_dir(path: Path, *, label: str) -> Path:
    resolved = path.expanduser().resolve()
    if not resolved.exists():
        raise RuntimeError(f"{label} does not exist: {resolved}. {_PROJECT_ROOT_HINT}")
    if not resolved.is_dir():
        raise RuntimeError(f"{label} is not a directory: {resolved}. {_PROJECT_ROOT_HINT}")
    return resolved


def _load_mapping(path: Path, *, kind: str) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise RuntimeError(f"Invalid YAML in {path}: {exc}") from exc
    except OSError as exc:
        raise RuntimeError(f"Cannot read {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise RuntimeError(f"{kind} {path} must be a YAML mapping")
    return data


def _require_str(data: dict[str, Any], field: str, path: Path, kind: str) -> str:
    value = data.get(field)
    if not isinstance(value, str) or not value.strip():
        raise RuntimeError(f"{kind} {path} is missing required field: {field}")
    return value


def _require_id(data: dict[str, Any], path: Path, kind: str) -> str:
    ident = _require_str(data, "id", path, kind).strip()
    if ident in {".", ".."} or any(sep in ident for sep in ("/", "\\")):
        raise RuntimeError(f"{kind} {path} has invalid id: {ident}")
    return ident


def _parse_globs(value: Any, path: Path) -> str | list[str]:
    if isinstance(value, str):
        if not value.strip():
            raise RuntimeError(f"Rule {path} field globs must be a string or list of strings")
        return value.strip()
    if isinstance(value, list):
        items: list[str] = []
        for item in value:
            if not isinstance(item, str) or not item.strip():
                raise RuntimeError(f"Rule {path} field globs must be a string or list of strings")
            items.append(item.strip())
        if not items:
            raise RuntimeError(f"Rule {path} field globs must be a string or list of strings")
        return items
    raise RuntimeError(f"Rule {path} field globs must be a string or list of strings")


def _frontmatter(data: dict[str, Any]) -> str:
    dumped = yaml.safe_dump(data, sort_keys=False, allow_unicode=True).strip()
    return f"---\n{dumped}\n---"
