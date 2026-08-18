---
name: context-dump
description: Append-only capture of working context, findings, and handoffs into the LLM knowledge base at {{VAULT_PATH}} — the durable cross-session memory for engineering work (a separate git repo / Obsidian vault spanning every project I work on; usually reachable as a {{VAULT}}/ symlink in the current project root). Use at the end of a work session, before a handoff, or whenever you've learned something worth persisting for the next session — to write a dated journal/handoff entry and keep the live "where are we / what's next" frontier truthful. This skill only ADDS and updates status; it never deletes, merges, restructures, archives, or re-links docs (that destructive cleanup is the separate "librarian" pass). Invoke when asked to "dump context", "write a handoff", "save findings to the vault", "checkpoint the workstream", or before ending a long session.
---

# context-dump — append-only capture into the LLM knowledge base

Persist what you did and learned into `{{VAULT_PATH}}` — the durable cross-session memory for engineering work —
so the next session can pick up where you left off.

**This skill is append-only / non-destructive.** You ADD docs and keep the live frontier truthful. You do NOT
consolidate, merge, delete, archive, or re-link — those destructive, cross-cutting ops are the **librarian's**
job, run as a separate deliberate pass. Concentrating all destruction in the librarian is what prevents parallel
agents from silently clobbering each other's notes (the failure that append-only structurally avoids).

The vault is its **own git repo** (separate from whatever repo you're working in) and an Obsidian graph: dated
long-form docs, a root `README.md` map, per-workstream folders with a `<folder>/<folder>.md` folder-note
(mini-MOC), and a `done/` archive. **One vault covers every project** — it is usually symlinked into the current
project root as `{{VAULT}}/`, so you can read and grep it as in-tree paths. Full conventions:
`{{VAULT_PATH}}/CLAUDE.md`.

## Do

1. **Read the conventions, then locate the workstream.** If you have not already read
   `{{VAULT_PATH}}/CLAUDE.md` this session, read it now — a session rooted in a code project does **not** load it
   automatically, so assume you haven't. Then skim `{{VAULT_PATH}}/README.md` (the map) + the relevant
   `workstreams/<name>/<name>.md` folder-note. Use the existing workstream if your work fits one; if it's
   genuinely new, you may create `workstreams/<name>/` + a `<name>.md` folder-note.
2. **Write a dated journal/handoff entry** — `workstreams/<name>/YYYY-MM-DD-topic.md` (today's date from `date`).
   Frontmatter: `type` / `status` / `date` / `tags` (+ `up:` linking the workstream folder-note). In the vault's
   terse, factual voice, capture:
   - what you did + the outcome (PR/commit numbers, branch names),
   - **a dedicated, scannable `## Risks, gates & landmines` block** — the thing an evaluation/review most needs
     and that prose most often buries. Don't scatter risks inline; collect them here, one item per line in a
     consistent shape — **`[TYPE] statement — trigger → consequence → mitigation/status`** — tagged by TYPE so
     severity is obvious at a glance, GATEs first:
     - **GATE** — a blocking precondition/ordering (must-happen-before / must-not-do); the outage-class risk
       (e.g. a deploy-order dependency, a STOP-gated dep/module change). These are what an evaluator must catch.
     - **LANDMINE** — a trap that breaks silently or burns time if you don't know it, but has a known avoidance.
     - **OPEN Q** — an unresolved unknown/decision that could bite.
     - **DEAD END** — a ruled-out approach + the reason (so nobody re-treads it).
     Write every item even if it feels minor; each one single-sourced here, not restated across the doc.
   - what's next / open questions,
   - **reusable commands or scripts** you built or worked out — the exact `rg`/`git`/build incantation, a
     probe/analyzer script, a useful tool-call sequence — so the next agent re-runs instead of re-deriving.
     Inline a short recipe copy-pasteably; persist a real script to `{{VAULT_PATH}}/tools/` (runnable by
     any agent) and `[[link]]` it.
   - `[[wikilinks]]` to related vault docs; leave code-repo paths as literal text.
3. **Update the live frontier — with explicit, evidence-bearing done-markers.** In the workstream's
   folder-note, which *is* its plan of record, record progress as **discrete line items the librarian can act on without guessing** — each
   with a state and its *evidence*:
   - `✅ done — merged #NNNN` / `commit <sha>` / `gate green` — a real landing, **NOT** "PR opened",
   - `⏳ in-flight — #MMMM (draft)` / `mid-rebase` / `blocked on …`,
   - `▢ not started — designed only`.
   Be precise about **done vs in-flight**: a draft or open PR is *not* done. The librarian archives, closes, and
   compacts **strictly off these markers** — if you leave done-ness implicit in prose, it gets inferred, and
   sometimes wrongly (it'll archive something that never merged). Keep the top "where are we / what's next"
   accurate; do **not** restructure, merge, or delete sections.
4. **Second pass — what didn't make it in?** Before you commit, interrogate the entry: *what did I NOT write
   down that the next agent (or a cold-start you, weeks later) would need?* Sweep specifically for:
   - **Implicit decisions** — choices made without recording the *why*; the "obvious to me right now"
     assumptions that won't survive the month.
   - **Dead ends already ruled out** — approaches you tried or rejected, *with the reason*, so nobody
     re-explores them.
   - **Gotchas / landmines** — "don't-do-X", non-obvious ordering, environment traps.
   - **Concrete current state** — branch name(s), committed vs WIP, which PR (#), what's green/red, anything
     mid-rebase or mid-flight.
   Fold the answers back in — route any newly-surfaced GATE / LANDMINE / OPEN-Q / DEAD-END into the
   `## Risks, gates & landmines` block in the typed shape above, not into loose prose. This is the write-time
   version of the adversarial review — far cheaper than re-deriving the loss later.
5. **Commit in the vault** (its own repo): `cd {{VAULT_PATH}} && git add <your specific files> && git
   commit`. Stage specific files — never `git add -A`. Don't push unless asked.
6. **Sync the pointer** if you created a doc future sessions must discover: add its one-line entry to the
   project memory index (`~/.claude/projects/<project>/memory/MEMORY.md`).

## Don't (these are librarian-only)

- Don't delete, merge, or restructure existing docs.
- Don't move anything to `done/`, and don't edit `done/` docs.
- Don't edit `sources/` or `external/` — raw inputs and already-delivered artifacts are read-only. Add a new
  source file freely; correct a stale one by appending a dated note.
- Don't repoint or remove other docs' `[[links]]`.
- Don't write a *competing* frontier — the workstream's folder-note is its one plan of record; append a journal
  entry and update that instead. (Rival "plan" docs from many agents are what create the overlapping-telephone
  mess.)

If consolidation, archiving, or graph cleanup is overdue, **say so and recommend a librarian pass** — don't do
it from here.

## Conventions (quick reference; full rules in the vault CLAUDE.md)

Terse and factual, written for a first-time reader. **No agent-local codenames** ("Option C", "Track B",
"Phase 2", workflow IDs) — say what a thing *is*. Filenames `YYYY-MM-DD-topic.md`. `[[wikilinks]]` for
intra-vault refs; literal text for code-repo paths. If you rename/move a note, use the `obsidian-cli` skill (it
keeps inbound links intact) — but renames are usually librarian work anyway.
