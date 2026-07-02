"""Tests for source_decay_ledger.memo."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest

from source_decay_ledger.ledger import append_row
from source_decay_ledger.memo import (
    Verdict,
    assign_verdicts,
    prior_week,
    render_memo,
    write_memo,
)
from source_decay_ledger.registry import load_registry
from source_decay_ledger.score import score_week, write_scores


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "sources.yaml").write_text(
        """
- slug: hot
  name: Hot Source
  category: x
  fetch_kind: rss
  fetch_target: http://h
  added_on: 2026-01-01
  verdict: keep
- slug: cold-old
  name: Cold Old Source
  category: x
  fetch_kind: rss
  fetch_target: http://c
  added_on: 2026-01-01
  verdict: probation
- slug: cold-new
  name: Cold New Source
  category: x
  fetch_kind: rss
  fetch_target: http://n
  added_on: 2026-06-15
  verdict: probation
""",
        encoding="utf-8",
    )
    return tmp_path


def test_prior_week_basic() -> None:
    assert prior_week("2026-W25") == "2026-W24"
    assert prior_week("2026-W01") == "2025-W52"


def test_assign_verdicts_keep_when_count_high(repo: Path) -> None:
    now = datetime(2026, 6, 22, tzinfo=UTC)
    sources = load_registry(repo / "data" / "sources.yaml")
    for i in range(5):
        append_row(
            root=repo,
            week="2026-W25",
            source_slug="hot",
            evidence_url=f"https://example.com/{i}",
            published_on=date(2026, 6, 1),
            now=now - timedelta(days=3),
        )
    scores = score_week(repo, "2026-W25", now=now)
    verdicts = assign_verdicts(scores, sources, now=now)
    by_slug = {v.source_slug: v for v in verdicts}
    assert by_slug["hot"].verdict == "keep"


def test_assign_verdicts_drop_old_zero_yield(repo: Path) -> None:
    now = datetime(2026, 6, 22, tzinfo=UTC)
    sources = load_registry(repo / "data" / "sources.yaml")
    scores = score_week(repo, "2026-W25", now=now)  # no rows
    verdicts = assign_verdicts(scores, sources, now=now)
    by_slug = {v.source_slug: v for v in verdicts}
    # cold-old was added 2026-01-01 → > 60 days ago, 0 count → DROP
    assert by_slug["cold-old"].verdict == "drop"
    # cold-new was added 2026-06-15 → < 60 days ago, 0 count → PROBATION
    assert by_slug["cold-new"].verdict == "probation"


def test_assign_verdicts_keep_boundary_at_count_three(repo: Path) -> None:
    # Pins KEEP_COUNT_90D == 3 and the `>=` operator on memo.py:38: a source at
    # exactly 3 items in 90d must land KEEP, one at 2 items must land PROBATION.
    now = datetime(2026, 6, 22, tzinfo=UTC)
    sources = load_registry(repo / "data" / "sources.yaml")
    for i in range(3):
        append_row(
            root=repo,
            week="2026-W25",
            source_slug="hot",
            evidence_url=f"https://example.com/hot/{i}",
            published_on=date(2026, 6, 1),
            now=now - timedelta(days=3),
        )
    for i in range(2):
        append_row(
            root=repo,
            week="2026-W25",
            source_slug="cold-new",
            evidence_url=f"https://example.com/cold/{i}",
            published_on=date(2026, 6, 1),
            now=now - timedelta(days=3),
        )
    scores = score_week(repo, "2026-W25", now=now)
    verdicts = assign_verdicts(scores, sources, now=now)
    by_slug = {v.source_slug: v for v in verdicts}
    assert by_slug["hot"].verdict == "keep"
    assert by_slug["hot"].reason == "3 items in 90d"
    assert by_slug["cold-new"].verdict == "probation"


def test_assign_verdicts_drop_window_boundary_at_sixty_days(repo: Path) -> None:
    # Pins DROP_DAYS_SINCE_ADDED == 60 and the strict `>` on memo.py:42. Both
    # sources have zero yield; the one added exactly 60 days ago stays PROBATION
    # (60 is not > 60), the one added 61 days ago drops.
    now = datetime(2026, 6, 22, tzinfo=UTC)
    (repo / "data" / "sources.yaml").write_text(
        """
- slug: edge-sixty
  name: Added Exactly Sixty Days Ago
  category: x
  fetch_kind: rss
  fetch_target: http://s
  added_on: 2026-04-23
  verdict: probation
- slug: edge-sixtyone
  name: Added Sixty One Days Ago
  category: x
  fetch_kind: rss
  fetch_target: http://o
  added_on: 2026-04-22
  verdict: probation
""",
        encoding="utf-8",
    )
    sources = load_registry(repo / "data" / "sources.yaml")
    scores = score_week(repo, "2026-W25", now=now)  # no rows → zero yield
    verdicts = assign_verdicts(scores, sources, now=now)
    by_slug = {v.source_slug: v for v in verdicts}
    assert (now.date() - sources[0].added_on).days == 60
    assert (now.date() - sources[1].added_on).days == 61
    assert by_slug["edge-sixty"].verdict == "probation"
    assert by_slug["edge-sixtyone"].verdict == "drop"


def test_render_memo_has_keep_probation_drop_sections() -> None:
    verdicts = [
        Verdict("a", "keep", "5 in 90d"),
        Verdict("b", "probation", "1 in 90d"),
        Verdict("c", "drop", "0 in 90d"),
    ]
    rendered = render_memo("2026-W25", scores=[], verdicts=verdicts, prior_verdicts=None)
    assert "## KEEP" in rendered
    assert "## PROBATION" in rendered
    assert "## DROP" in rendered
    assert "no prior week" in rendered


def test_render_memo_diffs_against_prior() -> None:
    prior = [Verdict("a", "probation", "")]
    current = [Verdict("a", "keep", "")]
    rendered = render_memo("2026-W26", scores=[], verdicts=current, prior_verdicts=prior)
    assert "a: probation → keep" in rendered


def test_write_memo_produces_file(repo: Path) -> None:
    now = datetime(2026, 6, 22, tzinfo=UTC)
    scores = score_week(repo, "2026-W25", now=now)
    write_scores(repo, "2026-W25", scores)
    out = write_memo(repo, "2026-W25", now=now)
    assert out.exists()
    text = out.read_text(encoding="utf-8")
    assert "Source registry verdicts" in text
    assert "## Yield table" in text
    assert "## What changed since last week" in text
