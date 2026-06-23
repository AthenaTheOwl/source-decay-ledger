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
from source_decay_ledger.memo import assign_verdicts, write_memo
from source_decay_ledger.registry import RegistryError, load_registry, validate_registry
from source_decay_ledger.score import read_scores, score_week, write_scores


def _default_root() -> Path:
    return Path.cwd()


def _repo_root() -> Path:
    """Repo root inferred from this file: src/source_decay_ledger/cli.py -> repo."""
    return Path(__file__).resolve().parent.parent.parent


def _latest_scored_week(root: Path) -> str | None:
    """Return the most recent YYYY-Wnn that has a committed score file."""
    scores_dir = root / "data" / "scores"
    if not scores_dir.exists():
        return None
    weeks = sorted(p.stem for p in scores_dir.glob("*.jsonl") if p.stem)
    return weeks[-1] if weeks else None


_VERDICT_GLYPH = {"keep": "KEEP", "probation": "PROBATION", "drop": "DROP"}


def cmd_show(args: argparse.Namespace) -> int:
    """Print a readable, ranked verdict view from committed data. No args, offline.

    Reads data/scores/<latest>.jsonl + data/sources.yaml and prints the ranked
    yield table plus a KEEP/PROBATION/DROP summary and a headline finding.
    """
    # Prefer an explicit --root, then cwd if it looks like the repo (has data/),
    # else fall back to the repo this package was installed from so a bare
    # `... show` still works when invoked from an unrelated directory.
    root = args.root
    if root is None:
        cwd = _default_root()
        if (cwd / "data").exists():
            root = cwd
        else:
            root = _repo_root()

    week = args.week or _latest_scored_week(root)
    if week is None:
        print(
            "no scored week found under data/scores/*.jsonl — "
            "run `score --week <YYYY-Wnn>` first",
            file=sys.stderr,
        )
        return 1

    scores = read_scores(root, week)
    if not scores:
        print(f"no scores for week {week}", file=sys.stderr)
        return 1
    sources = load_registry(root / "data" / "sources.yaml")
    name_by_slug = {s.slug: s.name for s in sources}
    verdicts = assign_verdicts(scores, sources)
    verdict_by_slug = {v.verdict: [] for v in verdicts}
    for v in verdicts:
        verdict_by_slug.setdefault(v.verdict, []).append(v)

    print(f"source-decay-ledger - weekly source verdicts, {week}")
    print(
        f"{len(scores)} source(s), ranked by 90-day signal yield "
        "(brief items traced back to each source)\n"
    )

    header = f"{'source':<22} {'90d':>4} {'30d':>4} {'last seen':<12} verdict"
    print(header)
    print("-" * len(header))
    for sc in scores:
        verdict = next((v.verdict for v in verdicts if v.source_slug == sc.source_slug), "-")
        last = sc.last_seen_at.date().isoformat() if sc.last_seen_at else "-"
        name = name_by_slug.get(sc.source_slug, sc.source_slug)
        print(
            f"{name[:22]:<22} {sc.count_90d:>4} {sc.count_30d:>4} "
            f"{last:<12} {_VERDICT_GLYPH.get(verdict, verdict)}"
        )

    keep = verdict_by_slug.get("keep", [])
    probation = verdict_by_slug.get("probation", [])
    drop = verdict_by_slug.get("drop", [])
    print(
        f"\nverdicts: {len(keep)} keep, {len(probation)} probation, {len(drop)} drop"
    )

    top = scores[0]
    if top.count_90d > 0:
        print(
            f"top yield: {name_by_slug.get(top.source_slug, top.source_slug)} "
            f"({top.count_90d} item(s) in 90d)."
        )
    else:
        print("top yield: none — every source is at zero items in the 90-day window.")
    if drop:
        names = ", ".join(name_by_slug.get(v.source_slug, v.source_slug) for v in drop)
        print(f"kill list: {names}.")
    else:
        print("kill list: empty.")
    return 0


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

    sp = sub.add_parser(
        "show",
        help="print a readable ranked verdict view from committed data (no args)",
    )
    sp.add_argument(
        "--week",
        type=str,
        default=None,
        help="ISO week to show (default: latest committed score file)",
    )
    sp.set_defaults(func=cmd_show)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.subcommand:
        return args.func(args)
    return cmd_full(args)


if __name__ == "__main__":
    raise SystemExit(main())
