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


def _not_implemented(exc: NotImplementedError) -> int:
    print(f"not implemented: {exc}", file=sys.stderr)
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mindcart", description="MindCart repo cognitive cartridge")
    sub = parser.add_subparsers(dest="command", required=True)

    stack_p = sub.add_parser("stack", help="Start/stop Cognee infra (Docker)")
    stack_sub = stack_p.add_subparsers(dest="stack_command", required=True)
    up_p = stack_sub.add_parser("up", help="Bring FalkorDB, Postgres, Redis, and Cognee API online")
    up_p.add_argument("--qdrant", action="store_true", help="Also start optional Qdrant")
    stack_sub.add_parser("down", help="Stop containers (keep named volumes)")
    stack_sub.add_parser("status", help="Show container status")

    ingest_p = sub.add_parser("ingest", help="Index the repo into Cognee")
    ingest_p.add_argument("path", nargs="?", default=".", help="Repo path to ingest")

    ask_p = sub.add_parser("ask", help="Ask a question against repo + tenant memory")
    ask_p.add_argument("question", help="Natural-language question")

    remember_p = sub.add_parser("remember", help="Store a personal note or file in tenant memory")
    remember_p.add_argument("text", nargs="?", help="Note to remember")
    remember_p.add_argument(
        "--file",
        dest="file",
        metavar="PATH",
        default=None,
        help="Read the note from this file (not together with text)",
    )

    update_p = sub.add_parser("update", help="Re-ingest changed repo files")
    update_p.add_argument("path", nargs="?", default=".", help="Repo path to update")

    sub.add_parser("improve", help="Enrich shared repo memory (Cognee improve)")

    install_p = sub.add_parser("install", help="Install skills and rules into the host Cursor project")
    install_p.add_argument(
        "--target",
        default=None,
        help="PROJECT_ROOT override (host project path)",
    )

    args = parser.parse_args(argv)

    try:
        if args.command == "stack":
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
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except NotImplementedError as exc:
        return _not_implemented(exc)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
