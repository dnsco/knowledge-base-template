---
type: reference
status: reference
date: 2026-08-20
tags: [vault, meta, agents, ontology, design, roles, tools]
---

# The design — what shape this system has, why, and what each role runs

The single design document for the vault and the agents that maintain it. It merges what were two
documents: the shape-and-forces argument, and the role-by-role operating detail. Sections 1–5 are the
design; §6–8 are the per-role and per-tool reference; §9–12 are the invariants, the open questions and
how to maintain this.

**It carries no measurements. It carries parameters.** A **measured figure** is record and lives in
`sources/evals/`, dated and frozen; a **chosen threshold** is a design decision and is revisable here.
Where a claim rests on a measurement, it points.

**Not normative.** `CLAUDE.md` and the agent definitions win on any conflict of wording; encoding
anything marked `▢` means authoring in the template first.

**Markers:** `✅` built and in force · `⏳` partly · `▢` designed, not built · plus
`[GATE]` / `[OPEN Q]` / `[DEAD END]` as elsewhere.

## 1. What this is for, and the choice that constrains everything

The vault is durable cross-session memory for engineering work: a **cohesive corpus** read by agents
that need continuity, deliberately not a stochastic index.

- **What it buys.** Facts arrive **whether or not the agent thought to ask for them** — the only reason
  a recorded dead end ever prevents anything.
- **What it costs.** Curation is slow, and it is work.
- **Why the trade holds.** The corpus's most valuable contents are *negative* results: ruled-out
  approaches, gates, landmines. A negative result's trigger is someone about to re-propose the thing,
  and that person by definition does not know to query for it. Pull retrieval cannot fire on the absence
  of a query. This is the argument for a **push** surface, and it is independent of retrieval technology.

### The first force: work evolves

A push surface works only while what it pushes is about the work at hand, and while it is short enough
to be read **at the moment of proposing**. Work does not hold still — pieces emerge, change what they
are about, and finish. **Context must be partitioned as they do**, or one surface accumulates everything
the effort ever contained and whoever opens the current piece is pushed all the previous ones.

Length is the tractable proxy, not the thing itself: a short surface full of another task's warnings
fails the same way a long one does.

### The second force: this is agents writing for agents

The original role machinery partitioned write authority hard — one role that appends, one that touches
the register, one that may destroy — and it was built for a human reader who would arbitrate content.
**That reader is an occasional scanner**, checking orientation and correcting mistakes. Two consequences
run through everything below:

- **Act, then report for correction**, not ask then act. §6.
- **Append is free; editing is what needs a check.** §5.

## 2. The goals

Judge every change against these, in order.

1. **An agent is pushed what bears on its work, and little else.** Relevance first, volume second.
2. **A warning fires unprompted or it does not count.**
3. **Keep every fact. Wording and redundancy are fungible** — things may be reworded and combined so
   long as meaning is preserved. What must not happen is a fact becoming unfindable.
4. **Any operation finishes inside two minutes.** Aspirational, tiered in practice. §3.
5. **Adoption is incremental.** No shape is worth a re-architecture; a workstream converts when it is
   next touched.
6. **Every claim names its enforcement, or admits it has none.**

## 3. Span, and the budgets

**Span** is wall-clock elapsed time from a pass's `start` record to its `stop` record. `pass_log.py`
computes it and writes `span_s`. It is deliberately **not** token cost, and **not** the agent's own
reasoning time — the rest of the wall clock is tool calls, file reads and, for a parent, time spent
blocked while children run. A pass can be cheap in tokens and still take seven minutes. The three
numbers move independently, which is why the budget is stated in one of them.

**Two minutes is the north star for the one SYNCHRONOUS operation** — the dump, which somebody is waiting
on. For the background roles it was a hypothesis, and it is now falsified: **not one pass, of any role, has
ever met it.**

| operation | what it should cost | last measured (2026-08-20) |
|---|---|---|
| `context-dump` — the only synchronous one | 2 min | — |
| `frontier-clerk` | 2 min | 133 s, simulated; no real span on record |
| `librarian` — one scope | beat the baseline below | **533 s** delta · **1,817 s** full on a 59 KB parent |
| `curator` — vault-wide | beat the baseline below | **1,407 s** / 6 scopes · **2,155 s** / 2 scopes |
| eval, profiling, or other developer work | **exempt** — a development task, not one anyone waits on |

✅ **A ceiling nothing has ever met is worse than no ceiling**, because every honest report then reads as a
failure and gets discounted — which is what happened to the 480 s figure, overridden twice in one run by an
agent that had priced the overrun correctly. So the background roles carry **observed baselines to beat**
rather than a target already missed, and the numbers live in `~/.config/lipika/config.json` so there is one
home for them. Re-measure and move them down; do not restate them in a definition.

**And width is not the lever.** Six scopes cost 1,407 s while two cost 2,155 s — one full pass over a 59 KB
parent outweighed a six-scope catch-up. A per-run ceiling cannot express that; a per-scope baseline can.

**What the ceiling implies.**

- **Agents in series are the primary cost.** The most frequent operation is expensive largely because it
  writes and then blocks on a second agent. Collapsing a chain, or making a link async, is worth more
  than trimming either link.
- **It does not mean rationing tools.** Tools should run **fast**, and a required step that is slow is a
  tool bug rather than a reason to drop the rule. More time measurement is good; it comes from logging
  more.
- ▢ **Logging belongs inside the tools that already do the work**, not in a separate agent round trip.
  A `start` and a `stop` issued as their own shell calls are two round trips per pass that the tools
  touching files could record for free.
- **Span is the metric, so the lever is the slowest child** — see §11's `[DEAD END]` on blocked time,
  which this sharpens rather than contradicts.

## 4. The document ontology

A workstream's sub-unit is a **task**: a dated piece of work that owns its own frontier, holds the dumps
written during it, and **closes**. A task is a folder, not a file.

```
workstreams/<ws>/
  <ws>.md                        parent — task index + a thin restated subset + cross-task invariants. No date.
  YYYY-MM-DD-<task>/             a live task
    <task>.md                    its frontier — its own gates and PR numbers while live. Not dated.
    YYYY-MM-DD-<topic>.md        dumps written during it
  historical/                    LIVE, not done — unsorted pre-conversion context
  done/YYYY-MM-DD-<task>/        closed tasks, per workstream. The retrieval surface.
  design/                        stable reference, no live status.

workstreams/done/<ws>/           ▢ a finished workstream, moved whole
```

*Terminology the vault spends:* a **task** is that sub-unit; a line in a register is an **item**; a dated
document written during a task is a **dump**. (Where §3 says "any operation", read *operation* — it is
not this sense of task.)

**A workstream was doing two incompatible jobs.** It was the unit of *work* — long-lived, accumulating,
which is how continuity survives — and simultaneously the unit of *retrieval*, which wants to be small
and about one thing. The accumulating job won. Splitting the two across a parent and its tasks is the
partition §1 requires.

- ▢ **A task owns the detailed what's-next**, its own gates and PR numbers while live.
- ▢ **A task is where a dump lands** — which is what stops one piece of work's notes being pushed at the
  next.
