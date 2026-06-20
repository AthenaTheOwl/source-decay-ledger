"""Append-only ledger: typed rows + manifest of sha256 fingerprints."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterator
from datetime import UTC, date, datetime
from pathlib import Path

from pydantic import BaseModel, Field

WEEK_PATTERN = re.compile(r"^(\d{4})-W(\d{2})$")


class LedgerRow(BaseModel):
    item_slug: str = Field(min_length=8, max_length=64)
    published_on: date
    source_slug: str
    evidence_url: str
    appended_at: datetime


class LedgerError(Exception):
    """Append-only invariant violated, or week-name malformed."""


def parse_week(week: str) -> tuple[int, int]:
    m = WEEK_PATTERN.match(week)
    if not m:
        raise LedgerError(f"week {week!r} must match YYYY-Wnn, e.g. 2026-W25")
    return int(m.group(1)), int(m.group(2))


def ledger_path(root: Path, week: str) -> Path:
    parse_week(week)
    return root / "data" / "ledger" / f"{week}.jsonl"


def manifest_path(root: Path) -> Path:
    return root / "data" / "ledger" / ".manifest.jsonl"


def _row_hash(row: LedgerRow) -> str:
    payload = json.dumps(
        {
            "item_slug": row.item_slug,
            "published_on": row.published_on.isoformat(),
            "source_slug": row.source_slug,
            "evidence_url": row.evidence_url,
            "appended_at": row.appended_at.isoformat(),
        },
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def derive_item_slug(evidence_url: str) -> str:
    """Deterministic short slug from evidence_url so duplicates are detectable."""
    return hashlib.sha256(evidence_url.encode("utf-8")).hexdigest()[:16]


def append_row(
    root: Path,
    week: str,
    source_slug: str,
    evidence_url: str,
    published_on: date,
    *,
    now: datetime | None = None,
) -> LedgerRow:
    """Append a row to data/ledger/<week>.jsonl AND data/ledger/.manifest.jsonl."""
    appended_at = now or datetime.now(UTC)
    row = LedgerRow(
        item_slug=derive_item_slug(evidence_url),
        published_on=published_on,
        source_slug=source_slug,
        evidence_url=evidence_url,
        appended_at=appended_at,
    )
    path = ledger_path(root, week)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(row.model_dump_json() + "\n")
    mpath = manifest_path(root)
    with mpath.open("a", encoding="utf-8") as fh:
        manifest_entry = {
            "week": week,
            "item_slug": row.item_slug,
            "sha256": _row_hash(row),
        }
        fh.write(json.dumps(manifest_entry, sort_keys=True) + "\n")
    return row


def read_week(root: Path, week: str) -> list[LedgerRow]:
    path = ledger_path(root, week)
    if not path.exists():
        return []
    out: list[LedgerRow] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        out.append(LedgerRow.model_validate_json(line))
    return out


def iter_all_rows(root: Path) -> Iterator[tuple[str, LedgerRow]]:
    """Yield (week, row) across every committed week file. Skips manifest + hidden."""
    base = root / "data" / "ledger"
    if not base.exists():
        return
    for path in sorted(base.glob("*.jsonl")):
        if path.name.startswith("."):
            continue
        if not WEEK_PATTERN.match(path.stem):
            continue
        week = path.stem
        for row in read_week(root, week):
            yield week, row


def append_only_check(root: Path) -> int:
    """Verify every manifest row's hash matches the live ledger.

    Returns number of rows verified. Raises LedgerError on first mismatch.
    """
    mpath = manifest_path(root)
    if not mpath.exists():
        return 0
    manifest_entries: dict[tuple[str, str], str] = {}
    for line in mpath.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        entry = json.loads(line)
        manifest_entries[(entry["week"], entry["item_slug"])] = entry["sha256"]
    if not manifest_entries:
        return 0
    verified = 0
    for week, row in iter_all_rows(root):
        key = (week, row.item_slug)
        expected = manifest_entries.get(key)
        if expected is None:
            raise LedgerError(
                f"row {row.item_slug!r} in week {week} not in manifest "
                "(insertion outside append-row path?)"
            )
        actual = _row_hash(row)
        if actual != expected:
            raise LedgerError(
                f"row {row.item_slug!r} in week {week} hash mismatch "
                f"(manifest={expected[:12]}..., actual={actual[:12]}...): row was rewritten"
            )
        verified += 1
    return verified
