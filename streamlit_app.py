"""source-decay-ledger - live demo (Streamlit Community Cloud).

Reads the committed weekly scores under data/scores/*.jsonl plus the typed
registry data/sources.yaml and shows the per-source signal yield: how many
brief items each source produced in the 90-day window, and the resulting
KEEP / PROBATION / DROP verdict. No network, no secrets - runs entirely off
the committed data.

Deploy: Streamlit Community Cloud -> New app -> repo AthenaTheOwl/source-decay-ledger,
branch main, main file streamlit_app.py.
"""
from __future__ import annotations

import json
from datetime import UTC, date, datetime
from pathlib import Path

import streamlit as st
import yaml

REPO = Path(__file__).resolve().parent
SCORES_DIR = REPO / "data" / "scores"
SOURCES_YAML = REPO / "data" / "sources.yaml"

KEEP_COUNT_90D = 3
DROP_DAYS_SINCE_ADDED = 60


def latest_week() -> str | None:
    files = sorted(SCORES_DIR.glob("*.jsonl")) if SCORES_DIR.exists() else []
    return files[-1].stem if files else None


def load_scores(week: str) -> list[dict]:
    path = SCORES_DIR / f"{week}.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_sources() -> dict[str, dict]:
    if not SOURCES_YAML.exists():
        return {}
    raw = yaml.safe_load(SOURCES_YAML.read_text(encoding="utf-8")) or []
    return {s["slug"]: s for s in raw}


def verdict_for(score: dict, source: dict | None, *, today: date) -> tuple[str, str]:
    """Mirror memo.assign_verdicts: KEEP_COUNT_90D, DROP_DAYS_SINCE_ADDED."""
    count_90d = score.get("count_90d", 0)
    if count_90d >= KEEP_COUNT_90D:
        return "keep", f"{count_90d} items in 90d"
    added = source.get("added_on") if source else None
    if isinstance(added, str):
        added = date.fromisoformat(added)
    days = (today - added).days if isinstance(added, date) else None
    if count_90d == 0 and days is not None and days > DROP_DAYS_SINCE_ADDED:
        return "drop", f"no items in 90d, added {days}d ago"
    tail = f", added {days}d ago" if days is not None else ""
    return "probation", f"{count_90d} items in 90d{tail}"


st.set_page_config(page_title="source-decay-ledger - source yield", layout="wide")
st.title("source-decay-ledger")
st.caption(
    "which reading-list sources earn their slot. each source is scored weekly by "
    "signal yield - the count of published brief items traced back to it - and gets "
    "a keep / probation / drop verdict."
)

week = latest_week()
if week is None:
    st.warning("no scored week found under data/scores/*.jsonl")
    st.stop()

scores = load_scores(week)
if not scores:
    st.warning(f"no scores for week {week}")
    st.stop()

sources = load_sources()
today = datetime.now(UTC).date()

rows = []
for sc in scores:
    src = sources.get(sc["source_slug"])
    verdict, reason = verdict_for(sc, src, today=today)
    rows.append(
        {
            "source": src.get("name", sc["source_slug"]) if src else sc["source_slug"],
            "slug": sc["source_slug"],
            "category": src.get("category", "-") if src else "-",
            "count_90d": sc.get("count_90d", 0),
            "count_30d": sc.get("count_30d", 0),
            "last_seen": (sc.get("last_seen_at") or "")[:10] or "-",
            "verdict": verdict,
            "reason": reason,
        }
    )
rows.sort(key=lambda r: (-r["count_90d"], r["source"]))

st.subheader(f"weekly source verdicts - {week}")

keep = [r for r in rows if r["verdict"] == "keep"]
probation = [r for r in rows if r["verdict"] == "probation"]
drop = [r for r in rows if r["verdict"] == "drop"]

c1, c2, c3 = st.columns(3)
c1.metric("keep", len(keep))
c2.metric("probation", len(probation))
c3.metric("drop", len(drop), help=f"no items in 90d and added > {DROP_DAYS_SINCE_ADDED}d ago")

verdict_filter = st.multiselect(
    "show verdicts",
    options=["keep", "probation", "drop"],
    default=["keep", "probation", "drop"],
)
shown = [r for r in rows if r["verdict"] in verdict_filter]

st.dataframe(
    [
        {
            "source": r["source"],
            "category": r["category"],
            "90d yield": r["count_90d"],
            "30d yield": r["count_30d"],
            "last seen": r["last_seen"],
            "verdict": r["verdict"].upper(),
        }
        for r in shown
    ],
    use_container_width=True,
    hide_index=True,
)

top = rows[0]
if top["count_90d"] > 0:
    st.info(
        f"**top yield:** {top['source']} - {top['count_90d']} item(s) in the 90-day window. "
        f"{len(drop)} source(s) on the kill list, {len(probation)} on probation."
    )
else:
    st.info(
        "**top yield:** none - every source is at zero items in the 90-day window, so "
        f"nothing earns a keep yet. {len(drop)} source(s) already on the kill list."
    )

if drop:
    with st.expander(f"kill list ({len(drop)} source(s))"):
        for r in drop:
            st.markdown(f"- **{r['source']}** ({r['category']}) - {r['reason']}")

st.caption(
    "v0.1 ships one scored week off 8 seed sources. the registry, append-only ledger, "
    "scoring, and verdict memo live in `src/source_decay_ledger/`; this page reads the "
    "committed `data/scores/*.jsonl` + `data/sources.yaml`. "
    "repo: github.com/AthenaTheOwl/source-decay-ledger"
)