- ▢ **The parent is a task index, a thin restated subset, and cross-task invariants.** **The register
  stays in it** rather than moving to a document agents must be told to open, which is how a warning
  stops firing.
- ✅ **The task folder carries the date; its frontier does not.** The date is what makes closing
  mechanical rather than a judgement call — a task with no date never closes.
- ✅ **One frontier per live task.** Two live copies of mutable state must be hand-synced and diverge:
  tried once and reversed the same day.
- ✅ **`done/` is per-workstream**, and a live document points at what was archived out of it.
- ▢ **A finished workstream moves to `workstreams/done/<ws>/` whole**, and the top-level `done/` stops
  existing. That is a migration, not a rule anyone applies piecemeal.

### `historical/` is live, deliberately

▢ Only an extant workstream gets one, and only for content predating the task ontology. Pre-conversion
context lands there as a **live task**, and a `librarian` splits material out of it into `done/` over
time as it is understood.

**It must not go into `done/` on conversion** — that claims consolidation over material nobody has read,
the same error as recording a skipped scope consolidated. This is also what makes lazy conversion safe
before the orientation check has ever fired: nothing is archived, so nothing goes dark, and the worst
case is material staying unsorted, which is where it already is.

### Budgets, and what breaching one means

✅ **A parent and a task each carry a byte budget asserted by a check** — because "thin" in prose does not
fire and a size in an exit code does. `budget_check.py` exits 1 over target and 2 over the signal, and it
prints the largest sections, so *what to extract* is answerable from the same call.

▢ **Parent 12 KB / 16 KB, task 8 KB / 12 KB — hypotheses**, calibrated against one corpus and separating
its smallest parent from its oversized ones and nothing more. **A threshold that has never fired against a
real corpus should be argued with, not obeyed.**

▢ **Over budget means extract, then split. It never means trim.** Extraction first: material that is
reference rather than a live warning goes to `reference/` or `design/`. Splitting is for a parent that is
two efforts wearing one name, and at workstream level the `librarian` **executes it and reports it** — a
**grand plan** is the owner's. **Trimming the task index or deleting history
is not an option** — a unit held under budget that way has failed the check it appears to pass. **Nor may the
budget restrict what a task pulls forward**: a check that makes an agent carry less context has done harm,
not good.

✅ **Measured, and it moved the tool: a total-bytes budget is unreachable with a resident register.** One
conversion cut a parent's non-register bytes by 18% while the total barely moved, because the pass's own
promotions grew the register. The budget is **non-register bytes**, with the register on a soft mark that
asks a question and never fails.

### Carry-across sideways: closing a task is opening its successor

✅ **When a task opens it pulls forward the warnings that bear on it** — the still-live gates, landmines,
dead ends and settled decisions from the workstream's closed tasks and `historical/` — into a
`## Carried across` section, each cited by source. Selection is paid **once per task**, by whoever knows
what the task is about. `orientation_check.py` requires the section and treats *nothing applied* and
*nobody looked* as different states, by refusing an uncited "nothing to carry".

**Rejected: migrating live context up into the parent on close.** The parent then accumulates
monotonically, reproducing the problem one level up — and correctness makes it worse, because reversing
an overreach means re-*expanding* distinctions a previous pass collapsed, so a register grows while being
deliberately drained.

✅ **So the residue goes SIDEWAYS, into the successor.** That is the third option, and its absence is why
nothing ever closed: a task closes when the work it was opened for has landed and what remains no longer
describes it, and the remains have to live somewhere. Closing one therefore *is* opening the next —

1. open the successor task;
2. carry every unstruck item and every live GATE / LANDMINE / OPEN Q / DEAD END into its
   `## Carried across`, cited by source, reworded freely;
3. extract what is durable but not forward-bearing into a workstream-local `reference/` or `design/`
   document — the option that keeps a successor thin, for knowledge a reader wants *when they go looking*
   rather than fired unprompted;
4. `git mv` the closed folder into `done/YYYY-MM-DD-<task>/`, whole. Basenames do not change, so no
   inbound link breaks;
5. point at it from the parent's task index and from the successor.

**The measurement that forced this.** 2026-08-20: three live tasks in one workstream, every workstream in
the vault `status: active`, four ledger files in `done/` and **zero** closed task folders — nothing had
ever closed since the ontology was written. The cause was not compliance. No role was chartered to close,
because *never infer completion* — correct about **items** — had been read as covering **task closure**,
and every real task carries a `▢`. Those are different questions: *did this land*, which only a marker
answers, and *does the remaining work still describe this task*, which is a partition judgement.

✅ **`closure_check.py` is the gate, in two modes.** `--scan` weighs landed markers across a task's *dumps*
against the residue on its frontier and prints the residue as the manifest a rollover must carry — a
heuristic, and authority to ask only. `<task> --into <successor>` refuses a rollover that leaves residue
with no trace in the successor. **Losslessness is `recall_check.py`'s; cohesion-of-what-is-next is this
one's, and nothing checked it before.** Matching is deliberately fuzzy — a carried item is *meant* to be
reworded, so an identifier localizes and prose corroborates, and only a total absence hard-fails.

### Conversion is lazy, and that is the design

▢ There is no migration project. An extant active workstream gets its last few tasks split out as dated
folders and everything else folded into `historical/`; every other extant workstream gets only a
`historical/`, picked apart when next lit up; a workstream created after this design needs neither.

**Conversion and normal operation are the same mechanism** — being lit up means opening a task, and
opening a task is when warnings get pulled forward. No workstream pays a conversion cost until someone is
already reading it.

✅ **Timestamp every metric.** A figure in a document is point-in-time, and saying so is what stops the
next agent correcting it: write "9 KB at 2026-08-19", never "9 KB". Agents correcting each other about
mutable numbers is the expensive failure, not the number aging. Measured: one commit count was
simultaneously wrong in two documents and went stale three times in two days, while nothing carrying only
a pointer did.

## 5. Append is free; editing is what needs a check

**Append needs no check.** Adding a dump, appending to `done/`, appending a dated note to `sources/` or
`external/`. Nothing can be lost by adding.

**Editing a live document needs a check, and the bar is semantic.** Every single-source **fact** must
remain findable; wording may change and redundant facts may be merged. `recall_check.py` is the gate and
every flag is judged **in writing** — a reworded flag is an acceptable answer, a missing fact is not.

This is a narrowing of an earlier absolute rule, not a repeal of it. That rule caught real losses —
four drops in one rewrite, and the same sentence dropped in two separate rewrites — so the check stays
mandatory; only the verdict language moved.

`[OPEN Q]` **Making the check cheap is the open engineering problem.** It is judgement-heavy and run by
hand today, which is exactly what §3's budget punishes. A sidecar vector store, or a tagging and indexing
scheme, is the intended direction and is deliberately out of scope for now. The current cost is the
baseline the premise gets checked against later.

### Three tiers are append-only, for three different reasons

Stating them separately matters, because they generalise differently.

- **`sources/`** — raw verbatim inputs. An edited transcript is no longer a transcript, and every
  document citing it now quotes something that was never said.
