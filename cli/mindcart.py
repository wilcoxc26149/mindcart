"""CLI entrypoint: stack, ingest, ask, remember, update, improve, install."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.catalog import install
from src.ingestion import ingest, update
from src.query import ask, improve, remember
from src.stack import stack_down, stack_status, stack_up
from src.utils import load_config

_EPILOG = """examples:
  mindcart stack up
  mindcart ingest
  mindcart ask "How does ingest work?"
  mindcart remember "We use uv for local dev setup."
  mindcart remember --file docs/note.md
  mindcart update
  mindcart improve
  mindcart install
"""

_INSTALL_HELP = """Install validated skills and rules into the host Cursor project.

PROJECT_ROOT resolution order: --target, PROJECT_ROOT env, project_root in
config/mindcart.yaml, then the parent of this cartridge. For a standalone
checkout, use PROJECT_ROOT=. or --target PATH.
"""


def _parser() -> tuple[argparse.ArgumentParser, argparse.ArgumentParser]:
    parser = argparse.ArgumentParser(
        prog="mindcart",
        description="MindCart repo cognitive cartridge",
        epilog=_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=False)

    stack_p = sub.add_parser("stack", help="Start/stop Cognee infra (Docker)")
    stack_sub = stack_p.add_subparsers(dest="stack_command", required=False)
    up_p = stack_sub.add_parser("up", help="Bring FalkorDB, Postgres, Redis, and Cognee API online")
    up_p.add_argument("--qdrant", action="store_true", help="Also start optional Qdrant")
    stack_sub.add_parser("down", help="Stop containers (keep named volumes)")
    stack_sub.add_parser("status", help="Show container status")

    ingest_p = sub.add_parser(
        "ingest",
        help="Index the repo into Cognee",
        description="Index the repo into Cognee using globs from config/mindcart.yaml.",
    )
    ingest_p.add_argument("path", nargs="?", default=".", help="Repo path to ingest (default: .)")

    ask_p = sub.add_parser("ask", help="Ask a question against repo + tenant memory")
    ask_p.add_argument("question", help="Natural-language question")

    remember_p = sub.add_parser(
        "remember",
        help="Store a personal note or file in tenant memory",
        description="Store a personal note or file in tenant memory. Pass text or --file, not both.",
    )
    remember_p.add_argument("text", nargs="?", help="Note to remember (not together with --file)")
    remember_p.add_argument(
        "--file",
        dest="file",
        metavar="PATH",
        default=None,
        help="Read the note from this file (not together with text)",
    )

    update_p = sub.add_parser(
        "update",
        help="Re-ingest changed repo files",
        description="Re-ingest added or changed files and forget removed ones. Path defaults to .",
    )
    update_p.add_argument("path", nargs="?", default=".", help="Repo path to update (default: .)")

    sub.add_parser("improve", help="Enrich shared repo memory (Cognee improve)")

    install_p = sub.add_parser(
        "install",
        help="Install skills and rules into the host Cursor project",
        description=_INSTALL_HELP,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    install_p.add_argument(
        "--target",
        default=None,
        help="PROJECT_ROOT override (host project path). See resolution order above.",
    )
    return parser, stack_p


def main(argv: list[str] | None = None) -> int:
    parser, stack_p = _parser()
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        parser.print_help()
        return 0

    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 0

    try:
        if args.command == "stack":
            if not args.stack_command:
                stack_p.print_help()
                return 0
            if args.stack_command == "up":
                return stack_up(qdrant=args.qdrant)
            if args.stack_command == "down":
                return stack_down()
            return stack_status()
        if args.command == "ingest":
            ingest(args.path)
        elif args.command == "ask":
            cfg = load_config()
            print(ask(args.question, tenant_id=str(cfg.get("tenant_id") or "admin")))
        elif args.command == "remember":
            cfg = load_config()
            remember(
                args.text,
                tenant_id=str(cfg.get("tenant_id") or "admin"),
                file=args.file,
            )
        elif args.command == "update":
            update(args.path)
        elif args.command == "improve":
            cfg = load_config()
            improve(str(cfg.get("tenant_id") or "admin"))
        elif args.command == "install":
            install(target=args.target)
    except KeyboardInterrupt:
        return 130
    except RuntimeError as exc:
        print(f"mindcart: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
