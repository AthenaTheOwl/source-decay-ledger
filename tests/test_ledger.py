"""Tests for source_decay_ledger.ledger."""

from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from source_decay_ledger.ledger import (
    LedgerError,
    append_only_check,
    append_row,
    derive_item_slug,
    parse_week,
    read_week,
)


def test_parse_week_valid() -> None:
    assert parse_week("2026-W25") == (2026, 25)


def test_parse_week_rejects_garbage() -> None:
    with pytest.raises(LedgerError):
        parse_week("not-a-week")
    with pytest.raises(LedgerError):
        parse_week("2026-25")


def test_derive_item_slug_is_deterministic() -> None:
    a = derive_item_slug("https://example.com/x")
    b = derive_item_slug("https://example.com/x")
    c = derive_item_slug("https://example.com/y")
    assert a == b
    assert a != c
    assert len(a) == 16


def test_append_and_read_round_trip(tmp_path: Path) -> None:
    row = append_row(
        root=tmp_path,
        week="2026-W25",
        source_slug="ai-daily-brief",
        evidence_url="https://example.com/news/1",
        published_on=date(2026, 6, 19),
        now=datetime(2026, 6, 19, 12, 0, tzinfo=UTC),
    )
    assert row.source_slug == "ai-daily-brief"
    rows = read_week(tmp_path, "2026-W25")
    assert len(rows) == 1
    assert rows[0].item_slug == row.item_slug


def test_append_only_check_passes_clean(tmp_path: Path) -> None:
    for i in range(3):
        append_row(
            root=tmp_path,
            week="2026-W25",
            source_slug="latent-space",
            evidence_url=f"https://example.com/{i}",
            published_on=date(2026, 6, 19),
            now=datetime(2026, 6, 19, 12, 0, tzinfo=UTC),
        )
    assert append_only_check(tmp_path) == 3


def test_append_only_check_detects_rewrite(tmp_path: Path) -> None:
    append_row(
        root=tmp_path,
        week="2026-W25",
        source_slug="latent-space",
        evidence_url="https://example.com/x",
        published_on=date(2026, 6, 19),
        now=datetime(2026, 6, 19, 12, 0, tzinfo=UTC),
    )
    # Tamper: change the published date in the live ledger but not the manifest.
    ledger_file = tmp_path / "data" / "ledger" / "2026-W25.jsonl"
    text = ledger_file.read_text(encoding="utf-8")
    tampered = text.replace("2026-06-19", "2099-12-31")
    ledger_file.write_text(tampered, encoding="utf-8")
    with pytest.raises(LedgerError, match="hash mismatch"):
        append_only_check(tmp_path)


def test_append_only_check_detects_extra_row(tmp_path: Path) -> None:
    append_row(
        root=tmp_path,
        week="2026-W25",
        source_slug="latent-space",
        evidence_url="https://example.com/x",
        published_on=date(2026, 6, 19),
        now=datetime(2026, 6, 19, 12, 0, tzinfo=UTC),
    )
    ledger_file = tmp_path / "data" / "ledger" / "2026-W25.jsonl"
    with ledger_file.open("a", encoding="utf-8") as fh:
        fh.write(
            '{"item_slug":"deadbeefdeadbeef","published_on":"2026-06-19",'
            '"source_slug":"x","evidence_url":"x","appended_at":"2026-06-19T12:00:00+00:00"}\n'
        )
    with pytest.raises(LedgerError, match="not in manifest"):
        append_only_check(tmp_path)


def test_append_only_check_empty_dir(tmp_path: Path) -> None:
    assert append_only_check(tmp_path) == 0