- **`external/`** — artifacts already delivered to an audience. Rewriting one makes the record disagree
  with what people actually received.
- **`done/`** — **because a future `librarian` should not have to read it.** This is a *read-cost* reason,
  not a fidelity one: **the corpus is not a normalized store of information**, and repetition in `done/`
  is acceptable in the interest of speed. Deduplication targets **live** documents, where the redundancy
  is actually being read.

A stale claim in any of the three gets an **appended dated note**, never an edit.

**Context dumps are append-only.** A dump is never edited and never retrofitted.

## 6. The roles

Five definitions became four. **The original organising principle was *who may write what*:**
concentrating destructive operations in one role is what let append-only agents run in parallel without
clobbering each other, and every other role's restraint depended on that one existing. **The pass log now
answers concurrency directly** (§7), which is what the write partition was standing in for — so the
principle is now **who loads what, how long it takes, and how far it reaches.**

**Reach is what separates the `librarian` from the `curator`, and it is a cost decision.** Measured
2026-08-20: folding the vault-wide orchestration into the `librarian` took its definition from 35,309 B to
43,888 B, so every **scoped** pass — the common case — paid 13,767 B of fan-out prose it never used: **+23%**
on a scoped pass and **+35%** on a three-scope run. Splitting the reach out into a `curator` beats both that
state and the state before the fold, because the fold's real win was deleting duplicated *rules*, which is
separable from merging the roles: both read `CLAUDE.md` first, so neither definition has to restate them.

| role | scope | synchronous? | does |
|---|---|---|---|
| `context-dump` (skill) | the live task | **yes** — the only one | appends one dated dump |
| `frontier-clerk` | one frontier | no — background | reconciles a frontier against the dumps |
| `librarian` | one task, workstream or grand plan | no — background | inside its scope: consolidate, reword, merge, split the workstream, split and merge tasks, archive, sort `historical/`, convert |
| `curator` | the vault | no — background | which scopes exist, and everything crossing a boundary: fan out one `librarian` per scope, merge, repoint, normalize conventions, own the shared surfaces |
| `scout` | any | on demand | read-only recon in a discarded context |

**Only the dump is synchronous.** It is an event: you know it happened, and it does not return until it
has. Everything else runs in the background and should be mostly invisible — visible enough to keep cost
controllable, and no more.

**Why the dump does not edit its own frontier: time management.** A dumping agent that also tidies the
vault gets sidetracked onto vault corrections, eating the working task's context and time. Keeping
housekeeping off the working session's clock is the whole reason for the separation — it is not a claim
that the dumping agent's judgement is worse.

### Act, then report for correction

Structural changes — splits, merges, moves, rewordings — are made on the agent's best judgement and
**reported for correction**, rather than proposed and held for approval.

The previous pattern was *detect, propose, execute on approval*, and ⏳ **it never fired.** No split
proposal came back from any pass. The diagnosis was that nobody's job was asking, so the asking was
reassigned to a role built for it — and it did not fire there either: that role returned "no questions"
while its own text held six, because *do not decide the taxonomy* collapsed into *do not raise it*. Two
attempts, zero questions. So the duty is inverted.

**What replaces it is a required change list**: every move, merge, reword and split, one line each — what
changed, why, and how to reverse it. The pass log already records files changed, commits and span from
git, so the report carries judgement and the log carries facts.

### The one rule every role shares

**Never infer completion. A marker is an agent's only authority to act.** The characteristic failure here
is not fabrication — it is **distinction-collapse, always toward upgrade**: *failed* read as *never
requested*, *encoded* as *discharged*, *settled* as *settled-and-executed*, a parent marked done because
most of its children were.

Two corollaries that decide arguments:

- **One marker per separately-statused fact.** A composite marker covering four facts is the single
  largest measured cause of a register edit overreaching. If tempted to write "all of X is done", write
  one line per member of X.
- **Settled is not executed.** A decision made is not work done, and the two licence entirely different
  actions.

**This survives §5's loosening untouched.** Rewording is free; *completion* is not a wording question.
Goal 3 governs prose, this rule governs state.

---

### `context-dump` — the skill that appends

A skill, not an agent: it runs in the main loop, so its reads are the session's and it has no transcript.
⏳ **The only role never profiled**, for that reason.

**What it does.** Writes one dated dump into the live task: what happened, the evidence-bearing markers,
a typed risks-gates-landmines block, and the reusable commands.

**Governing rules.**

- **Append only.** It may not touch a frontier — not a `status` flip, not striking a next-move it just
  finished.
- ✅ **Find the best home for the dump.** Most likely the most recent task in the most recent workstream;
  a **new task** when the work is appreciably different; sometimes a **new workstream**. Name the choice
  and let the owner redirect. Never infer silently, never interrogate.
- **Ask the closure question** — is that task done? A marker only exists if someone raised the question,
  and a dump is the moment.
- **Emit a marker for every owner decision**, dated and attributed, including ones taken in conversation.
  An unwritten decision leaves the frontier stale and costs a second round trip.
- **A frontier line is state plus a pointer, not a summary.** It says *what state something is in* and
  *where to read about it* — `⏳ in-flight — retention sweep, #4730 (draft). Detail: [[…]]`. A summary
  duplicates the dump and then drifts from it, which is why one does not belong on a frontier at all.
- **Reconciliation is gated on a check, not a count.** It is owed when the dump carries a marker that
  moves the frontier, or when `frontier_lag_check.py` reports the frontier already lags. A purely
  additive dump reports *no pass owed* **and names the check it ran**: "the check said clean" is
  verifiable later, "I judged it unnecessary" is not.
- ▢ **Reconciliation is dispatched, not waited on.** The dump returns; the clerk runs in the background
  and reports when it lands. `[OPEN Q]` A count-based trigger — *has this task accumulated enough dumps
  to be worth a pass* — remains undecided, and **it is a different mechanism from the gate**, which asks
  *did this change frontier state*. Shipping both without deciding which governs leaves two triggers that
  can disagree.
- ✅ **Announce the pass and close it.** A dump never consolidates anything, and the tool refuses the
  claim.

| tool | contract |
|---|---|
| `frontier_lag_check.py <ws>` | has the plan-of-record fallen behind its own dumps? **exit 0** no signals · **exit 1** signals, read them · **exit 5** bad invocation. This is the gate |
| `orientation_check.py <task>` | does a new task cite what it reviewed? **exit 0** cited · **exit 1** cited but a `done/` or `historical/` goes unmentioned — judge it · **exit 2** no section or nothing cited: the pull did not happen |
| `pass_log.py start\|stop` | announce and close. `start` **exit 1** = a concurrent pass overlaps this scope |

### `frontier-clerk` — the register keeper

The cheap middle tier: more than a dumper, less than a `librarian`. It **must** be cheap in both tokens
and time (§3), and it runs in the background.

**What it does.** Reconciles a frontier against the dumps written under it — **the task's frontier by
default**, the parent only when a marker is genuinely cross-task. It flips a `status`, strikes a
next-move whose completion is recorded, demotes an in-flight line a landed one supersedes, reorders within
a list, and drains a closed item into the workstream's dated `done/` ledger.

