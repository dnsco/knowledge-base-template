---
type: reference
status: reference
date: 2026-08-21
tags: [vault, meta, agents, ontology, design, roles, tools]
---

# The design — what shape this system has, why, and what each role runs

The single design document for the vault and the machinery that maintains it.

**It carries no measurements. It carries parameters.** A **measured figure** is record and lives in
`sources/evals/`, dated and frozen; a **chosen threshold** is a design decision and is revisable here.
Where a claim rests on a measurement, it points.

**Not normative.** `CLAUDE.md` and the skill and agent definitions win on any conflict of wording.

**Markers:** `✅` built and in force · `⏳` partly · `▢` designed, not built · plus
`[GATE]` / `[OPEN Q]` / `[DEAD END]` as elsewhere.

## 1. What this is for, and the choice that constrains everything

The vault is durable cross-session memory for engineering work: a **cohesive corpus** read by agents that
need continuity, deliberately not a stochastic index.

- **What it buys.** Facts arrive **whether or not the agent thought to ask for them** — the only reason a
  recorded dead end ever prevents anything.
- **What it costs.** Curation is slow, and it is work.
- **Why the trade holds.** The corpus's most valuable contents are *negative* results: ruled-out
  approaches, gates, landmines. A negative result's trigger is someone about to re-propose the thing, and
  that person by definition does not know to query for it. Pull retrieval cannot fire on the absence of a
  query. This is the argument for a **push** surface, and it is independent of retrieval technology.

**The first force: work evolves.** A push surface works only while what it pushes is about the work at
hand, and while it is short enough to be read at the moment of proposing. Pieces of work emerge, change
what they are about, and finish. Context must be partitioned as they do, or one surface accumulates
everything the effort ever contained.

**The second force: this is agents writing for agents.** The reader who arbitrates content is an
occasional scanner, checking orientation and correcting mistakes. So: **act, then report for correction**,
not ask then act.

## 2. The goals

Judge every change against these, in order.

1. **An agent is pushed what bears on its work, and little else.** Relevance first, volume second.
2. **A warning fires unprompted or it does not count.**
3. **Nothing that was written down becomes unfindable.**
4. **Any operation somebody waits on finishes inside two minutes.**
5. **Adoption is incremental.** No shape is worth a re-architecture.
6. **Every claim names its enforcement, or admits it has none.**

## 3. Records and views — the rule everything else follows from

**Every document is a record or a view. Nothing is both.**

| | record | view |
|---|---|---|
| dated | yes | yes, except `architecture/` |
| edited | **never** | regenerated wholesale, never patched |
| corrected by | writing a newer document | regenerating |
| examples | dumps, `reference/` traces, `sources/`, `external/`, every orientation already written | the current orientation, the vault index, `architecture/` |

**Why this is the whole design.** The vault previously had a third class — mutable *and* authoritative:
the task frontier and the parent register. That class was the entire maintenance bill. It needed surgical
edits, so it needed a slice tool and line citations; it needed a licence check so an edit could not claim
more than its evidence; it needed a losslessness gate because an edit could drop a fact; it needed a byte
budget because it accumulated; it needed a closure primitive to bound the accumulation; and it needed a
role of its own to do the editing. Seven tools and one role, all serving one class of document.

Removing the class removes all of it. A view needs no losslessness gate because its sources are intact and
a bad regeneration is fixed by regenerating again. It needs no surgical discipline because you rewrite the
file. It cannot go over budget because you regenerate under a target rather than trimming an accumulator.

**The three older append-only tiers keep their own reasons**, which is why they generalise differently:
`sources/` because an edited transcript is no longer a transcript and every document citing it now quotes
something that was never said; `external/` because rewriting a delivered artifact makes the record
disagree with what people received; a dump because it is evidence of a moment.

✅ **`architecture/` is the one long-lived edited view, and only the owner writes it.** An agent-authored
portrait fails worse than a stale one: it becomes the most-linked document in the vault with no dated
evidence positioned to contradict it, and nothing in the system is placed to disagree with it. Agents
produce the dated `reference/` traces behind it and **contradict it with them** — which is an ESCALATED
item, and the loop that keeps it honest.

## 4. The document ontology

```
vault/
  README.md                        VIEW — the index of threads. Regenerated.
  architecture/<system>.md         VIEW — the owner's portrait. Stable name, no date, as-of <sha>.
  reference/YYYY-MM-DD-<topic>.md  RECORD — a trace from source, cross-thread
  workstreams/
    YYYY-MM-DD-<thread>/
      YYYY-MM-DD-<thread>.md       the routing note. Dated to match the folder.
      orientation/YYYY-MM-DD-HHMM.md   VIEW-as-record. Newest wins.
      dumps/YYYY-MM-DD-<topic>.md      RECORD
      reference/YYYY-MM-DD-<topic>.md  RECORD — a trace, thread-local
  sources/  external/  values/  grand-plans/     RECORD
```

