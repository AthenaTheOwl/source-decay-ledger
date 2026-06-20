"""Smoke tests for the CLI: validate, append, score, memo, dry-run."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def repo(tmp_path: Path) -> Path:
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
""",
        encoding="utf-8",
    )
    return tmp_path


def _run(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    # Ensure the source tree is importable in tests
    repo_src = Path(__file__).parent.parent / "src"
    env["PYTHONPATH"] = str(repo_src) + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, "-m", "source_decay_ledger", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


def test_cli_validate_passes(repo: Path) -> None:
    result = _run("validate", cwd=repo)
    assert result.returncode == 0, result.stderr
    assert "valid: 1 sources" in result.stdout


def test_cli_validate_fails_on_bad_registry(tmp_path: Path) -> None:
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "sources.yaml").write_text(
        "- slug: AAA\n  name: bad\n", encoding="utf-8"
    )
    result = _run("validate", cwd=tmp_path)
    assert result.returncode == 2


def test_cli_append_and_score_and_memo(repo: Path) -> None:
    # append a row
    res1 = _run(
        "append",
        "--week",
        "2026-W25",
        "--source",
        "alpha",
        "--evidence-url",
        "https://example.com/x",
        "--published-on",
        "2026-06-19",
        cwd=repo,
    )
    assert res1.returncode == 0, res1.stderr
    assert "appended 1 row" in res1.stdout
    # score
    res2 = _run("score", "--week", "2026-W25", cwd=repo)
    assert res2.returncode == 0, res2.stderr
    assert "scored 1 sources" in res2.stdout
    assert (repo / "data" / "scores" / "2026-W25.jsonl").exists()
    # memo
    res3 = _run("memo", "--week", "2026-W25", cwd=repo)
    assert res3.returncode == 0, res3.stderr
    memo_path = repo / "decisions" / "source-registry" / "2026-W25.md"
    assert memo_path.exists()
    assert "Source registry verdicts" in memo_path.read_text(encoding="utf-8")


def test_cli_append_only_check_clean(repo: Path) -> None:
    _run(
        "append",
        "--week",
        "2026-W25",
        "--source",
        "alpha",
        "--evidence-url",
        "https://example.com/x",
        "--published-on",
        "2026-06-19",
        cwd=repo,
    )
    result = _run("append-only-check", cwd=repo)
    assert result.returncode == 0, result.stderr
    assert "verified 1 rows" in result.stdout


def test_cli_dry_run(repo: Path) -> None:
    result = _run("--week", "2026-W25", "--dry-run", cwd=repo)
    assert result.returncode == 0, result.stderr
    assert "valid: 1 sources" in result.stdout
    assert "would write data/scores/2026-W25.jsonl" in result.stdout