**Governing rules.**

- **Acts strictly off markers.** It never infers completion and never decides that something is done.
- ✅ **Default is task-local.** Promoting a task-local fact to the parent is the upgrade-direction
  collapse this system reliably fails at.
- **Do not mark an item done while a sub-item under it is still open.** An item stays at its weakest live
  part, however much of it landed. The test is mechanical rather than a judgement: **read the line back,
  and if it still contains a weaker marker, it has overreached.** Measured — one edit produced a line
  reading `✅ done … ▢ not started` in a single breath.
- **When a flip is genuinely close, the weaker marker is the one the record supports.** Nothing is lost by
  a frontier that lags one dump; a frontier that overclaims sends the next session to build on something
  that never happened.
- **A removal must be lossless.** Strike a completed item only because its landed evidence exists — in
  the document, the dump, or `done/`.
- **May create and append to `done/`; may never rewrite existing text there.** The frozen-tier rule is
  about altering what is already written, and create-and-append does not.
- ✅ **Slice, and cite the line number for every changed line.** `frontier_slice.py`. Measured: with the
  citation required, about 22% of a frontier read; without it, about 92% — naming the tool did not make an
  agent reach for it, requiring its output did. **This is the clerk's rule specifically**, because its
  edits are surgical. See the `librarian` for why it does not generalise.
- **Never merges, moves or splits documents, never rewrites prose for quality, never records a pass
  `consolidated`.**

| tool | contract |
|---|---|
| `frontier_slice.py <note>` | the mutable part of a plan-of-record without the prose. `--section` for one block; `--find PATTERN --context N` instead of paging; `--lines A,B` repeatable and `--numbered` for a restructure; `--stats` before any whole read. Reads **both** marker spellings |
| `marker_licence_check.py <dump> <note> --vault <p>` | did the edit claim more than the dump licenses? **exit 1** unlicensed-upgrade reports to read and judge · **exit 2** a self-contradiction or a rollup over a live child — defects, not judgement calls |
| `verify_pr_markers.py '<owner/repo#N>' …` | state, merge time and merge commit per cited PR in one request. Refuses a bare number rather than guess. **A bare `#N` is a shell comment** — quote refs, or everything after the first is swallowed |
| `frontier_lag_check.py`, `orientation_check.py`, `pass_log.py` | as above |

### `librarian` — structure, and the only role that destroys

**What it does**, inside **one** scope handed to it — a task, a workstream, or a grand plan:

- **task** — reconcile and tidy one task's frontier and its dumps.
- **workstream** — consolidate overlapping notes, reword, merge redundant facts, split the workstream, split
  and merge tasks, promote finished work to `done/`, repair the link graph, sort `historical/`, convert a
  workstream to the task shape.

▢ **Autonomy inside the scope is bounded by losslessness, not by permission** (owner decision, 2026-08-20). It
does not ask; it keeps every fact and reports a change list. Handing it a taxonomy decision it could make
itself is the duty that failed to fire in two previous homes.

**What it may not do is reach past its prefix.** Which scopes exist, fusing two workstreams that are one
effort, relocating a document to another workstream, a convention applied inconsistently across scopes, and a
claim in another scope's files that its work falsified — all the `curator`'s. So are the shared surfaces.

**Governing rules.**

- **Curate, don't engineer.** Never edit code in any project repo; never *make* an engineering or product
  decision. Absolute, and orthogonal to everything §5 loosens.
- **Never infer completion.** Acts strictly on explicit, evidence-bearing done-markers. A draft or open
  PR is not done. Verify against reality rather than prose — it is cheap.
- **Act, then report the change list.** Above.
- **May reword and merge redundant facts in live documents**, subject to §5. This is a change: it was
  previously forbidden, as the boundary of a role that was not supposed to do it.
- **Never lose a fact.** `git show` every source before consolidating; measured losses come from merging
  without reading what is being merged.
- **Read whole when merging; slice when editing surgically.** The slice mandate does **not** generalise
  from the clerk. Measured: a `--section`-only mandate is **unsatisfiable** for a restructure whose diff
  spans twenty hunks, and the first pass under it read 137% of a note by hand. An unsatisfiable
  requirement teaches an agent to ignore the tool, which is worse than no requirement. The universal rule
  is only **never page a file with `sed`**.
- **Never starts on a dirty tree.** Uncommitted files silently veto the losslessness guarantee — you
  cannot `git show` an original that was never committed — and cannot have their inbound links repointed.
  A dirty tree also makes the pass's own diff unreviewable. Never resolve it by committing or stashing
  someone else's work.
- **Renames go through the Obsidian CLI**, which keeps inbound links intact. A hand-rename with eight
  inbound pointers breaks eight documents.
- **Frozen tiers take an appended dated note, never an edit** — §5, and the three reasons differ.
- **A skipped scope is recorded `skipped`, never `consolidated`.** "Not looked at" must not be spelled the
  same way as "already handled".
- **A delta pass must never scope its *writes* to the delta.** Reading only changed documents leaves a new
  dump un-merged into an untouched frontier while the pass reports success.
- **Never two scopes in parallel in one invocation** — both write the shared map and the memory pointer, so
  parallel passes clobber each other. Sequentially, and the shared files are the `curator`'s.
- ⏳ **Refusing to act is sometimes correct.** One sub-`librarian` declined to promote 25 dead ends — what
  a literal reading of its mandate asked, and the larger half of the material by bytes — citing two of the
  owner's own rulings. A refusal reversed or upheld on rule-reading is the behaviour a simplification pass
  can delete by accident.
- ✅ **It is the mechanism that converts a workstream**, and conversion is lazy (§4).

| tool | contract |
|---|---|
| `recall_check.py <pre-change-ref> <path>` | did a rewrite drop a rule? **exit 0** clean · **exit 1** flagged, judge every one in writing. `--mode all --threshold 0.25` for prose, `--into <survivor>` when content moved. **Never reword a file to satisfy a flag** |
| `budget_check.py <ws>` | **exit 1** over target · **exit 2** over the signal → extract or split, never trim. Prints the largest sections |
| `dangling_links.py <root> [memory-dir]` | which links resolve to nothing. **exit 1** if any dangle; separates the false-positive classes. The memory-dir argument is **optional** and only classifies memory-note links |
| `frozen_tier_check.py <ref>` | was substance altered in a frozen tier, or only repointed and appended? **exit 1** a substance or deleted verdict · **exit 2** the filter matched nothing, so nothing was checked. **That exit exists because the tool once reported "nothing changed" nine times having read no diff.** Pass frozen **file** paths, never a directory |
| `pass_invariants.py <ref>` | every end-of-pass check in one call, run once. **exit 0** clean, **skips reported rather than hidden** · **exit 1** an invariant failed — read the section, do not re-run hoping · **exit 5** bad invocation. Reports SKIPPED rather than failed where the index refuses inside a worktree, which is correct there |
| `scope_manifest_validate.py <manifest> <branch>` | does a sub-agent's structured return match the branch it wrote? **exit 0** holds, **UNVERIFIED reported rather than hidden** · **exit 1** an assertion failed · **exit 5** bad invocation or unparseable. Unknown keys are preserved and reported, never rejected |
| `vault_commit.py -m "…" -- <paths>` | refuses a bare commit and a half-rename. **exit 2** a rule refused it · **exit 3** nothing under those pathspecs |
| `obsidian.py` | vault query, and the link-preserving route for renames and moves |
| `frontier_slice.py`, `verify_pr_markers.py`, `closure_check.py` | as above and §7 |

