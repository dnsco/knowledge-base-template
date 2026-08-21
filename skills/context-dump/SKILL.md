---
name: context-dump
description: Append-only capture of working context into the knowledge-base vault — the durable cross-session memory for engineering work (a separate git repo / Obsidian vault spanning every project I work on). Use whenever you have learned something worth persisting, and at the end of a session or before a handoff, when it also writes the next orientation document a fresh agent will read. It only ever ADDS documents: a dump is never edited and never retrofitted, and an orientation is superseded by writing a newer one rather than by changing it. Invoke when asked to "dump context", "write a handoff", "save findings to the vault", "checkpoint the workstream", or before ending a long session.
---

# context-dump — write a record, and on the way out write the next orientation

Two modes, and you are usually in the first.

- **A dump**, any time you have learned something worth keeping. One dated document. That is all.
- **A handoff**, when the session is ending. The dump, **plus** a new orientation document for whoever
  picks this up next.

## The rule underneath everything here

**Every document in the vault is a record or a view.**

- **A record is never edited.** Dumps, `reference/` traces, `sources/`, `external/`, and every orientation
  already written. Correct one by writing a newer one — it supersedes, and the old one stays true about the
  moment it describes.
- **A view is regenerated wholesale, never patched.** An orientation is a view written *as* a record: fresh
  each handoff, newest wins. It is safe to rewrite from scratch precisely because the records behind it are
  intact.
- **`architecture/` is the owner's.** You may contradict it with a dated trace. You do not edit it.

So there is nothing here you can damage by adding, and nothing you are allowed to change by hand.

## Shape

```
workstreams/YYYY-MM-DD-<thread>/
  YYYY-MM-DD-<thread>.md       routing note — what this thread is. Dated to match the folder.
  orientation/YYYY-MM-DD-HHMM.md   newest wins. Written at handoff.
  dumps/YYYY-MM-DD-<topic>.md      <- YOUR DUMP GOES HERE
  reference/YYYY-MM-DD-<topic>.md  dated traces from source
```

One workstream is **one thread of work** — one path prefix, one agent at a time. A second concurrent thread
is a **new dated workstream and a link**, not a subfolder. Resolve the vault with `lipika vault-config path`;
no path to it is written here. Full conventions: the vault's `CLAUDE.md`, which a session rooted in a code
project does **not** load automatically — read it if you have not.

**A workstream still in the old task shape** has no `dumps/`. Create `dumps/` and write there; leave every
existing document exactly where it is. Conversion is lazy and it never moves records.

## Do

1. **Find the home, name your choice, let the owner redirect.** Usually the most recently touched workstream.
   A **new dated workstream** when this is a second concurrent thread rather than more of the same one.

   ```bash
   cd "$(lipika vault-config path)" && git log -12 --name-only --pretty=format:'%h %ad %s' --date=short -- workstreams/
   lipika pass-log active --scope workstreams/<ws>     # is anyone else in here?
   ```

   Say it in one breath: *"Dumping into `workstreams/2026-08-21-x/`."* Never interrogate. If an open pass
   overlaps, say so before you write; a STALE record is an agent that died, not one still working.

   ```bash
   lipika pass-log start context-dump "<what you are dumping>" --scope workstreams/<ws> --kind dump
   ```

2. **Write the dump** — `workstreams/<ws>/dumps/YYYY-MM-DD-<topic>.md`, today's date from `date`.
   Frontmatter: `type` / `status` / `date` / `tags` / `up:`. Terse and factual, for a first-time reader.

   - **What you did and what came of it** — PR numbers, commit shas, branch names, what is green and what
     is red.
   - **Answer the questions you inherited.** You opened with an orientation carrying open questions and
     live warnings. Say what happened to each one you touched: resolved (with the evidence), still open,
     or now understood differently. This is what makes the newest document the most useful one, and it is
     the single highest-value thing in a dump.
   - **A scannable `## Live items` block** — collected, not scattered through prose, one per line:

     `[TYPE] statement — trigger → consequence → dies when <condition> · as-of YYYY-MM-DD`

     - **GATE** — a blocking precondition or ordering. The outage-class risk.
     - **LANDMINE** — breaks silently or burns time, with a known avoidance.
     - **OPEN Q** — unresolved, and agents can work on it.
     - **ESCALATED** — unresolved, and **only the owner can decide it**. Distinct from OPEN Q on purpose:
       this is the list a fresh session opens with, so an item routed here reaches a human and an OPEN Q
       does not.
     - **DEAD END** — ruled out, with the reason. It has no death condition; it fires forever.

     **Every item carries a death condition** — what would make it stop being true. Writing it costs you
     nothing now, with the context in hand, and without it the next agent cannot decide whether the item is
     still live without re-reading everything. An item you cannot write one for is usually two items.

     **`as-of` is when the item was last *confirmed*, not when it was last copied.** Carrying an item
     forward does not refresh its date.
   - **State, with its basis.** Say what landed and how you know: `merged #4131`, `commit a1b2c3d`, `gate
     green`. A draft or an open PR has not landed. Where you are asserting judgement rather than evidence,
     say that instead — *judgement: the remaining work no longer describes this thread*. Both are
     acceptable; an unstated basis is not, because it is the one thing nobody can check later.
   - **Reusable commands** — the exact incantation, so the next agent re-runs instead of re-deriving. A real
     script goes in Lipika's `tools/`, not the vault.
   - `[[wikilinks]]` to vault docs; literal text for code-repo paths, with the repo named.

