"""Weekly score: count rows per source in last 90d / 30d."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from pydantic import BaseModel

from source_decay_ledger.ledger import LedgerRow, iter_all_rows
from source_decay_ledger.registry import load_registry


class ScoreRow(BaseModel):
    source_slug: str
    count_90d: int
    count_30d: int
    last_seen_at: datetime | None


def _utc(value: datetime) -> datetime:
    """Legacy naive ledger timestamps are UTC; preserve aware timestamps' instants."""
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def score_week(
    root: Path,
    week: str,
    *,
    now: datetime | None = None,
) -> list[ScoreRow]:
    """Compute per-source counts as of `now` (default UTC now)."""
    cutoff_now = _utc(now or datetime.now(UTC))
    cutoff_90 = cutoff_now - timedelta(days=90)
    cutoff_30 = cutoff_now - timedelta(days=30)
    sources = load_registry(root / "data" / "sources.yaml")
    per_source: dict[str, list[LedgerRow]] = {s.slug: [] for s in sources}
    for _week, row in iter_all_rows(root):
        if row.source_slug in per_source:
            per_source[row.source_slug].append(row)
    out: list[ScoreRow] = []
    for slug, rows in per_source.items():
        observed = [_utc(r.appended_at) for r in rows if _utc(r.appended_at) <= cutoff_now]
        last = max(observed, default=None)
        out.append(
            ScoreRow(
                source_slug=slug,
                count_90d=sum(
                    1 for timestamp in observed if timestamp >= cutoff_90
                ),
                count_30d=sum(
                    1 for timestamp in observed if timestamp >= cutoff_30
                ),
                last_seen_at=last,
            )
        )
    out.sort(key=lambda r: (-r.count_90d, r.source_slug))
    return out


def write_scores(root: Path, week: str, scores: list[ScoreRow]) -> Path:
    out_path = root / "data" / "scores" / f"{week}.jsonl"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fh:
        for row in scores:
            fh.write(row.model_dump_json() + "\n")
    return out_path


def read_scores(root: Path, week: str) -> list[ScoreRow]:
    p = root / "data" / "scores" / f"{week}.jsonl"
    if not p.exists():
        return []
    return [
        ScoreRow.model_validate_json(line)
        for line in p.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
