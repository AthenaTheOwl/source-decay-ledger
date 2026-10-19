# DEC-SDL-002: Preserve observation time during brief backfills

Date: 2026-10-18

Backfilling a missing brief can add an old publication to today's ledger. A score
claimed as of an earlier date must not count that observation before it existed.
The old scorer applied only a lower window boundary and could count future rows.
A two-row regression reproduced a count of two when only one row existed at the
chosen cutoff.

The scorer now applies inclusive lower and upper boundaries to `appended_at` and
normalizes aware timestamps to UTC without changing the instant. Older naive
ledger timestamps retain the existing UTC interpretation. `score --as-of` exposes
the cutoff as an offset-qualified timestamp; ordinary scoring still uses now.
Each score row records the cutoff it was computed at as `as_of`, and verdicts
measure `days_since_added` against that recorded cutoff. Score files written
before the field load without it and are aged at the end of their ISO week
(capped at the current time), so a committed week does not re-age as the clock
moves.

Publication date and observation date answer different questions. The score is
yield known by the cutoff, not a reconstruction of which articles were available
then. A historical registry snapshot is still needed to reconstruct membership;
a source whose `added_on` falls after the cutoff gets no verdict.
No existing ledger row or manifest is changed.
