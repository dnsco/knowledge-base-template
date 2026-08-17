---
type: moc
status: stub
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

A workstream is a thread, not a folder: while it was one doc it lived as a flat `workstreams/<name>.md`, because
a near-empty folder with one live note is worse than one file. It got promoted here once it had a second doc's
worth of material. A `design/` subfolder joins these two when stable reference starts accumulating.

## Start here
- [[2026-08-17-encabulator-re-encoding|Re-encoding — plan of record]] — the single canonical current-state and
  forward-path doc, and **the only doc with live state** (frontier, gates, PR numbers, next move). **Roll on
  here.**

**This folder-note is a map, not a frontier.** It does not restate status, PR numbers or what's next — a second
copy of mutable state is a copy that goes stale. Everything live is in the plan-of-record.

## Done
Finished and frozen, in `done/`. Pointers carry the still-salient fact so it stays discoverable without opening
the archive:

- [[2026-08-16-side-fumbling-baseline]] — baseline measured at 14.2 fumbles/kilocycle. **Landmine:** the counter
  resets on reticulation, so any measurement must span a full cycle or it reads low.
