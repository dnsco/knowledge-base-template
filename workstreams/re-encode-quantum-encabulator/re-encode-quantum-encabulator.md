---
type: moc
status: stub
date: 2026-08-17
tier: workstream
up: "[[fix-some-fundamental-architecture]]"
tags: [demo, workstream]
---

# Re-encode the quantum encabulator

> **Demo folder.** A worked example of a `workstreams/` entry — delete the whole directory once you have a real
> one.

**Workstream.** One coherent thread of work, possibly spanning several code repos. Re-encode the encabulator's
marzlevane so the side-fumbling is not merely prevented but unnecessary. Serves
**[[fix-some-fundamental-architecture]]**.

**This folder-note is the plan of record** — the map *and* the single frontier, the one place mutable state
lives: status, gates, PR numbers, what's next. There is no separate plan doc, because a workstream with one has
two frontiers waiting to diverge. If another doc here grows its own status section, that state gets migrated
back and the doc left as pure reference. When this file gets too big, move *reference* down into `design/` —
never the frontier out into a second live doc.

A workstream is a thread, not a folder: while it was one doc it lived as a flat `workstreams/<name>.md`, because
a near-empty folder with one live note is worse than one file. It got promoted here once it had a second doc's
worth of material — and a flat doc is its own plan of record by the same rule. A `design/` subfolder joins this
one when stable reference starts accumulating.

## Frontier — where are we, what's next

Answers three things in the time it takes to read them. It is the first thing every session reads, so it is the
thing to keep true.

- **Goal:** re-encode the marzlevane so side-fumbling is unnecessary rather than merely prevented.
- **State:** scoped only; nothing started. Baseline measured — see [[2026-08-16-side-fumbling-baseline]].
- **Next move:** decide the amulite question below, since it sets whether this is a week or a quarter.

Progress is recorded here as discrete line items carrying their **evidence**, because the librarian archives
strictly off these markers and never infers completion:

- ✅ done — side-fumbling baseline captured, merged #4711
- ⏳ in-flight — marzlevane encoding survey, #4730 (draft)
- ▢ not started — re-encode the logarithmic casing

A merely-open PR is `⏳`, never `✅`.

## Risks, gates & landmines

One deduped register, GATEs first, each item `[TYPE] statement — trigger → consequence → mitigation/status`.
Typed so severity is obvious at a glance; single-sourced here rather than scattered inline, because this is what
a review reads before anything else.

- [GATE] The parent grand plan's conformance gate is unmet — trigger: starting encoder changes now →
  consequence: behaviour drift ships unnoticed → status: **live, blocks all work here**.
- [LANDMINE] The fumble counter resets on reticulation — a measurement shorter than a full cycle reads low →
  always span a cycle; see [[2026-08-16-side-fumbling-baseline]] for the command.
- [OPEN Q] Is the existing prefabulated amulite reusable, or does it need re-spurving? — decides week vs quarter
  → unresolved, and the next move.
- [DEAD END] Removing the encabulator entirely — the ambifacient lunar waneshaft depends on it, so removal is not
  available. Do not re-explore.

## Done
Finished and frozen, in `done/`. Pointers carry the still-salient fact so it stays discoverable without opening
the archive:

- [[2026-08-16-side-fumbling-baseline]] — baseline measured at 14.2 fumbles/kilocycle. **Landmine:** the counter
  resets on reticulation, so any measurement must span a full cycle or it reads low.
