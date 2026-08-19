---
name: context-dump
description: Append-only capture of working context, findings, and handoffs into the LLM knowledge base at {{VAULT_PATH}} — the durable cross-session memory for engineering work (a separate git repo / Obsidian vault spanning every project I work on; usually reachable as a {{VAULT}}/ symlink in the current project root). Use at the end of a work session, before a handoff, or whenever you've learned something worth persisting for the next session — to write a dated journal/handoff entry carrying evidence-bearing markers, then dispatch the `frontier-clerk` to reconcile the live "where are we / what's next" frontier against it. This skill only ADDS: it does not touch the frontier itself, and it never deletes, merges, restructures, archives, or re-links docs (the frontier is the `frontier-clerk`'s; that destructive cleanup is the separate "librarian" pass). Invoke when asked to "dump context", "write a handoff", "save findings to the vault", "checkpoint the workstream", or before ending a long session.
---

# context-dump — append-only capture into the LLM knowledge base

Persist what you did and learned into `{{VAULT_PATH}}` — the durable cross-session memory for engineering work —
so the next session can pick up where you left off.

**This skill is append-only, and that includes the frontier.** You ADD a dated entry. You do NOT edit the
frontier — the `frontier-clerk` you spawn at the end does that — and you do NOT consolidate, merge, delete,
archive or re-link, which are the **librarian's**, run as a separate deliberate pass. Concentrating all
destruction in the librarian is what prevents parallel agents silently clobbering each other's notes.

**Why the frontier is the clerk's and not yours.** Writing a narrative entry *and* paraphrasing it into the
frontier means duplicating what you are forbidden to consolidate, and that is one step from merging and tidying.
It is also not your judgement to make: you have just spent a long session forming views, so everything feels
salient to you. A clerk seeing only your entry and the frontier judges salience as a future reader will.

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
3. **State progress as explicit, evidence-bearing markers — in your entry, not in the frontier.** Record it as
   **discrete line items a clerk can act on without guessing**, each with a state and its *evidence*:
   - `✅ done — merged #NNNN` / `commit <sha>` / `gate green` — a real landing, **NOT** "PR opened",
   - `⏳ in-flight — #MMMM (draft)` / `mid-rebase` / `blocked on …`,
   - `▢ not started — designed only`.
   Be precise about **done vs in-flight**: a draft or open PR is *not* done. Everything downstream acts
   **strictly off these markers** — leave done-ness implicit in prose and it gets inferred, sometimes wrongly,
   archiving something that never merged. Your contract is to emit them; moving them is the clerk's.

   Name the workstream whose frontier is affected, and anything your entry **falsifies** — a line the frontier
   still asserts that your work has made untrue. That is the clerk's input.

   **Emit every marker the clerk will need, including for decisions the owner took in conversation.** The clerk
   may act only on markers in your entry, so an owner decision you were told but did not write down leaves the
   frontier stale and costs a second round trip — measured: two of three clerk invocations in one session existed
   only because a marker was missing. Write the decision, dated and attributed, as its own `✅ settled` line.

   **One marker per separately-statused fact. Never a composite.** A marker covering several facts that do not
   share a state is the single largest measured cause of a clerk overreaching: one entry's
   *"✅ all four inherited defects hold"* covered four separately-statused facts, and the clerk collapsed two
   distinctions off it — while the same clerk, on the same workstream a day earlier, **preserved** the identical
   distinction when the marker was per-item. Same role, same context, opposite outcome; the marker was the
   variable. So if you are tempted to write "all of X is done", write one line per member of X.

   **Distinguish *settled* from *settled-and-executed*, and say which.** A decision the owner made is not work
   that happened. `✅ settled … execution deferred` and `✅ done` licence completely different actions, and
   collapsing them is how a deferred plan gets carried out.
4. **Spawn the `frontier-clerk`, and do not report success until it returns.** Hand it the entry you just
   wrote and the workstream's folder-note. It flips the `status`, strikes next-moves your markers show
   completed, demotes superseded in-flight lines, and files landed items — the frontier work you may not do.
   **Its return is part of your report.** Skip it, or report done while it failed, and you leave a stale
   frontier behind a dump that claimed success — the silent failure this vault exists to prevent.

   Frontier lines are **state plus a pointer, never a paraphrase** —
   `- ⏳ in-flight — retention sweep, #4730 (draft). Detail: [[2026-01-02-retention-sweep]].` A line that explains
   rather than states is a paraphrase and belongs in your entry. Don't hand the clerk one.

   **A mutable measurement is not state, so never hand the clerk one to transcribe.** A commit count, a
   review-comment tally, a queue depth: cite the reference and let a tool answer the number. Measured — the one
   restated figure of this kind in one vault was simultaneously wrong in two documents and went stale three times
   in two days, while nothing that carried only a pointer did.

5. **Second pass — what didn't make it in?** Before you commit, interrogate the entry: *what did I NOT write
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
6. **Commit in the vault** (its own repo): `cd {{VAULT_PATH}} && git add <your specific files> && git
   commit`. Stage specific files — never `git add -A`. Don't push unless asked.
7. **Sync the pointer** if you created a doc future sessions must discover: add its one-line entry to the
   project memory index (`~/.claude/projects/<project>/memory/MEMORY.md`).

## Don't (these belong to the clerk or the librarian)

- **Don't edit the frontier yourself** — no `status` flip, no striking a next-move, no demoting a superseded
  line, not even one you just finished. Emit the marker; the clerk moves it.
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
