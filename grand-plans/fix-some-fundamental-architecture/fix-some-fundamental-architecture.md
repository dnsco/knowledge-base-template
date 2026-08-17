---
type: moc
status: stub
tier: grand-plan
tags: [demo, grand-plan]
---

# Fix some fundamental architecture

> **Demo folder.** A worked example of a `grand-plans/` entry — delete the whole directory once you have a real
> one.

**Grand plan.** Long-horizon direction that outlives the workstreams serving it: what you are heading towards
over quarters, which no single effort completes. It is not a to-do list and holds **no live status** — that lives
in the plan-of-record of whichever workstream is currently doing the work.

Work that is real but far off earns a doc like this, `status: stub`, rather than a paragraph buried in a handoff.
Handoffs get consumed and superseded; a named stub survives, accumulates detail as you learn things, and gives
every serving workstream something to point its `up:` at.

It got a folder rather than a flat `grand-plans/<name>.md` once it had a second doc's worth of material. This
file is then the folder-note: a thin map, one line per doc.

## Thesis
One paragraph on why this is worth doing and what gets cheaper or safer once it is — the claim a future reader
should be able to challenge. If you cannot state it in a paragraph you do not have a grand plan, you have an itch.

## Baseline
The measurement the premise rests on, with its date, so the premise stays checkable later: *2026-08-17 — full
rebuild 41m; the average change touches 1,900 files.* Without one you cannot tell, a year in, whether the plan is
working or whether the problem quietly solved itself.

## Depth
- [[fundamental-architecture-path-forward]] — problem anatomy, the edit inventory, the sequenced roadmap and the
  exit criteria. Kept separate so this folder-note stays a map.

## Workstreams serving this
- [[re-encode-quantum-encabulator]] — `status: stub`.

One line per workstream, no dates and no PR numbers. When one goes active it carries its own frontier and this
doc still does not restate it.