**Invocations, and the one-off project scripts no role runs, live in the workstream's own tool inventory** —
not here, because an inventory goes stale the way a count does and this document carries neither.
**Vault machinery is defined by membership in the template**, which is what makes the boundary checkable:
durable role machinery lives here, one-off analysis lives in the vault.

### `curator` — reach, and the surfaces no scope owns

▢ **The role for "the vault feels messy."** It exists because reach is a cost: a `librarian` invoked on one
workstream should not carry the prose for deciding what the vault needs. Added 2026-08-20 as the owner's answer
to the +23%-per-scoped-pass measurement above; the earlier ruling that a `curator` *may earn its own role later*
is discharged by it. **It is not a rename of the `librarian`** — that remains ruled out.

**What it does.** Screens and partitions the vault into scopes, dispatches one `librarian` per scope in its own
worktree, then does what no single-scope agent can: merges their branches, applies cross-scope link repoints,
corrects claims another scope's work falsified, normalizes a convention applied inconsistently, fuses two
workstreams that are one effort, syncs the shared surfaces, runs the invariants and commits.

**Governing rules.**

- **It never rewrites a document's substance.** Every judgement about what a document should say belongs to the
  `librarian` it dispatched, which needs no permission inside its scope.
- **It owns `README.md`, `CLAUDE.md` and the memory pointer**, and nothing else writes them. A `librarian`
  reports its surfaces delta rather than applying it.
- **Only run it when several scopes are genuinely overdue.** **Adding a scope costs a whole pass floor**, and the
  floor is most of a pass; batching documents into one scope is nearly free. One or two scopes overdue is a
  `librarian` invoked directly.
- **Screen on shape, not delta.** A zero-file delta certifies nothing: the two largest restructures of one run
  had empty deltas. Skip only on three git-or-filesystem facts together — no delta since the *consolidated*
  baseline, a folder-note under bound, and nothing at the scope's top level beside it.
- **A pass is not over until every spawned scope has returned or been accounted for.** ⏳ Regressed once after
  being fixed — an orchestrator said it would wait and then returned, costing a full context resume. **Live and
  unmitigated in prose**, which by §10 means it wants a tool.
- **Validate and merge incrementally.** Holding the merge until the last scope lands has left 55% of a run's
  span idle; paths are disjoint, so only the README sync needs them all.
- **Isolation does not replace reconciliation.** Worktrees stop agents corrupting each other's work and do
  nothing about links and claims that cross a boundary.
- **A grand plan and a top-level folder stay the owner's**, as for the `librarian`.

| tool | contract |
|---|---|
| `scope_manifest_validate.py <manifest> <branch>` | does a scope's structured return match the branch it wrote? **exit 0** holds, **UNVERIFIED reported rather than hidden** · **exit 1** an assertion failed · **exit 5** bad invocation. Unknown keys preserved and reported, never rejected |
| `pass_invariants.py <ref>` | every end-of-pass check in one call, run **once, after the merge** |
| `pass_log.py start --parent`, `stop` | one record per scope plus its own run; `--parent` keeps its lineage from reading as a conflict with itself |
| `scope_recon.py`, `verify_pr_markers.py`, `vault_commit.py` | as above and §7 |

### `scout` — read-only reconnaissance, in a context that is discarded

**What it does.** Surveys a scope and returns a distillate. Its context is **discarded** on return, so the
sifting costs the caller nothing but the answer. **That is the whole reason the role exists**, and no
in-line duty reproduces it.

✅ **It carries named briefs** rather than one job:

- **`orientation`** — read the closed tasks and `historical/`, return the warnings that bear on a task
  about to open, each with its source path so the caller can pull it forward.
- **`sizing`** — is this task or parent over budget, and does the workstream want extraction or a split.
- **`closure`** — which tasks look done. A merged PR is a **heuristic**: mechanical, dated externally, and
  authority to *ask* whether a task is closed, never to close it — auto-promotion would be inferring
  completion. A task carries zero, one or many PRs. **Tasks with no PR need no analogue**: they close on
  their own markers and the heuristic simply does not fire. A vault that is never pushed is entirely this
  case.
- **`recon`** — the mechanical facts about a scope: deltas, inventories, folder-note sizes, frontmatter,
  the link graph, which scopes are worth a worktree.

**Governing rules.**

- **Writes nothing in the corpus, curates nothing, commits nothing.** The guarantee is about the vault's
  documents and it stops there. ✅ **It announces itself in the pass log like every other role** — `start`
  before it reads, `stop` when it returns. The log is machinery state rather than corpus (§7), so a
  write-nothing rule read as covering it made the one role that goes in ahead of everyone else invisible to
  everyone else, which is the single thing the log exists to prevent.
- **It returns findings and a recommendation**, with the inputs behind them, so the caller can disagree
  cheaply. It does not hold a question back for someone else to ask.
- ✅ **Open the report with `scope_recon.py`'s raw output.** Naming the tool did not make an agent reach
  for it; requiring the output did. **What fires is a schema, not an exhortation.**
- ✅ **A mandatory `## Not looked at` section.** An announced gap costs the caller one command; a silent
  one reads as a clean result.
- ✅ **Slice mandated, with one carve-out:** the `orientation` brief reads closed-task bodies, because
  there reading *is* the job.
- ⏳ **Its mandatory dispatch has never fired** — fourteen recon commands ran in a context that had to
  survive to reconciliation, with no scout sent. Encoded in prose, unmitigated.
- ✅ **No separate role was added for orientation.** A role for a duty that already has an owner pays a
  whole pass floor to fix a missing brief. **Do not re-propose.**

| tool | contract |
|---|---|
| `scope_recon.py <scope> …` | every mechanical fact about a set of scopes in one call, replacing a long tail of forensic invocations. Does not emit refs the verifier aborts on |
| `budget_check.py <ws>` | the `sizing` brief. **exit 2** over the signal → extract or split, never trim. Prints the largest sections, so *what to extract* comes from the same call |
| `pass_log.py start\|stop\|active` | announce itself, close it on return, and read who else is on this ground |
| `frontier_slice.py`, `closure_check.py` | as above and §7 |

## 7. Cross-role machinery

### Isolation, retired — what replaced it

✅ **Worktree isolation is retired (2026-08-20).** It was standing in for two failures, and both now have
cheaper guards that already existed:

| the failure | what guards it now |
|---|---|
| two agents writing one file | a **disjoint path-prefix partition**, plus `pass-log start` exiting 1 on overlap |
| a commit capturing another session's work | `vault_commit.py` refusing staged paths outside the pathspecs |

