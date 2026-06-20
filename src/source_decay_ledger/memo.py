"""Weekly memo: ranked yield + KEEP/PROBATION/DROP + diff vs prior week."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from source_decay_ledger.registry import Source, load_registry
from source_decay_ledger.score import ScoreRow, read_scores

KEEP_COUNT_90D = 3
DROP_DAYS_SINCE_ADDED = 60
WEEK_DURATION = timedelta(days=7)


@dataclass
class Verdict:
    source_slug: str
    verdict: str  # "keep" | "probation" | "drop"
    reason: str


def assign_verdicts(
    scores: list[ScoreRow],
    sources: list[Source],
    *,
    now: datetime | None = None,
) -> list[Verdict]:
    """Apply DEC-SDL-001 thresholds. Returns one Verdict per source."""
    cutoff_now = now or datetime.now(UTC)
    src_by_slug = {s.slug: s for s in sources}
    out: list[Verdict] = []
    for sc in scores:
        source = src_by_slug.get(sc.source_slug)
        if source is None:
            continue  # registry was edited mid-week; defer
        if sc.count_90d >= KEEP_COUNT_90D:
            out.append(Verdict(sc.source_slug, "keep", f"{sc.count_90d} items in 90d"))
            continue
        days_since_added = (cutoff_now.date() - source.added_on).days
        if sc.count_90d == 0 and days_since_added > DROP_DAYS_SINCE_ADDED:
            out.append(
                Verdict(
                    sc.source_slug,
                    "drop",
                    f"no items in 90d, added {days_since_added}d ago",
                )
            )
            continue
        out.append(
            Verdict(
                sc.source_slug,
                "probation",
                f"{sc.count_90d} items in 90d, added {days_since_added}d ago",
            )
        )
    return out


def prior_week(week: str) -> str:
    """Return the prior ISO week given YYYY-Wnn. Crude but sufficient for v0.1."""
    year_s, w_s = week.split("-W")
    year = int(year_s)
    w = int(w_s)
    if w > 1:
        return f"{year:04d}-W{w-1:02d}"
    return f"{year-1:04d}-W52"


def render_memo(
    week: str,
    scores: list[ScoreRow],
    verdicts: list[Verdict],
    prior_verdicts: list[Verdict] | None,
) -> str:
    lines: list[str] = [f"# Source registry verdicts — {week}", ""]
    lines.append("## Yield table")
    lines.append("")
    lines.append("| source | count_90d | count_30d | last_seen |")
    lines.append("| ------ | --------: | --------: | --------- |")
    for sc in scores:
        last = sc.last_seen_at.date().isoformat() if sc.last_seen_at else "—"
        lines.append(f"| {sc.source_slug} | {sc.count_90d} | {sc.count_30d} | {last} |")
    lines.append("")
    for bucket in ("keep", "probation", "drop"):
        lines.append(f"## {bucket.upper()}")
        lines.append("")
        matches = [v for v in verdicts if v.verdict == bucket]
        if not matches:
            lines.append("- (none)")
        else:
            for v in matches:
                lines.append(f"- {v.source_slug} ({v.reason})")
        lines.append("")
    lines.append("## What changed since last week")
    lines.append("")
    if prior_verdicts is None:
        lines.append("- no prior week")
    else:
        prior_by_slug = {v.source_slug: v.verdict for v in prior_verdicts}
        diffs: list[str] = []
        for v in verdicts:
            prior = prior_by_slug.get(v.source_slug)
            if prior is None:
                diffs.append(f"- {v.source_slug}: NEW → {v.verdict}")
            elif prior != v.verdict:
                diffs.append(f"- {v.source_slug}: {prior} → {v.verdict}")
        if not diffs:
            diffs.append("- no verdict changes")
        lines.extend(diffs)
    lines.append("")
    return "\n".join(lines)


def write_memo(
    root: Path,
    week: str,
    *,
    now: datetime | None = None,
) -> Path:
    scores = read_scores(root, week)
    sources = load_registry(root / "data" / "sources.yaml")
    verdicts = assign_verdicts(scores, sources, now=now)
    prior_scores = read_scores(root, prior_week(week))
    prior_verdicts = (
        assign_verdicts(prior_scores, sources, now=now) if prior_scores else None
    )
    out_path = root / "decisions" / "source-registry" / f"{week}.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        render_memo(week, scores, verdicts, prior_verdicts), encoding="utf-8"
    )
    return out_path
