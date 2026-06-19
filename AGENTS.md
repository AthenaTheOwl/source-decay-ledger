# AGENTS.md — source-decay-ledger

Operating contract for AI agents (Claude, Codex, Cursor) working in
this repo. Conventions match the AthenaTheOwl portfolio so an agent
already trained on `ai-field-brief` recognizes the shape.

## What this repo is

A small weekly batch pipeline plus a typed registry plus an append-only
ledger. The product is the weekly memo under
`decisions/source-registry/`, and the ledger under `data/ledger/`.
There is no UI. The registry (`data/sources.yaml`) is the single
source of truth for which sources are in scope.

## Voice constraints

- No marketing words. The banned set will live in
  `scripts/voice_lint.py::BANNED_FAIL` once the lint script lands in
  spec 0002. Examples that always fail: leverage, demonstrate, seamless,
  cutting-edge, best-in-class, synergy.
- No antithetical reversals as a structural device.
- Plain assertions. The verdicts are the artifact; explanations stay
  short. Three sentences per source maximum in any weekly memo.

## Gates

Will land in spec `0002-weekly-pass`. The intended chain:

- `voice_lint` on every memo under `decisions/source-registry/`.
- `validate_registry`: every source in `sources.yaml` has the required
  fields and a valid `verdict` value.
- `validate_ledger`: every JSONL row in `data/ledger/` parses and
  references a known source slug and a known brief-item slug.
- `append_only_check`: no commit may modify or delete existing rows
  in any ledger file. Only appends.

## Out of scope

- A web frontend. The memos are markdown; the ledger is JSONL.
- LLM-judge scoring. Yield is a computable function of brief
  citations, not a vibe.
- Multi-user. This is a personal forcing function.
- Auto-pruning. The script emits verdicts; the human applies them
  to the OPML and the registry.
