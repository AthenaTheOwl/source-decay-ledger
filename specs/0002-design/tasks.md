# Tasks — 0002-design

PR 1 — Foundation + registry (commitable on its own)
- [x] specs/0002-design/{requirements, design, tasks, acceptance}.md
- [ ] pyproject.toml + .python-version + uv lockfile
- [ ] src/source_decay_ledger/{__init__.py, __main__.py, cli.py} skeleton
- [ ] src/source_decay_ledger/registry.py: Pydantic models + load/validate
- [ ] data/sources.yaml: 5–10 seed sources from ai-field-brief reading list
- [ ] tests/test_registry.py
- [ ] DEC-SDL-001-yield-thresholds.md
- [ ] CLI: `validate` subcommand

PR 2 — Ledger + scoring + memo (the full v0.1 loop)
- [ ] src/source_decay_ledger/ledger.py + .manifest.jsonl format
- [ ] src/source_decay_ledger/score.py
- [ ] src/source_decay_ledger/memo.py
- [ ] CLI: `append`, `append-only-check`, `score`, `memo`, `--dry-run`
- [ ] tests/test_ledger.py
- [ ] tests/test_score.py
- [ ] tests/test_memo.py
- [ ] tests/test_cli.py (smoke)
- [ ] Generate one example ledger row + scores file + memo for week 2026-W25
- [ ] README walkthrough

PR 3 — voice_lint + acceptance
- [ ] scripts/voice_lint.py (vendored minimal banlist)
- [ ] Run voice_lint on README, memo template, DEC-SDL-001
- [ ] Run end-to-end dry-run; confirm exit 0
