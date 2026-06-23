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
import sys
import tempfile
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import streamlit as st
import yaml

REPO = Path(__file__).resolve().parent
SCORES_DIR = REPO / "data" / "scores"
SOURCES_YAML = REPO / "data" / "sources.yaml"

# Make the real package importable on Streamlit Cloud (src layout). The
# interactive section below drives the actual scoring + verdict engine, not a
# reimplementation.
_SRC = REPO / "src"
if _SRC.exists() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

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

st.divider()

# --------------------------------------------------------------------------
# interactive: score a source yourself (drives the REAL engine)
# --------------------------------------------------------------------------
# This section imports the actual package functions used by the CLI/memo:
#   score.score_week    raw ledger rows  -> per-source 90d/30d counts
#   memo.assign_verdicts counts + source -> keep / probation / drop + reason
# The user supplies a source's added-on date, its ledger items, and the
# DEC-SDL-001 thresholds; we run the real pipeline live off a temp repo root.
import source_decay_ledger.memo as memo  # noqa: E402
from source_decay_ledger.registry import load_registry  # noqa: E402
from source_decay_ledger.score import score_week  # noqa: E402

st.subheader("score a source yourself")
st.caption(
    "give a source an added-on date and its ledger items (one brief item per "
    "line: a published date + an evidence url), set the keep/drop thresholds, "
    "and the page runs the real `score_week` + `assign_verdicts` engine - the "
    "same code the weekly memo uses - to recompute the verdict live."
)

run_week = "2026-W25"

colL, colR = st.columns(2)
with colL:
    added_on = st.date_input(
        "source added on",
        value=date(2026, 4, 1),
        help="how long the source has been on the list - feeds the DROP rule",
    )
    keep_thresh = st.slider(
        "KEEP_COUNT_90D - items in 90d needed to KEEP",
        min_value=1,
        max_value=10,
        value=memo.KEEP_COUNT_90D,
    )
    drop_days = st.slider(
        "DROP_DAYS_SINCE_ADDED - grace days before a zero-yield source can DROP",
        min_value=7,
        max_value=180,
        value=memo.DROP_DAYS_SINCE_ADDED,
    )
with colR:
    as_of = st.date_input(
        "evaluate as of",
        value=today,
        help="the 90d / 30d windows are measured back from this date",
    )
    default_ledger = "\n".join(
        [
            f"{(today - timedelta(days=5)).isoformat()}  https://example.com/post-a",
            f"{(today - timedelta(days=20)).isoformat()}  https://example.com/post-b",
            f"{(today - timedelta(days=70)).isoformat()}  https://example.com/post-c",
        ]
    )
    ledger_text = st.text_area(
        "ledger items (published_date  evidence_url)",
        value=default_ledger,
        height=160,
        help="one item per line. leave empty to model a zero-yield source.",
    )

# parse the pasted ledger into (published_on, evidence_url) pairs
parsed: list[tuple[date, str]] = []
parse_errors: list[str] = []
for i, line in enumerate(ledger_text.splitlines(), start=1):
    line = line.strip()
    if not line:
        continue
    parts = line.split(None, 1)
    if len(parts) != 2:
        parse_errors.append(f"line {i}: expected '<date> <url>', got {line!r}")
        continue
    raw_date, url = parts
    try:
        pub = date.fromisoformat(raw_date)
    except ValueError:
        parse_errors.append(f"line {i}: bad date {raw_date!r} (want YYYY-MM-DD)")
        continue
    parsed.append((pub, url.strip()))

if parse_errors:
    for err in parse_errors:
        st.warning(err)

if st.button("run the engine", type="primary"):
    as_of_dt = datetime(as_of.year, as_of.month, as_of.day, tzinfo=UTC)
    slug = "my-source"

    # build a throwaway repo root and let the REAL engine read it
    tmp_root = Path(tempfile.mkdtemp())
    (tmp_root / "data").mkdir(parents=True, exist_ok=True)
    (tmp_root / "data" / "sources.yaml").write_text(
        yaml.safe_dump(
            [
                {
                    "slug": slug,
                    "name": "My Source",
                    "category": "user-input",
                    "fetch_kind": "manual",
                    "fetch_target": "notes-only",
                    "added_on": added_on.isoformat(),
                    "verdict": "probation",
                }
            ]
        ),
        encoding="utf-8",
    )
    ledger_dir = tmp_root / "data" / "ledger"
    ledger_dir.mkdir(parents=True, exist_ok=True)
    lines = []
    for n, (pub, url) in enumerate(parsed):
        item_slug = f"useritem{n:06d}"[:64]
        appended = datetime(pub.year, pub.month, pub.day, tzinfo=UTC)
        lines.append(
            json.dumps(
                {
                    "item_slug": item_slug,
                    "published_on": pub.isoformat(),
                    "source_slug": slug,
                    "evidence_url": url or f"https://example.com/{n}",
                    "appended_at": appended.isoformat(),
                }
            )
        )
    (ledger_dir / f"{run_week}.jsonl").write_text(
        ("\n".join(lines) + "\n") if lines else "", encoding="utf-8"
    )

    # apply the user's thresholds to the real engine's module constants, then
    # restore them so we never leave the engine mutated.
    saved_keep = memo.KEEP_COUNT_90D
    saved_drop = memo.DROP_DAYS_SINCE_ADDED
    try:
        memo.KEEP_COUNT_90D = keep_thresh
        memo.DROP_DAYS_SINCE_ADDED = drop_days
        scores = score_week(tmp_root, run_week, now=as_of_dt)
        sources = load_registry(tmp_root / "data" / "sources.yaml")
        verdicts = memo.assign_verdicts(scores, sources, now=as_of_dt)
    finally:
        memo.KEEP_COUNT_90D = saved_keep
        memo.DROP_DAYS_SINCE_ADDED = saved_drop

    score_row = scores[0]
    verdict = verdicts[0]

    m1, m2, m3 = st.columns(3)
    m1.metric("90d yield", score_row.count_90d)
    m2.metric("30d yield", score_row.count_30d)
    m3.metric("verdict", verdict.verdict.upper())

    days_since = (as_of - added_on).days
    if verdict.verdict == "keep":
        st.success(
            f"**KEEP** - {verdict.reason}. "
            f"clears the bar of {keep_thresh} item(s) in 90d."
        )
    elif verdict.verdict == "drop":
        st.error(
            f"**DROP** - {verdict.reason}. "
            f"zero yield and past the {drop_days}d grace window "
            f"(added {days_since}d before the as-of date)."
        )
    else:
        st.warning(
            f"**PROBATION** - {verdict.reason}. "
            f"below the keep bar of {keep_thresh} but inside the "
            f"{drop_days}d grace window, so not dropped yet."
        )

    st.caption(
        f"engine: source_decay_ledger.score.score_week -> "
        f"source_decay_ledger.memo.assign_verdicts "
        f"(week {run_week}, {len(parsed)} ledger item(s) parsed)."
    )

st.divider()

st.caption(
    "v0.1 ships one scored week off 8 seed sources. the registry, append-only ledger, "
    "scoring, and verdict memo live in `src/source_decay_ledger/`; the top of this page "
    "reads the committed `data/scores/*.jsonl` + `data/sources.yaml`, and the section "
    "above drives the real `score_week` + `assign_verdicts` engine on your own input. "
    "repo: github.com/AthenaTheOwl/source-decay-ledger"
)