✅ **One workstream is one thread of work** — one path prefix, one agent at a time. That makes the pass
log's prefix partition exactly right rather than approximate.

✅ **Heaviness is concurrent threads, not bytes.** Two hundred dumps on one thread cost nothing: orientation
is still one document and dumps are read on demand. Forty dumps across three concurrent efforts is already
too heavy at a fifth the size. **A second concurrent thread is a new dated workstream and a link** — which
is also why there is no task tier, no closure ceremony, no carry-across and no `done/`.

✅ **A thread ends by not being listed as live.** Nothing is archived. A dated folder plus its last dump's
date already encodes the lifecycle, and leaving it in place is what keeps every inbound link true forever.

✅ **Folders and notes carry the date; `architecture/` does not.** The date is *opened*, never *current* —
last-touched stays derivable from git and is never written down. Wikilinks resolve by basename and dating
folders is exactly what invites a repeat topic, so the note carries the date too; otherwise a link to the
second effort on a subject quietly resolves to the first.

▢ **Conversion is lazy and additive.** A workstream in the old task shape gets a `dumps/` directory and is
written into; nothing already there moves. There is no migration project, and records never move.

## 5. The live set, and how an item dies

An orientation carries typed items: **GATE**, **LANDMINE**, **DEAD END**, **OPEN Q**, and **ESCALATED**.

✅ **ESCALATED is a distinct type, not a flavour of OPEN Q.** "Agents can work on this" and "only the owner
can decide this" route differently: escalations are what a fresh session opens with, so an item typed this
way reaches a human and an OPEN Q does not.

✅ **Every item carries a death condition** — what would make it stop being true. It costs the writing agent
nothing, with the context in hand, and without it a later agent cannot judge whether the item is live
without re-reading everything. It moves the cost to the agent best placed to pay it. A DEAD END is exempt:
it fires forever.

✅ **Every item carries its own `as-of`** — when last *confirmed*, not when last copied. An item carried
unchanged through six handoffs inherits the newest document's name and reads as fresh; its own `as-of` is
the only thing that says otherwise.

✅ **Recency is a prior, not a rule.** More recent information generally supersedes older and is trusted
more. The newest orientation can be thin or wrong and an agent may reach back into dumps; what it may not
do is treat an older orientation as a rival account of the present.

✅ **Four dispositions at a handoff: carried, resolved with evidence, dropped with a reason, escalated.**
Every item live in the previous orientation takes exactly one. **Dropping on judgement is expected** —
requiring evidence to drop anything is how a live set grows forever.

✅ **Every disposition states its basis: evidence or judgement.** This replaces *never infer completion; a
marker is the only authority*, which is retired — see §8.

## 6. The two skills, and where the audit lives

| | when | synchronous | does |
|---|---|---|---|
| `pickup` | session start | **yes** | reads the current orientation, audits it, opens with what needs the owner, enters plan mode |
| `context-dump` | learned something | **yes** | one dated dump |
| `context-dump` (handoff) | session end | **yes** | the dump, plus a new dated orientation |

Both are skills rather than agents: they run in the main loop, where the context already is.

✅ **The audit runs at pickup, not at handoff.** The handing-off agent is the least-budgeted and least
independent reader in the system — nearly out of room, and auditing its own work. The fresh one has a full
window and no stake. A bad handoff is caught one session later instead of never, and nothing blocks on the
handoff path.

✅ **`orientation-audit` is the gate.** Every item live in the previous orientation must appear in the
current one as carried, or be recorded as resolved, dropped or escalated. **A silent disappearance is the
one failure this document class has**, and it is the exact price of regenerating rather than editing: an
edited register leaves a diff, a regenerated document leaves nothing. Matching is deliberately fuzzy,
because a carried item is *meant* to be reworded.

✅ **The architecture recommendation is pickup's, not handoff's.** A handoff *infers* a portrait would
help; pickup *feels it* — it is the agent reading cold and discovering the system it must work on is
described nowhere. `architecture-candidates` is the mechanical half of the same signal.

✅ **A pickup ends in plan mode.** Measured 2026-08-21: hooks receive `permission_mode` as a **read-only**
input field and no hook output can change it, so a hook cannot force plan mode — the skill calls
`EnterPlanMode` itself.

## 7. The roles that remain, and the machinery they share

| role | scope | does |
|---|---|---|
| `curator` | the vault | regenerates the index, repairs links that cross threads, owns the shared surfaces |
| `scout` | any | read-only recon in a context that is discarded |

**Why there are only two.** Everything inside one thread belongs to the session working in it. What is
left for a background role is the surfaces no thread can own, and reconnaissance whose cost is worth
paying in a context that gets thrown away.

