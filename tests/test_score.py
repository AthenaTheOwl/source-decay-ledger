"""Tests for source_decay_ledger.score."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta, timezone
from pathlib import Path

import pytest

from source_decay_ledger.ledger import append_row
from source_decay_ledger.score import read_scores, score_week, write_scores


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    # Minimal registry with 2 sources
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "sources.yaml").write_text(
        """
- slug: alpha
  name: Alpha
  category: x
  fetch_kind: rss
  fetch_target: http://a
  added_on: 2026-01-01
  verdict: keep
- slug: beta
  name: Beta
  category: x
  fetch_kind: rss
  fetch_target: http://b
  added_on: 2026-01-01
  verdict: probation
""",
        encoding="utf-8",
    )
    return tmp_path


def test_score_week_zero_rows(repo: Path) -> None:
    scores = score_week(repo, "2026-W25", now=datetime(2026, 6, 22, tzinfo=UTC))
    assert {s.source_slug for s in scores} == {"alpha", "beta"}
    assert all(s.count_90d == 0 for s in scores)


def test_score_week_counts_within_windows(repo: Path) -> None:
    now = datetime(2026, 6, 22, tzinfo=UTC)
    # 4 alpha rows: 1 within 30d, 1 just outside 30d but within 90d, 1 just outside 90d, 1 very fresh
    for i, days_ago in enumerate([2, 20, 60, 100]):
        ts = now - timedelta(days=days_ago)
        append_row(
            root=repo,
            week="2026-W25",
            source_slug="alpha",
            evidence_url=f"https://example.com/a/{i}",
            published_on=date(2026, 6, 1),
            now=ts,
        )
    # 1 beta row, fresh
    append_row(
        root=repo,
        week="2026-W25",
        source_slug="beta",
        evidence_url="https://example.com/b/0",
        published_on=date(2026, 6, 1),
        now=now - timedelta(days=5),
    )
    scores = {s.source_slug: s for s in score_week(repo, "2026-W25", now=now)}
    assert scores["alpha"].count_30d == 2  # 2 days ago + 20 days ago
    assert scores["alpha"].count_90d == 3  # 2, 20, 60 days ago (100 is outside)
    assert scores["beta"].count_30d == 1
    assert scores["beta"].count_90d == 1


def test_score_results_sorted_by_count_90d_desc(repo: Path) -> None:
    now = datetime(2026, 6, 22, tzinfo=UTC)
    # alpha gets 3, beta gets 1 -> alpha sorts first
    for i in range(3):
        append_row(
            root=repo,
            week="2026-W25",
            source_slug="alpha",
            evidence_url=f"https://example.com/a/{i}",
            published_on=date(2026, 6, 1),
            now=now - timedelta(days=5),
        )
    append_row(
        root=repo,
        week="2026-W25",
        source_slug="beta",
        evidence_url="https://example.com/b/0",
        published_on=date(2026, 6, 1),
        now=now - timedelta(days=5),
    )
    scores = score_week(repo, "2026-W25", now=now)
    assert scores[0].source_slug == "alpha"
    assert scores[1].source_slug == "beta"


def test_write_and_read_scores_round_trip(repo: Path) -> None:
    now = datetime(2026, 6, 22, tzinfo=UTC)
    scores = score_week(repo, "2026-W25", now=now)
    out = write_scores(repo, "2026-W25", scores)
    assert out.exists()
    read_back = read_scores(repo, "2026-W25")
    assert len(read_back) == len(scores)
    assert {s.source_slug for s in read_back} == {s.source_slug for s in scores}


def test_historical_score_excludes_future_observations(repo: Path) -> None:
    cutoff = datetime(2026, 9, 30, 12, tzinfo=UTC)
    for i, ts in enumerate((cutoff - timedelta(days=1), cutoff + timedelta(days=1))):
        append_row(repo, "2026-W40", "alpha", f"https://example.com/{i}",
                   date(2026, 9, 29), now=ts)
    alpha = next(s for s in score_week(repo, "2026-W40", now=cutoff) if s.source_slug == "alpha")
    assert (alpha.count_30d, alpha.count_90d) == (1, 1)
    assert alpha.last_seen_at == cutoff - timedelta(days=1)


def test_historical_score_normalizes_offsets_before_window_comparison(repo: Path) -> None:
    cutoff = datetime(2026, 9, 30, 12, tzinfo=UTC)
    # 14:00+02:00 is exactly the cutoff; replacing its tzinfo would move it into the future.
    ts = cutoff.astimezone(timezone(timedelta(hours=2)))
    append_row(repo, "2026-W40", "alpha", "https://example.com/offset", date(2026, 9, 30), now=ts)
    alpha = next(s for s in score_week(repo, "2026-W40", now=cutoff) if s.source_slug == "alpha")
    assert alpha.count_30d == 1 and alpha.last_seen_at == cutoff


def test_score_cli_accepts_explicit_as_of_and_rejects_naive_time(repo: Path) -> None:
    from source_decay_ledger.cli import main

    assert main(["--root", str(repo), "score", "--week", "2026-W40",
                 "--as-of", "2026-09-30T12:00:00Z"]) == 0
    assert len(read_scores(repo, "2026-W40")) == 2
    assert main(["--root", str(repo), "score", "--week", "2026-W40",
                 "--as-of", "2026-09-30T12:00:00"]) == 2


def test_score_rows_record_cutoff_and_legacy_files_still_load(repo: Path) -> None:
    cutoff = datetime(2026, 9, 30, 14, tzinfo=timezone(timedelta(hours=2)))
    write_scores(repo, "2026-W40", score_week(repo, "2026-W40", now=cutoff))
    recorded = {s.as_of for s in read_scores(repo, "2026-W40")}
    assert recorded == {datetime(2026, 9, 30, 12, tzinfo=UTC)}
    # A score file written before `as_of` existed still loads, with no cutoff.
    (repo / "data" / "scores" / "2026-W25.jsonl").write_text(
        '{"source_slug":"alpha","count_90d":1,"count_30d":1,"last_seen_at":null}\n',
        encoding="utf-8",
    )
    assert read_scores(repo, "2026-W25")[0].as_of is None