**What it cost, measured:** five defects of its own, every one a tool answering about the wrong tree —
a stale `origin/main` base, `frozen_tier_check.py` with no `--vault` returning a false green, the Obsidian
index unusable from a worktree, `vault_commit.py` resolving the configured vault rather than the cwd,
`pass_invariants.py` anchors red on an untracked log. Against that: the three recorded clobbering
incidents (2026-08-18) were each a scoped `git add` followed by a **bare** commit, which a worktree does
not prevent and a pathspec does.

**Two things survive it.** First, **a tree at an unexpected commit reports clean** — the delta still
computes, so the failure looks like success; two sub-agents once caught this and reset before writing, one
having been handed a folder-note 22 KB smaller than the one it was sent to edit. Any agent given a base ref
checks `HEAD` against it before reading. Second, **nobody changes HEAD in a shared checkout**: creating a
branch moves it for every session in the tree, so the next agent's commits land on someone else's branch.
That is the one hazard retiring isolation adds.

### The pass log — one file, and every role announces itself in it

`pass_log.py`, appending to `pass-log.jsonl` at the vault root. **One shared log, not one per unit:** the
question it exists to answer is *what is another agent doing right now*, and answering that from N logs is
not answering it. **Untracked**, because N worktrees appending to a tracked file conflict on every pass,
and because this is machinery state rather than corpus — nothing in the vault should cite it.

**It now carries the load the write-authority partition used to.** That is what makes §6's role collapse
safe: `start`/`stop` records make concurrency visible directly, where the role split was standing in for
the same guarantee.

| command | contract |
|---|---|
| `start <role> "<desc>" [--scope S] [--kind K] [--parent ID]` | prints the pass id. **exit 1** = a concurrent open pass overlaps this scope; judge it before writing. `--scope` must be a **path** — whitespace is refused, after an agent passed its description there and recorded a pass no overlap check could match. `--parent` keeps an orchestrator's run from reading as a conflict with its own children |
| `stop <role> "<desc>" [--result R]` | `consolidated` \| `incremental` \| `skipped` \| `aborted`. Records span, commits and files changed **itself, from git**. **There is no metric flag:** it lasted one run and indicted itself, when a dump recorded a span by hand that the subject's own record already carried correctly — two figures for one span, the hand-typed one wrong. **exit 2** = a defect, not a judgement call: a non-full pass claiming `consolidated`, a stop with no start, a double stop |
| `active [--scope S]` | open passes with age, and STALE past a threshold — an agent that died, not one still working |
| `baseline [--scope S]` | the last `consolidated` full run and its HEAD sha as the delta anchor. **exit 1** = no baseline, so the pass is necessarily full |
| `history [--scope S]` | what recent passes did, when, and their spans — the input to §3 |

**Only a full run's record establishes a baseline.** Deltas stack, and their accumulated weight *is* the
signal that the next full run is due. A record carries the HEAD sha, so rewriting history afterwards
orphans every anchor.

**The one failure mode seen so far is an unclosed `start`, and it fails safe** — another agent backs off
unnecessarily. Every role closes what it opened, including scopes it skipped.

**The git-tag mechanism this replaced is dead.** A tag was one global name per scope, so it could say
neither *when* a pass ran nor that two agents were on the same ground, and none were imported as
baselines. **Do not re-propose importing them.**

### ▢ Coordination, once everything but the dump is async

Background passes can overlap, so something has to keep them off each other's files.

- **The log stays the append-only source of truth.** An append-only log cannot go stale-wrong; a status
  file has to be kept correct by whoever crashed.
- **Status is a derived view a tool renders, not a second file.** `pass_log.py active --scope <s>` already
  computes it, so **an agent never parses the log** — it pays one fast call and reads a few lines. Call it
  *status*; it is not a frontier.
- ▢ **Two gaps to close.** `active` is scope-*prefix* granular rather than file-level, and it is advisory
  — nothing refuses. Close both **inside the tools that write**, per §3, so the check costs no extra agent
  call.
- ▢ **A handoff or a dump must be able to ask "is anyone churning right now?" in one call.**
- **[DEAD END] Renaming a file with a `.locked` suffix while working on it.** Breaks the link graph,
  Obsidian, and git paths mid-operation, and a crashed agent leaves a file locked forever with no
  age-based recovery. **Do not re-propose.**
- **[DEAD END] A second status or lock file alongside the log.** One store with a derived projection, not
  two things that can disagree. **Do not re-propose.**

### Porting a shared surface — retired 2026-08-20

**There is one copy now.** The machinery moved into its own repo, so nothing is shared-by-copy with a
vault and there is nothing to port: author here, once. The section below is kept as the record of what
the loop cost and what it taught, because both are reasons not to rebuild it.

**Why it existed at all:** these files were duplicated into every vault that used them, and a
placeholder substitution rewrote the vault's path into each copy. **Why it is gone:** the harness reads
agent definitions and skills from `~/.claude`, never through the vault-as-project, so the second copy
bought nothing — and a plugin's `bin/` is on `PATH`, so a definition can name a command instead of a
path. Measured 2026-08-20: 6 files needed hand-ports on every change, and `${CLAUDE_PLUGIN_ROOT}` —
the obvious replacement for the placeholder — is **empty in a subagent's shell**, which is why the
answer is a command name rather than an interpolated path.

**[DEAD END] Keeping the duplication and improving the port tooling.** Three tools existed for it, one
written specifically because the substitution had broken a different way each time it was touched, and
six files still needed hand-porting. **Do not re-propose.**

**Two lessons worth keeping, both paid for:**

- **A port check must not be byte-identity.** A vault names real repos, shas and dated evidence where a
  generic copy stays generic, so diffing to zero destroys the part meant to differ — and an identity
  check rewards you for it.
- **A wholesale copier flattens deliberate divergence.** `--apply` would have deleted 18 lines of
  project-specific wording from one skill and 19 from one tool.

### Where a tool lives, and how a definition names it

| mechanism | measured 2026-08-20 |
|---|---|
| `${CLAUDE_PLUGIN_ROOT}` | **empty** in the Bash environment of a subagent spawned from a plugin. Documented for component files; do not rely on it in a definition |
| `<plugin>/bin` on `PATH` | **yes**, for three separately installed plugins. This is the mechanism: a definition writes `lipika <command>`, with no path to be correct about |
| the vault's location | never written into a definition. `vault_config` resolves it — flag, then `$LIPIKA_VAULT`, then `~/.config/lipika/config.json`, then the checkout — and **refuses rather than guessing**, because a tool that guesses its target curates the wrong tree and reports success |

### `agent_transcript.py` — read another agent's run

| command | contract |
|---|---|
| `--list [--cwd PATH]` | every session under a project slug and its subagent transcripts, newest first, with sizes, agent types, and a LIVE marker on anything still being appended. **A worktree session has its own slug**, so `--cwd` is how you reach it |
| `<id>` | calls, per-tool byte totals, and cost with the traps applied — peak cache-read never a sum, cache-creation reported separately and **never added**, newlines rendered visibly because collapsing them fabricates pipelines |
| `<id> --calls --min-bytes N` · `--grep PATTERN` | the expensive reads; whether a mandated tool actually fired. The call table carries a reasoning-bytes column and marks tool errors |
| `<id> --thinking [N]` | the N largest reasoning blocks in full, with the call each preceded. **For reading, not counting** |