**The pass log carries concurrency.** `pass-log.jsonl` at the vault root, untracked, one shared file
because the question it answers is *what is another agent doing right now* and N logs do not answer it.
Every role announces itself with `start` before it writes and `stop` when it finishes. The one failure
mode seen so far is an unclosed `start`, and it fails safe.

✅ **Worktree isolation is retired (2026-08-20).** It cost five defects of its own, every one a tool
answering about the wrong tree, against three clobbering incidents that were each a scoped `git add` plus a
**bare** commit — which a worktree does not prevent and a pathspec does. Two things survive it: **a tree at
an unexpected commit reports clean**, so any agent given a base ref checks `HEAD` against it first; and
**nobody changes HEAD in a shared checkout**, because creating a branch moves it for every session in the
tree.

✅ **`recall-check` survives as a machinery-development tool only.** Its subject is now a definition being
rewritten here, not a corpus document — nothing in the vault is edited, so nothing in the vault needs it.
It is **not** the way to check a deliberate deletion: a pass whose purpose is removing rules flags every
one of them, and judging a hundred intended retirements in writing is a large amount of work for no
signal. The deletions are the deliverable; `git diff` is the record.

## 8. What was retired, and why — so it is not re-proposed

These were correct answers to a problem this design removes. They are recorded rather than erased, because
the reasoning that produced them was sound and the next person to hit the same symptom should find the
history rather than rebuild it.

| retired | what it did | why it is gone |
|---|---|---|
| the `frontier-clerk` | reconciled a mutable register against dumps | there is no register |
| the `librarian` | consolidated, merged, archived, closed, converted | records are never consolidated, nothing is archived, nothing closes |
| `frontier_slice` | read a register without its prose | nothing edits a register surgically |
| `marker_licence_check` | caught an edit claiming more than its evidence | replaced by dispositions stating their basis |
| `frontier_lag_check` | had the register fallen behind its dumps | the newest document is the state |
| `budget_check` + the 8/12 KB pairs | bounded an accumulating document | heaviness is thread count; a regenerated view cannot accumulate |
| `orientation_check` | did a new task pull warnings forward | there is no task tier; `orientation-audit` replaces it at a different point |
| `closure_check` | is this task finished, and what must carry | nothing closes; its fuzzy matcher lives on in `orientation-audit` |
| the task tier, `done/`, `historical/`, carry-across | partitioned an accumulating register | splitting a thread replaces all of it |
| *never infer completion; a marker is the only authority* | stopped an agent upgrading an item it had no evidence for | it made closure impossible — every real unit carries a `▢`, so requiring a marker meant nothing ever closed, measured across the vault's entire history. It guarded a mutable register against a second agent acting mechanically at a distance, and neither exists. Replaced by **every disposition states its basis** |
| *one marker per separately-statused fact* | stopped a composite marker collapsing distinctions | a writing rule compensating for downstream mechanical action; with judgement restored it has no consumer |
| the clean-tree halt | protected a losslessness guarantee | the guarantee is gone; what protects a commit is the pathspec |
| the write-authority partition | kept parallel agents off each other's files | the pass log answers concurrency directly |

## 9. Invariants, with what would falsify each

| invariant | why | falsified by |
|---|---|---|
| An agent is pushed what bears on its work | A surface full of another thread's warnings fails as a long one does | Recall flat in the irrelevant fraction |
| Every document is a record or a view | The maintenance bill was entirely the third class | A document that must be both, and stays correct |
| A record is never edited | It is evidence of a moment; a later moment gets a later document | An edited record nobody had to reconcile |
| A view is regenerated, never patched | Patching reintroduces surgical discipline and its whole toolchain | A patched view that stayed true over months |
| Every item live in one orientation is disposed of in the next | Regeneration leaves no diff, so a silent drop is invisible | A drop nobody needed to have recorded |
| A disposition states its basis | Silent inference is the failure; inference itself is not | An unstated basis nobody later needed |
| One thread per workstream | Two threads under one prefix put two agents on one path with an advisory warning between them | Two concurrent threads sharing an orientation without either being pushed the other's warnings |
| Every metric carries the date it was taken | Undated figures invite every later agent to correct them | Agents agreeing on an undated figure across a month |
| The owner writes `architecture/` | An agent-authored portrait is confident, most-linked, and uncontradicted | An agent-written portrait surviving a trace that disagreed with it |
| Prose in a definition does not fire; a tool with an exit code does | Every measured instance of a rule silently not firing was fixed by moving it into a tool | A rule holding across several passes on prose alone |

## 10. Three tool-design rules the set was built on

- **Prefer a tool that refuses to prose that asks.** Measured repeatedly: a scope-screening condition
  shipped unsatisfiable and went unnoticed until used; a mandatory dispatch did not fire across fourteen
  recon commands; a verifier reported "nothing changed" nine times having read no diff. Every one was
  fixed by moving the rule into a tool with an exit code. A definition is also a system prompt paid on
  **every** invocation, so a tool is the cheaper end as well.
