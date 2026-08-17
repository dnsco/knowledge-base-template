---
type: journal
status: done
date: 2026-08-16
tags: [demo, workstream]
up: "[[re-encode-quantum-encabulator]]"
---

# Side-fumbling baseline

> **Demo file.** Delete with its folder.

A small finished task, archived. `done/` is **frozen history** — opened only to re-examine completed work, never
for current state. Working agents never write here and never edit what is here; only the librarian moves things
in, and only off an explicit evidence-bearing marker.

**✅ done — merged #4711** (2026-08-16). Instrumented the encabulator's fumble counter and captured a baseline
before touching the encoding, so the premise stays checkable later.

**Outcome:** 14.2 fumbles/kilocycle, averaged over six full reticulation cycles.

## Reusable command

Captured so the next agent re-runs it instead of re-deriving it — the whole point of writing any of this down:

```bash
encabulate --probe=marzlevane --cycles=6 --emit=fumbles | awk '{s+=$2; n++} END {print s/n}'
```

`--cycles` must be ≥1 whole cycle. Anything shorter reads low.

## What was learned

- **Landmine:** the fumble counter resets on reticulation, so a sub-cycle measurement under-reports. Cost half a
  day before it was noticed; it survives in the plan-of-record's risk register, which is why the pointer in the
  folder-note repeats it rather than just naming this file.
- **Dead end:** sampling the waneshaft instead of the marzlevane — the waneshaft aggregates two fumble sources and
  cannot attribute them. Do not re-explore.

Notice what the archive keeps: substance **verbatim**, not summarized away. A future deep-dive needs the command
and the reason, and a one-line synopsis would have destroyed both.