✅ **A profile opens with a qualitative read of the run, before any figure** — the required questions live
in `agent-eval-method.md`, each answerable only by pointing at a call number or a quoted line.
**A size is not a finding:** reasoning bytes locate where to read and say nothing about whether the
thinking was good.

✅ **Per-call figures come from the transcript, never from an agent's own report.** The log says a pass
happened and what it moved; the transcript answers how it went. The agent being profiled spends nothing,
because it is not the one reporting.

**Transcripts are session-scoped and they disappear.** `sources/evals/` is the durable record, which is
why it is frozen. **Bytes returned per call is the denominator** of a relevant-fraction measurement; the
classification — load-bearing, duplicated, never used — is judgement and stays with the profiler.

## 8. Delta and full are two different jobs

- **Delta — the work at hand, going fast.** It does the work and stops. No restructuring.
- **Full — housekeeping whose purpose is to keep delta fast.** Consolidation, promotion to `done/`,
  sorting `historical/`, semantic splits. ▢ Send a `scout` in first and answer what it brings back.

▢ Splits are a **named duty of a full run** rather than a threshold a delta might trip over. The trigger
is weight, and the parent's budget makes it measurable: over budget proposes a full run, and the full run
opens the extract-or-split question and then executes it.

**Rejected: a chain of delta anchors a later pass walks to reconstruct coverage.** More machinery for the
same guarantee — the weight signal already says when to consolidate, and a chain adds a second thing that
can be wrong.

### What to measure

**Measure what a role loads, and how much of it bore on the work at hand.** Tokens and wall clock are
consequences; relevance is the quantity this design moves. ✅ The relevant fraction now exists as one
measurement over one workstream — figures and per-read classification in `sources/evals/`. One data point,
and the denominator is a choice: read the method before arguing with the number.

Two things easy to get backwards:

- **A pass has a floor, and the floor is most of it.** The floor is paid regardless of backlog, and input
  context is re-paid every turn, so it multiplies by turn count. Batching documents into one scope is
  nearly free; **adding a scope costs a whole floor.**
- **A parent agent blocked while its children run is not a cost.** It costs no tokens, the children work
  throughout, and a high blocked fraction is closer to evidence the fan-out is working. Report **span**
  and **slowest-child duration**. See §11.

## 9. Invariants, with what would falsify each

Each is a claim, not a preference. **The operative wording lives in `CLAUDE.md` and the agent
definitions; on any conflict those win and this table is the stale copy.**

| invariant | why | falsified by |
|---|---|---|
| An agent is pushed what bears on its work | A surface full of another task's warnings fails as a long one does | Recall flat in the irrelevant fraction |
| A background pass's cost is its slowest child | Width was not the driver: 6 scopes cost 1,407 s, 2 scopes cost 2,155 s | A run whose span tracked scope count rather than its largest scope |
| One frontier per live task | Two live copies of status must be hand-synced and diverge; tried and reversed in a day | A second live frontier held in sync for a month |
| A push surface must stay short | A dead end fires unprompted or not at all | Agents reliably reading a register they were not required to open |
| Every metric carries the date it was taken | Undated figures invite every later agent to correct them, which costs more than staleness | Agents agreeing on an undated figure across a month |
| Over budget means extract or split, never trim | The task summaries are among the most useful things here | A workstream held under budget only by deleting history, with nothing lost |
| A live document points at what was archived out of it | Otherwise archiving is how a warning goes dark | An archived warning found reliably with nothing pointing at it |
| Unread material is never marked consolidated | Applies to a skipped scope and to `historical/` alike | — definitional |
| Markers are the only authority to call an ITEM done | Every overreach found so far was an unlicensed upgrade | An agent inferring an item's completion correctly and repeatably |
| A task closes on judgement, not on a marker | A task always carries a `▢`; requiring a marker made closure impossible — 0 closed tasks in the vault's history | Tasks closing reliably while closure needs an explicit owner marker |
| Residue carries sideways on close, never up | The parent grows monotonically otherwise, reproducing the problem one level up | A parent absorbing every closed task's residue and staying readable |
| One marker per separately-statused fact | Measured overreaches trace to composite markers | Composite markers reconciled correctly across passes |
| An edit keeps every fact; wording and redundancy are fungible | Semantic loss is the harm; rewording is not | A reworded document that lost a fact nobody noticed for a month |
| `done/`, `sources/`, `external/` are append-only — for three different reasons | Fidelity, delivery, and read cost. §5 | mostly definitional; the `done/` one is a cost claim and could be wrong |
| Prose in a definition does not fire; a tool with an exit code does | Every measured instance of a rule silently not firing was fixed by moving it into a tool | A rule holding across several passes on prose alone |

## 10. Three tool-design rules the set was built on

- **Prefer a tool that refuses to prose that asks.** Measured: a scope-screening condition shipped
  unsatisfiable and went unnoticed until it was used; a mandatory dispatch did not fire across fourteen
  recon commands; an agent told to prefer the Obsidian CLI never checked whether it was answering about
  the right tree; a verifier reported "nothing changed" nine times having read no diff. Every one was
  fixed by moving the rule into a tool with an exit code. It is also the cheaper end — a definition is a
  system prompt paid on **every** invocation.
- **A check that stays red on correct content gets dismissed.** A fourth marker-licence rule was tried and
  **removed** at 1 true positive against 3 false. Do not re-add a rule without per-item locality, and give
  every new check a hand-audited red case and a green case.
- **A check reports what it did not check, rather than swallowing it.** Skips, UNVERIFIED rows and
  empty-filter cases are surfaced with their own exit code or label — an unannounced gap reads as a
  clean result, which is how one verifier reported "nothing changed" nine times having read no diff.
- **A required step must name what it catches *and* what it costs.** §3 makes span a budget, so
  "move it into a tool" stops being a free answer. This is in tension with the first rule deliberately;
  the resolution is that tools should be **fast**, not that rules should stay in prose.

## 11. Standing tensions — open, deliberately

Only what is unresolved. An answered question becomes the design above and leaves here.

- `[OPEN Q]` **What a full pass can actually cost.** The 480 s / 300 s ceilings are falsified on four data
  and are now observed baselines instead (§3). Open: whether the floor is reducible at all, or whether a
  first pass over an untended scope is simply developer work and exempt.
- `[OPEN Q]` **How to make the semantic-loss check cheap.** §5.
- `[OPEN Q]` **Coordination granularity and teeth.** §7.
- `[OPEN Q]` **What is the count-based trigger, if any**, and does it or the state-change gate govern? §6.
- `[OPEN Q]` **The BYTE budget numbers are still guesses** — 8 KB / 12 KB against non-register bytes,
  calibrated against this corpus and nothing else. A second converted workstream is the second data point.
  Note that closure, not extraction, is the first answer when a frontier is over budget carrying closed work.