3. **Second pass — what did not make it in?** Before you commit: what would a cold-start you need in a
   month? Sweep for implicit decisions made without the *why*, dead ends ruled out without the reason,
   environment traps, and concrete current state. Route anything new into `## Live items` in the typed
   shape rather than into loose prose.

4. **If this is a handoff, write the next orientation.** `workstreams/<ws>/orientation/YYYY-MM-DD-HHMM.md`
   — the time is in the name because more than one handoff a day is normal and the newest must sort last.

   Read the previous orientation and your own dumps since it. Then write a **new** document; do not edit
   the old one, and do not diff-and-patch it in your head. Regeneration is the cheap operation here.

   ```markdown
   ---
   type: orientation
   status: current
   date: YYYY-MM-DD
   up: "[[YYYY-MM-DD-<thread>]]"
   ---

   ## Where this is
   Two or three sentences. What this thread is for and what state it is in.

   ## Needs the owner
   Every ESCALATED item. If there are none, say so.

   ## Live items
   Every carried GATE / LANDMINE / DEAD END / OPEN Q, in the typed shape, each with its own `as-of`.

   ## Settled since the last orientation
   One line per item that left the live set, with its disposition and basis:
   resolved — <evidence> · dropped — <reason>

   ## Recent narrative
   The last handful of dumps, newest first, one or two sentences each, linked.
   ```

   **Every item that was live in the previous orientation appears in exactly one of those sections.** An
   item that silently vanishes is the one failure this document has; the next session's `pickup` audits
   for exactly that, so a drop you record honestly costs nothing and a drop you hide gets caught anyway.

   Dropping an item on judgement is fine and expected — say it is judgement and say why. Requiring
   evidence to drop anything is how a live set grows forever.

5. **Commit** in the vault, which is its own repo. Stage **specific paths** — never `git add -A`, never a
   bare `commit`, because other sessions write here.

   ```bash
   cd "$(lipika vault-config path)" && lipika vault-commit -m "…" -- <your paths>
   ```

   **Never change HEAD.** No `git checkout -b`: the checkout is shared, and creating a branch moves HEAD
   for every other session in it. Don't push unless asked.

6. **Close the pass.**

   ```bash
   lipika pass-log stop context-dump "<the dump you wrote>" --result incremental
   ```

   `--result aborted` if you did not write. An unclosed `start` reads to the next agent as someone still
   working in here.

## Don't

- **Don't edit any record** — not a dump, not a previous orientation, not a `reference/` trace, not
  `sources/` or `external/`. Correct one by writing a newer document that says so.
- **Don't edit `architecture/`.** Contradict it in your dump, with the trace behind the contradiction.
- **Don't move documents.** Nothing is archived and nothing needs to be; a dated folder that stops
  accruing dumps has already recorded that it finished.
- **Don't write a second live orientation for one thread.** If the work has become two threads, that is a
  second dated workstream, and say so.

## Voice

Terse and factual, written for a first-time reader who was not in the room. **No agent-local codenames** —
"Option C", "Track B", "Phase 2", workflow IDs — say what a thing *is*. Filenames `YYYY-MM-DD-topic.md`.
**Timestamp every metric**: "9 KB at 2026-08-21", never "9 KB", so the next agent reads it as point-in-time
instead of correcting it. Better still, cite the reference and let a tool answer the number.
