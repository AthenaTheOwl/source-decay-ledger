# Acceptance — 0002-design

Run on a clean clone (Python 3.11, uv installed):

```bash
git clone https://github.com/AthenaTheOwl/source-decay-ledger
cd source-decay-ledger
uv sync
uv run python -m source_decay_ledger validate
# expect: exit 0, "valid: N sources"

uv run python -m source_decay_ledger append \
  --week 2026-W25 \
  --source ai-daily-brief \
  --evidence-url https://example.com/ai-news/2026-06-19 \
  --published-on 2026-06-19
# expect: exit 0, "appended 1 row to data/ledger/2026-W25.jsonl"

uv run python -m source_decay_ledger append-only-check
# expect: exit 0, "verified N rows"

uv run python -m source_decay_ledger score --week 2026-W25
# expect: exit 0, "scored N sources -> data/scores/2026-W25.jsonl"

uv run python -m source_decay_ledger memo --week 2026-W25
# expect: exit 0, "wrote decisions/source-registry/2026-W25.md"

uv run python -m source_decay_ledger --week 2026-W26 --dry-run
# expect: exit 0, "would write data/scores/2026-W26.jsonl ... would write decisions/source-registry/2026-W26.md"

uv run pytest tests/ -q
# expect: all tests pass

python scripts/voice_lint.py decisions/ README.md
# expect: 0 hits
```