- `[OPEN Q]` **Which required steps earn their round trip.** A budget question now, not a curiosity.
- `[OPEN Q]` **Should a `scout` write a report for later auditing?** Leaning no — writing nothing is the
  property that makes the role safe, and `sources/evals/` may already cover the need.
- `[OPEN Q]` **Do lists of typed facts beat synthesis?** Promotion and synthesis pull in opposite
  directions: promoting preserves register items as a list, synthesis destroys the list on purpose. §4
  says *when* to promote and *what* to pull; it does not say which to reach for.
- `[OPEN Q]` **Does the qualitative read need a second reader?** One profiler's judgement about another
  agent's run is exactly the kind of claim this system normally makes someone verify, and nothing verifies
  this one.
- `[OPEN Q]` **Whether workstream-local `design/` and `reference/` documents cut the cost of proving nothing
  was dropped.** Smaller reference documents may make an adversarial check cheap enough to run at the point
  of a split. Extraction into one is now step 3 of a rollover, so this gets exercised on every close.
- `[OPEN Q]` **`historical/` has no orientation check behind it.** Nothing forces a new task to review
  closed ones beyond the shape check. `historical/` staying live is the only current mitigation.
- `[OPEN Q]` **Where role tooling should live.** Durable machinery and one-off scripts share one `tools/`,
  distinguished only by what is shared upstream. Co-locating a role's tools with its definition runs into
  a hard constraint: **agent definitions are flat `.md` files whose registry reads `*.md`**, so an agent
  becoming a directory stops registering. It also cuts against the assignment, since several tools serve
  every role. Owner's call; the constraint is stated so it can be made with the facts.
- **Marker spelling is inconsistent.** **Evolve toward one form; do not rewrite the past unprompted** —
  sweeping old documents for consistency is slow and wasteful. New writing picks the current form, tools
  tolerate both, and anything counting items reads both.
- **[DEAD END] Attacking a parent agent's blocked time.** Ranked the largest problem across three passes
  and was never a cost: no tokens, children working throughout, fan-out wall clock `max(child) + overhead`
  by construction. Two attempts on record — a polling fix, then incremental merging — both correctly
  failing to move a number that was never loss. **Do not re-propose.** The lever is the **slowest child's
  duration**, which §3 makes the primary metric.
- **[DEAD END] A "turns that thought and called nothing" signal.** Built, measured against a real run,
  deleted: the harness emits reasoning in its own message, so the count was *every* deliberation — 37 of
  37 on one run. **Inventing a defect is worse than missing one**, and a shape in a transcript is not a
  behaviour.
- **[DEAD END] Loop detectors and scoring over reasoning** — repeat-call clustering, retry chains,
  oscillation windows, shingle overlap between thinking blocks. Scaffolded, then dropped: the ask was a
  gut check, not a classifier. Reconsider only with a run a human read that a detector would have caught.
- **[DEAD END] Banning mutable measurements from documents.** The correct fix is dating them; agents
  correcting each other about undated figures is the cost, not the figure aging.
- **[DEAD END] "`done/` is a retrieval surface, not an archive" as an invariant.** It asserts nothing —
  material is retrievable from an archive too. Replaced by *a live document points at what was archived
  out of it*, which is checkable.
- **[DEAD END] Deleting a resolved-question ledger** without first folding the answer into the relevant
  section. That deletes the content along with the question.

## 12. How to read and maintain this document

**Living document, and the place to experiment.** It states the current and desired state of the system
and is the platform for changing either. Mechanisms marked `▢` are untested and their numbers are
hypotheses: run them, measure, and amend here with a dated amendment.

**Not a frontier.** A `▢` means *the system is not this shape yet*, not *someone should go do this*. A PR
number or a next-move appearing here means it has become a second frontier.

**Voice.** Terse and factual, written for a first-time reader. A rule its own owner cannot parse has
failed, however well it encodes a real measurement — rewrite it rather than re-explaining it.

**Where things live:**

| document | carries |
|---|---|
| `CLAUDE.md` | the normative rules, terse and operative |
| `agent-eval-method.md` | the **procedure** for changing and measuring an agent |
| the workstream's own docs | the **record** — what each round found, with figures |
| `sources/evals/` | the **verbatim measurements**, frozen and dated |
| this document | the **design** — the shape, the forces, the falsifiers |

**Developed through the loop in `agent-eval-method.md`** — author here (there is one copy of every file),
prove no rule was dropped, try it on real work, profile it, summarise the round where the next agent will
read it, feed the findings back. That return edge is the difference between a design that stays true and one
that becomes aspirational.

## Amendments

**2026-08-20 — merged into one document, and the role machinery redesigned.** This document absorbs what
was a separate per-role reference; §6–7 are that material, kept in its own shape because the role-by-role
cut is the part worth reading. The redesign it encodes, all owner decisions:

- **Five roles become three.** Coordination folds into the `librarian` as a fan-out scope; the
  `frontier-clerk` is retained as the cheap middle tier. What makes the collapse safe is that the pass log
  now provides coordination directly, where the write-authority partition was standing in for it.
- **Act, then report for correction**, replacing detect-propose-execute-on-approval — which never fired in
  two separate homes.
- **Two minutes becomes an aspirational north star for every operation**, tiered by role, with
  developer-facing work exempt. It was previously one role's ceiling.
- **Only the dump is synchronous.** Everything else is background, which needs a coordination scheme; the
  log with a derived status view is the chosen one, and two alternatives are recorded as dead ends.
- **Append is free; editing needs a semantic check.** Keep every fact, reword and merge freely. `done/`
  keeps its append-only status for a **read-cost** reason — the corpus is not a normalized store.
- **Tools are encouraged, not rationed**, and logging moves inside them.

- **Roles fall in two classes**, operating and vault-development, and only the operating ones carry §3's
  budgets. The profiler was never an operating definition and was never counted as one.
- **A `curator` takes the vault-wide reach back out of the `librarian`** (owner decision, 2026-08-20, after the
  fold was measured at +23% on a scoped pass). A `librarian` now gets one scope and full autonomy inside it,
  bounded by losslessness; the `curator` owns which scopes exist, everything crossing a boundary, and the shared
  surfaces. Five definitions became three and then four.
- **Splitting a workstream is the `librarian`'s to execute and report**; a grand plan stays the owner's.
- **The `scout` announces itself in the pass log.** Its write-nothing guarantee covers the corpus, not the
  machinery state that tells every other role where it is.

Three claims the previous documents stated the other way, corrected here: the dump-and-reconcile split is
**time management**, not a claim about the dumping agent's judgement; the slice mandate is the
**clerk's specifically** and does not generalise to a `librarian` doing a merge; and a required step is
**not** to be understood as a cost to be minimised against the span budget.

**Earlier amendments, compressed.** This document was reframed on 2026-08-19 around partitioning — *work
evolves, so context must be partitioned as pieces of it emerge and finish* — which is when the sub-unit
became a dated **task**, budgets arrived to make the sizing question mechanical, and measurements became
dated rather than banned. A later round the same day recorded the pass log replacing one-log-per-unit, and
the reconciliation gate replacing unconditional dispatch. **The owner decisions behind each live in the
workstream's record, not here**, per the division above; this section keeps only that they happened and
when.
