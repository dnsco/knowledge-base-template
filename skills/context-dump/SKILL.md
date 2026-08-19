---
name: context-dump
description: Append-only capture of working context, findings, and handoffs into the LLM knowledge base at {{VAULT_PATH}} — the durable cross-session memory for engineering work (a separate git repo / Obsidian vault spanning every project I work on; usually reachable as a {{VAULT}}/ symlink in the current project root). Use at the end of a work session, before a handoff, or whenever you've learned something worth persisting for the next session — to write a dated dump carrying evidence-bearing markers into the live task, then dispatch the `frontier-clerk` to reconcile the task's frontier against it when the dump actually changes frontier state. This skill only ADDS: it does not touch the frontier itself, and it never deletes, merges, restructures, archives, or re-links docs (the frontier is the `frontier-clerk`'s; that destructive cleanup is the separate "librarian" pass). Invoke when asked to "dump context", "write a handoff", "save findings to the vault", "checkpoint the workstream", or before ending a long session.
---

# context-dump — append-only capture into the LLM knowledge base

Persist what you did and learned into `{{VAULT_PATH}}` — the durable cross-session memory for engineering work —
so the next session can pick up where you left off.

**This skill is append-only, and that includes the frontier.** You ADD a dated **dump** — the vault's word for
a dated document written during a task. You do NOT edit the frontier — the `frontier-clerk` does that, when one
is owed — and you do NOT consolidate, merge, delete, archive or re-link, which are the **librarian's**, run as a
separate deliberate pass. Concentrating all destruction in the librarian is what prevents parallel agents
silently clobbering each other's notes.

**Why the frontier is the clerk's and not yours.** Writing a narrative dump *and* paraphrasing it into the
frontier means duplicating what you are forbidden to consolidate, and that is one step from merging and tidying.
It is also not your judgement to make: you have just spent a long session forming views, so everything feels
salient to you. A clerk seeing only your dump and the frontier judges salience as a future reader will.

The vault is its **own git repo** (separate from whatever repo you're working in) and an Obsidian graph. **One
vault covers every project** — it is usually symlinked into the current project root as `{{VAULT}}/`, so you can
read and grep it as in-tree paths. Full conventions: `{{VAULT_PATH}}/CLAUDE.md`. The shape your dump has to fit:

```
workstreams/<ws>/
  <ws>.md                      the parent — task index, a thin restated subset, cross-task invariants
  YYYY-MM-DD-<task>/           a live task: the unit of work that closes
    <task>.md                  its frontier — its own gates and PR numbers while live. Not dated
    YYYY-MM-DD-<topic>.md      dumps written during it  <- YOUR DUMP GOES HERE
  historical/                  LIVE, not done — unsorted pre-conversion context
  done/YYYY-MM-DD-<task>/      closed tasks
```

**A workstream not yet converted has no task folders.** Do not convert it as a side effect of dumping: write into
the workstream root as before, and say in your report that it wants a task folder next time it is opened. Lazy
conversion is deliberate — the mechanism that converts a workstream is the one that operates it, and that is a
`librarian` pass, not this skill.

## Do

1. **Read the conventions, then guess the destination and ask.** If you have not already read
   `{{VAULT_PATH}}/CLAUDE.md` this session, read it now — a session rooted in a code project does **not** load it
   automatically, so assume you haven't. Then skim `{{VAULT_PATH}}/README.md` (the map) + the relevant
   `workstreams/<name>/<name>.md` folder-note.

   **Name your guess and ask the owner to confirm or redirect. Never infer it silently, and never interrogate.**
   The guess is the **most recently edited task in the most recently edited workstream**, which is usually right:

   ```bash
   cd {{VAULT_PATH}} && git log -12 --name-only --pretty=format:'%h %ad %s' --date=short -- workstreams/
   python3 {{VAULT_PATH}}/tools/pass_log.py active --scope workstreams/<ws>   # is anyone else in here?
   ```

   Ask in one breath, not as an interview: *"Dumping into `workstreams/x/2026-08-19-y/` — right place? And is
   that task done?"* Both questions matter here and nowhere else. The destination is how work belonging to **no**
   task — a debugging session, a spike — stops being appended wherever the session happened to be rooted. The
   closure question is asked because **nobody else's job is asking**: a marker only exists if someone raised the
   question, and a dump is the moment. You ask; the owner answers; the clerk acts on the marker.

   **If `pass_log.py active` shows an open pass on this workstream, say so before you write.** Another agent is
   editing these files right now — a `librarian` mid-restructure is the case that loses work. A STALE record (no
   stop record, older than a few hours) is an agent that died, not one still working; say which you saw.

   If the work is genuinely new, you may create `workstreams/<name>/` + a `<name>.md` folder-note. **Opening a
   new task also means pulling forward what bears on it** — the still-live GATEs, LANDMINEs and DEAD ENDs from
   the workstream's closed tasks and `historical/` — into a `## Carried across` section of the task's frontier,
   each cited by source. Dispatch a `scout` with the `orientation` brief to find them rather than reading `done/`
   yourself, then:

   ```bash
   python3 {{VAULT_PATH}}/tools/orientation_check.py workstreams/<ws>/YYYY-MM-DD-<task>/
   ```

   Exit 2 means the pull did not happen, and a warning that does not fire is indistinguishable from one nobody
   recorded.

   **Then announce yourself in the shared pass log, before you write anything.**

   ```bash
   python3 {{VAULT_PATH}}/tools/pass_log.py start --role context-dump --scope workstreams/<ws> --kind dump
   ```

   Keep the id it prints; you close it in step 7. One log covers the whole vault so that every role can see what
   the others are doing — a `start` with no matching `stop` is how the next agent learns someone is in here now.
   Exit 1 means a concurrent pass overlaps your scope: read it and judge before writing.
2. **Write the dump** — `workstreams/<ws>/YYYY-MM-DD-<task>/YYYY-MM-DD-topic.md` (today's date from `date`),
   or `workstreams/<ws>/YYYY-MM-DD-topic.md` in a workstream with no task folders yet.
   Frontmatter: `type` / `status` / `date` / `tags` (+ `up:` linking the task frontier, or the folder-note where
   there is no task). In the vault's
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
3. **State progress as explicit, evidence-bearing markers — in your dump, not in the frontier.** Record it as
   **discrete line items a clerk can act on without guessing**, each with a state and its *evidence*:
   - `✅ done — merged #NNNN` / `commit <sha>` / `gate green` — a real landing, **NOT** "PR opened",
   - `⏳ in-flight — #MMMM (draft)` / `mid-rebase` / `blocked on …`,
   - `▢ not started — designed only`.
   Be precise about **done vs in-flight**: a draft or open PR is *not* done. Everything downstream acts
   **strictly off these markers** — leave done-ness implicit in prose and it gets inferred, sometimes wrongly,
   archiving something that never merged. Your contract is to emit them; moving them is the clerk's.

   Name the task whose frontier is affected (and the workstream, if a marker is genuinely cross-task), and
   anything your dump **falsifies** — a line the frontier still asserts that your work has made untrue. That is
   the clerk's input, and in step 4 it is also how you decide whether a clerk pass is owed at all.

   **Emit every marker the clerk will need, including for decisions the owner took in conversation.** The clerk
   may act only on markers in your dump, so an owner decision you were told but did not write down leaves the
   frontier stale and costs a second round trip — measured: two of three clerk invocations in one session existed
   only because a marker was missing. Write the decision, dated and attributed, as its own `✅ settled` line.

   **One marker per separately-statused fact. Never a composite.** A marker covering several facts that do not
   share a state is the single largest measured cause of a clerk overreaching: one dump's
   *"✅ all four inherited defects hold"* covered four separately-statused facts, and the clerk collapsed two
   distinctions off it — while the same clerk, on the same workstream a day earlier, **preserved** the identical
   distinction when the marker was per-item. Same role, same context, opposite outcome; the marker was the
   variable. So if you are tempted to write "all of X is done", write one line per member of X.

   **Distinguish *settled* from *settled-and-executed*, and say which.** A decision the owner made is not work
   that happened. `✅ settled … execution deferred` and `✅ done` licence completely different actions, and
   collapsing them is how a deferred plan gets carried out.
4. **Decide whether a clerk pass is owed. If it is, spawn it and wait. If it is not, say so and name the check.**

   **The clerk no longer runs on every dump** (owner decision, 2026-08-19, Dennis). It is a multi-minute agent
   and it was sitting in front of the system's most frequent action, unconditionally. It runs when a dump
   actually changes frontier state.

   A pass is owed when **either** holds:
   - your dump carries a marker that moves the frontier — a `✅ done`, a `✅ settled` owner decision, a completed
     next-move, a `status` that should flip, or a line the frontier asserts that your work **falsifies**;
   - the frontier has already fallen behind its own dumps:
     ```bash
     python3 {{VAULT_PATH}}/tools/frontier_lag_check.py workstreams/<ws>    # exit 1 = signals, read them
     ```

   It is **not** owed when the dump is purely additive — findings, a recipe, a measurement, a question raised and
   left open — and nothing the frontier currently asserts became untrue. Then write in your report: *no clerk
   pass owed*, with the lag-check exit code and the reason. **Naming the check is the point:** "I judged it
   unnecessary" and "the check said clean" are different claims, and only one of them is verifiable later.

   When it **is** owed: hand the clerk your dump, the **task** frontier (the parent only if a marker is genuinely
   cross-task), and the lag-check output so it does not re-derive what you already have. It flips the `status`,
   strikes next-moves your markers show completed, demotes superseded in-flight lines, and files landed items —
   the frontier work you may not do. **Do not report success until it returns.** Gating *which* dumps pay for a
   clerk is the fix; skipping the wait on one that owes it is not, because a dump that reports done over a stale
   frontier is the silent failure this split exists to prevent.

   Frontier lines are **state plus a pointer, never a paraphrase** —
   `- ⏳ in-flight — retention sweep, #4730 (draft). Detail: [[2026-01-02-retention-sweep]].` A line that explains
   rather than states is a paraphrase and belongs in your dump. Don't hand the clerk one.

   **A mutable measurement is not state, so never hand the clerk one to transcribe.** A commit count, a
   review-comment tally, a queue depth: cite the reference and let a tool answer the number. Measured — the one
   restated figure of this kind in one vault was simultaneously wrong in two documents and went stale three times
   in two days, while nothing that carried only a pointer did.

5. **Second pass — what didn't make it in?** Before you commit, interrogate the dump: *what did I NOT write
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
6. **Commit in the vault** (its own repo): `cd {{VAULT_PATH}} && git add <your specific files> && git commit -m
   "…" -- <your specific paths>`. Stage and commit **specific paths** — never `git add -A` and never a bare
   `commit`, because other sessions write here and a bare commit takes their staged work with yours. Don't push
   unless asked.
7. **Close the pass, and sync the pointer.**

   ```bash
   python3 {{VAULT_PATH}}/tools/pass_log.py stop --id <the id from step 1> --result incremental
   ```

   A dump is incremental by definition — it never consolidates anything, and the tool refuses if you claim it
   did. Use `--result aborted` if you did not end up writing. An open `start` you never close reads to the next
   agent as an agent still working in here, which is how a stale record becomes a reason someone else backed off
   for no reason.

   Then, if you created a doc future sessions must discover, add its one-line pointer to the project memory index
   (`~/.claude/projects/<project>/memory/MEMORY.md`).

## Don't (these belong to the clerk or the librarian)

- **Don't edit the frontier yourself** — no `status` flip, no striking a next-move, no demoting a superseded
  line, not even one you just finished. Emit the marker; the clerk moves it, when one is owed. A clerk pass you
  judged unnecessary is not a licence to make its edits yourself.
- **Don't convert a workstream to task folders** as a side effect of dumping, and don't move existing docs into
  one. Conversion is a `librarian`'s.
- Don't delete, merge, or restructure existing docs.
- Don't move anything to `done/`, and don't edit `done/` docs.
- Don't edit `sources/` or `external/` — raw inputs and already-delivered artifacts are read-only. Add a new
  source file freely; correct a stale one by appending a dated note.
- Don't repoint or remove other docs' `[[links]]`.
- Don't write a *competing* frontier — a live task's `<task>.md` is the plan of record for that task, and the
  parent folder-note is the plan of record for the workstream. Append a dump and let the clerk update the
  frontier. (Rival "plan" docs from many agents are what create the overlapping-telephone mess.)

If consolidation, archiving, or graph cleanup is overdue, **say so and recommend a librarian pass** — don't do
it from here.

## Conventions (quick reference; full rules in the vault CLAUDE.md)

Terse and factual, written for a first-time reader. **No agent-local codenames** ("Option C", "Track B",
"Phase 2", workflow IDs) — say what a thing *is*. Filenames `YYYY-MM-DD-topic.md`. `[[wikilinks]]` for
intra-vault refs; literal text for code-repo paths. If you rename/move a note, use the `obsidian-cli` skill (it
keeps inbound links intact) — but renames are usually librarian work anyway.
