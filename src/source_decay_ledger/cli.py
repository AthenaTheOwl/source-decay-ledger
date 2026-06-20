"""CLI: argparse-based; subcommands compose the v0.1 loop."""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

from source_decay_ledger.ledger import (
    LedgerError,
    append_only_check,
    append_row,
    parse_week,
)
from source_decay_ledger.memo import write_memo
from source_decay_ledger.registry import RegistryError, validate_registry
from source_decay_ledger.score import score_week, write_scores


def _default_root() -> Path:
    return Path.cwd()


def cmd_validate(args: argparse.Namespace) -> int:
    root = args.root or _default_root()
    try:
        n = validate_registry(root / "data" / "sources.yaml")
    except RegistryError as err:
        print(f"INVALID: {err}", file=sys.stderr)
        return 2
    print(f"valid: {n} sources")
    return 0


def cmd_append(args: argparse.Namespace) -> int:
    root = args.root or _default_root()
    try:
        parse_week(args.week)
    except LedgerError as err:
        print(f"INVALID week: {err}", file=sys.stderr)
        return 2
    try:
        published = date.fromisoformat(args.published_on) if args.published_on else date.today()
    except ValueError as err:
        print(f"INVALID --published-on: {err}", file=sys.stderr)
        return 2
    try:
        row = append_row(
            root=root,
            week=args.week,
            source_slug=args.source,
            evidence_url=args.evidence_url,
            published_on=published,
        )
    except (LedgerError, OSError) as err:
        print(f"append failed: {err}", file=sys.stderr)
        return 3
    print(f"appended 1 row to data/ledger/{args.week}.jsonl (item_slug={row.item_slug})")
    return 0


def cmd_append_only_check(args: argparse.Namespace) -> int:
    root = args.root or _default_root()
    try:
        n = append_only_check(root)
    except LedgerError as err:
        print(f"APPEND-ONLY VIOLATION: {err}", file=sys.stderr)
        return 4
    print(f"verified {n} rows")
    return 0


def cmd_score(args: argparse.Namespace) -> int:
    root = args.root or _default_root()
    try:
        parse_week(args.week)
    except LedgerError as err:
        print(f"INVALID week: {err}", file=sys.stderr)
        return 2
    scores = score_week(root, args.week)
    out = write_scores(root, args.week, scores)
    print(f"scored {len(scores)} sources -> {out.as_posix()}")
    return 0


def cmd_memo(args: argparse.Namespace) -> int:
    root = args.root or _default_root()
    try:
        parse_week(args.week)
    except LedgerError as err:
        print(f"INVALID week: {err}", file=sys.stderr)
        return 2
    out = write_memo(root, args.week)
    print(f"wrote {out.as_posix()}")
    return 0


def cmd_full(args: argparse.Namespace) -> int:
    """The default action when no subcommand is given.

    With --dry-run: validate + would-write paths.
    Without --dry-run: validate + score + memo. Append is a manual subcommand.
    """
    root = args.root or _default_root()
    if not args.week:
        print("ERROR: --week required when no subcommand is given", file=sys.stderr)
        return 2
    try:
        parse_week(args.week)
    except LedgerError as err:
        print(f"INVALID week: {err}", file=sys.stderr)
        return 2
    try:
        n = validate_registry(root / "data" / "sources.yaml")
    except RegistryError as err:
        print(f"INVALID registry: {err}", file=sys.stderr)
        return 2
    print(f"valid: {n} sources")
    if args.dry_run:
        print(f"would write data/scores/{args.week}.jsonl")
        print(f"would write decisions/source-registry/{args.week}.md")
        return 0
    scores = score_week(root, args.week)
    out = write_scores(root, args.week, scores)
    print(f"scored {len(scores)} sources -> {out.as_posix()}")
    memo_out = write_memo(root, args.week)
    print(f"wrote {memo_out.as_posix()}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="source_decay_ledger",
        description="Weekly typed registry over brief sources, scored by yield.",
    )
    p.add_argument(
        "--root",
        type=Path,
        default=None,
        help="repo root (default: cwd)",
    )
    p.add_argument(
        "--week",
        type=str,
        default=None,
        help="ISO week YYYY-Wnn (e.g. 2026-W25)",
    )
    p.add_argument("--dry-run", action="store_true")
    sub = p.add_subparsers(dest="subcommand")

    sp = sub.add_parser("validate", help="validate data/sources.yaml")
    sp.set_defaults(func=cmd_validate)

    sp = sub.add_parser("append", help="append one row to a week's ledger")
    sp.add_argument("--week", type=str, required=True)
    sp.add_argument("--source", type=str, required=True)
    sp.add_argument("--evidence-url", type=str, required=True)
    sp.add_argument("--published-on", type=str, default=None)
    sp.set_defaults(func=cmd_append)

    sp = sub.add_parser("append-only-check", help="verify ledger hasn't been rewritten")
    sp.set_defaults(func=cmd_append_only_check)

    sp = sub.add_parser("score", help="compute weekly per-source counts")
    sp.add_argument("--week", type=str, required=True)
    sp.set_defaults(func=cmd_score)

    sp = sub.add_parser("memo", help="write the weekly KEEP/PROBATION/DROP memo")
    sp.add_argument("--week", type=str, required=True)
    sp.set_defaults(func=cmd_memo)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.subcommand:
        return args.func(args)
    return cmd_full(args)


if __name__ == "__main__":
    raise SystemExit(main())
