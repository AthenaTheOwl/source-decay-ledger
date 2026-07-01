"""Tests for source_decay_ledger.registry."""

from __future__ import annotations

from pathlib import Path

import pytest

from source_decay_ledger.registry import (
    RegistryError,
    Source,
    load_registry,
    validate_registry,
)


def _write(path: Path, body: str) -> Path:
    path.write_text(body, encoding="utf-8")
    return path


def test_seed_registry_loads(tmp_path: Path) -> None:
    seed = Path(__file__).parent.parent / "data" / "sources.yaml"
    sources = load_registry(seed)
    assert len(sources) >= 5
    assert all(isinstance(s, Source) for s in sources)
    assert {s.slug for s in sources} == {s.slug for s in sources}  # unique


def test_slug_pattern_enforced(tmp_path: Path) -> None:
    f = _write(
        tmp_path / "sources.yaml",
        """
- slug: AAA
  name: Bad Slug
  category: x
  fetch_kind: rss
  fetch_target: http://x
  added_on: 2026-01-01
  verdict: keep
""",
    )
    with pytest.raises(RegistryError, match="failed validation"):
        load_registry(f)


def test_duplicate_slug_rejected(tmp_path: Path) -> None:
    f = _write(
        tmp_path / "sources.yaml",
        """
- slug: dup
  name: First
  category: x
  fetch_kind: rss
  fetch_target: http://x
  added_on: 2026-01-01
  verdict: keep
- slug: dup
  name: Second
  category: x
  fetch_kind: rss
  fetch_target: http://y
  added_on: 2026-01-01
  verdict: keep
""",
    )
    with pytest.raises(RegistryError, match="duplicate slug"):
        load_registry(f)


def test_unknown_verdict_rejected(tmp_path: Path) -> None:
    f = _write(
        tmp_path / "sources.yaml",
        """
- slug: ok-slug
  name: x
  category: x
  fetch_kind: rss
  fetch_target: http://x
  added_on: 2026-01-01
  verdict: maybe
""",
    )
    with pytest.raises(RegistryError, match="failed validation"):
        load_registry(f)


def test_validate_registry_count(tmp_path: Path) -> None:
    f = _write(
        tmp_path / "sources.yaml",
        """
- slug: one
  name: One
  category: x
  fetch_kind: rss
  fetch_target: http://1
  added_on: 2026-01-01
  verdict: keep
- slug: two
  name: Two
  category: x
  fetch_kind: rss
  fetch_target: http://2
  added_on: 2026-01-01
  verdict: probation
""",
    )
    assert validate_registry(f) == 2


def test_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(RegistryError, match="not found"):
        load_registry(tmp_path / "nope.yaml")


def test_empty_file_returns_empty_list(tmp_path: Path) -> None:
    f = _write(tmp_path / "empty.yaml", "")
    assert load_registry(f) == []


def test_non_list_root_rejected(tmp_path: Path) -> None:
    f = _write(tmp_path / "obj.yaml", "key: value\n")
    with pytest.raises(RegistryError, match="must be a YAML list"):
        load_registry(f)


def test_malformed_yaml_raises_registry_error(tmp_path: Path) -> None:
    # A scanner error from broken YAML must surface as RegistryError, not a raw
    # yaml.YAMLError traceback.
    f = _write(tmp_path / "bad.yaml", "- slug: x\n  name: [unterminated\n")
    with pytest.raises(RegistryError, match="not valid YAML"):
        load_registry(f)


def test_directory_in_place_of_file_raises_registry_error(tmp_path: Path) -> None:
    # sources.yaml being a directory makes read_text raise OSError; that must be
    # converted to RegistryError so callers get a clean INVALID message.
    d = tmp_path / "sources.yaml"
    d.mkdir()
    with pytest.raises(RegistryError, match="cannot read registry file"):
        load_registry(d)