- **A check that stays red on correct content gets dismissed.** Give every new check a hand-audited red
  case and a green case. Measured 2026-08-21 while building `orientation-audit`: its first matcher scored
  a deleted item at 43% against a successor that never mentioned it, because it compared each item to the
  *concatenation* of the successor's items and shared scaffolding vouched for everything. Its second
  reported a correctly-recorded resolution as needing judgement, because it demanded a hard identifier in
  a haystack one item long. Both were found by the fixtures, not by reading.
- **A check reports what it did not check, rather than swallowing it.** Skips and empty-filter cases get
  their own exit code or label; an unannounced gap reads as a clean result.

## 11. Standing tensions — open, deliberately

- `[OPEN Q]` **Does the dump carry the live set, or only report?** Carrying it makes the dump chain
  self-reconciling and orientation nearly free to generate, at the cost of state living in two documents.
  Reporting only makes orientation the sole holder, and loses the reconciliation when a session dies
  without a handoff. Currently: the dump reports and raises; the handoff holds the live set.
- `[OPEN Q]` **Does the routing note earn its place beside orientation**, or does the index carry its one
  line?
- `[OPEN Q]` **What is the relevant fraction of a pickup** — of what it loads, how much bore on the work.
  Never measured, and it is the quantity this design claims to move.
- `[OPEN Q]` **How stale is too stale.** `orientation-audit` reports an item at 14 days on no evidence.
- `[OPEN Q]` **Does regenerating from `previous orientation + dumps since` lose things** that regenerating
  from all records would not? The loss is recoverable — the records are intact — but the rate is unknown.
- **[DEAD END] Attacking a parent agent's blocked time.** Ranked the largest problem across three passes
  and was never a cost: no tokens, children working throughout. **Do not re-propose.**
- **[DEAD END] A "turns that thought and called nothing" signal.** The harness emits reasoning in its own
  message, so the count was *every* deliberation — 37 of 37 on one run. **Inventing a defect is worse than
  missing one.**
- **[DEAD END] Loop detectors and scoring over reasoning.** Scaffolded, then dropped: the ask was a gut
  check, not a classifier.
- **[DEAD END] Banning mutable measurements from documents.** The correct fix is dating them.
- **[DEAD END] Renaming a file with a `.locked` suffix while working on it.** Breaks the link graph,
  Obsidian and git paths mid-operation, and a crashed agent leaves it locked forever.
- **[DEAD END] A second status or lock file alongside the pass log.** One store with a derived projection,
  not two things that can disagree.
- **[DEAD END] Importing the pre-log git tags as baselines.** A tag was one global name per scope, so it
  could say neither *when* a pass ran nor that two agents were on the same ground.
- **[DEAD END] Keeping the machinery duplicated into each vault and improving the port tooling.** Three
  tools existed for it and six files still needed hand-porting. There is one copy now.

## 12. How to read and maintain this document

**Living document, and the place to experiment.** Mechanisms marked `▢` are untested and their numbers are
hypotheses: run them, measure, and amend here with a dated amendment.

**Not a frontier.** A `▢` means *the system is not this shape yet*, not *someone should go do this*. A PR
number or a next-move appearing here means it has become a second frontier.

**Voice.** Terse and factual, for a first-time reader. A rule its own owner cannot parse has failed,
however well it encodes a real measurement — rewrite it rather than re-explaining it.

| document | carries |
|---|---|
| `CLAUDE.md` | the normative rules, terse and operative |
| `agent-eval-method.md` | the **procedure** for changing and measuring a role |
| the thread's own dumps | the **record** — what each round found, with figures |
| `sources/evals/` | the **verbatim measurements**, frozen and dated |
| this document | the **design** — the shape, the forces, the falsifiers |

## Amendments

**2026-08-21 — records and views.** The mutable-and-authoritative document class is removed, and with it
seven tools, two roles and the task tier; §8 is the retirement record. Orientation replaces the frontier
and is written fresh at each handoff rather than edited. `pickup` is added as the read-side counterpart to
`context-dump`, and the audit moves to it. `architecture/` is added as a new tier and is the owner's.
ESCALATED is added to the marker vocabulary. Heaviness becomes thread count rather than bytes.

**Earlier, compressed.** The document was reframed on 2026-08-19 around partitioning — *work evolves, so
context must be partitioned as pieces of it emerge and finish* — which is when the sub-unit became a dated
task, byte budgets arrived, and measurements became dated rather than banned. 2026-08-20 recorded the pass
log replacing one-log-per-unit, the machinery moving into its own repo, worktree isolation retiring, and
the closure primitive that let a task close for the first time. Most of that is superseded above; the
reasoning is preserved in §8 rather than deleted.
