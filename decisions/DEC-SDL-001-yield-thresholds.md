# DEC-SDL-001 — Yield thresholds for source verdicts

**Date**: 2026-06-20
**Status**: v0.1 (revisit after 4 weeks of data)

## Decision

A source's weekly verdict is computed from two counters:
- `count_90d` — items from this source in the last 90 days
- `days_since_added` — days since the source's `added_on` date

Verdict rules, applied in order:

1. **KEEP** if `count_90d >= 3`
2. **DROP** if `count_90d == 0` AND `days_since_added > 60`
3. **PROBATION** otherwise

## Why these numbers

v0.1 has no real signal yet — the cutoffs are starting points calibrated to the author's reading rhythm (one brief per week, ~12 items per brief). With ~12 items per brief and 13 weeks in 90 days, ~3 references means the source carries roughly its weight in the rotation.

The 60-day window before DROP gives a new source two months to prove its yield before being cut. Sources added in the last 60 days stay in PROBATION until they hit the keep threshold or age out.

## What revisits this DEC

After 4 weeks of real data the thresholds get re-examined against these questions:

- Is anything stuck in PROBATION forever?
- Is anything moving KEEP → DROP without ever stopping at PROBATION?
- Are the cutoffs producing actionable verdict diffs week-over-week, or are they too sticky to surface decay?
- Should we weight by item importance instead of treating every item-source pair equally?

Revisions land as DEC-SDL-002+.

## Out of scope for this DEC

- Multi-author rubrics
- Per-category overrides (e.g., primary-source sources may deserve KEEP even at count_90d == 1)
- Time-decay weighting (a stale item should count less than a fresh one)

These get their own decisions if the v0.1 thresholds prove inadequate.
