---
type: reference
status: reference
date: 2026-08-19
tags: [vault, meta, agents, ontology, design, model]
---

# The design — what shape this system has, why, and what is not built yet

## 1. What this is for, and the choice that constrains everything else

The vault is durable cross-session memory for engineering work: a **cohesive corpus**, read by agents that need
continuity, deliberately not a stochastic index. Every other choice follows from that one.

- **What it buys.** An agent can be pointed at one file and get the frontier, the gates and the next move. Facts
  arrive **whether or not the agent thought to ask for them** — the only reason a recorded dead end ever prevents
  anything.
- **What it costs.** Curation is slow and it is work. Vector search over the same material would be faster to
  maintain and would need no ontology at all.
- **Why the trade is taken anyway.** The corpus's most valuable contents are *negative* results — ruled-out
  approaches, gates, landmines. A negative result's trigger is someone about to re-propose the thing, and that person
  by definition does not know to query for it. Pull-shaped retrieval cannot fire on the absence of a query. This is
  the argument for a **push** surface, and it is independent of retrieval technology.

### The force that shapes everything downstream: work evolves

A push surface only works while what it pushes is about the work at hand, and while it is short enough to be read
**at the moment of proposing**. But work does not hold still. Pieces of it emerge, change what they are about, and
finish — so **context must be partitioned as they do**. Otherwise one surface accumulates everything the effort ever
contained, and whoever opens the current piece is pushed all the previous ones.

That is the requirement §2 exists to meet. Length is its tractable proxy and not the thing itself: a short surface
full of another task's warnings fails the same way a long one does.

## The goals

Judge every change to this system against these, in this order.

1. **An agent is pushed what bears on its work, and little else.** Relevance first, volume second.
2. **A warning fires unprompted or it does not count.** A dead end's trigger is someone about to re-propose the
   thing; it cannot wait to be queried for.
3. **Nothing is lost when it stops being current.** Context that stops bearing on the work moves somewhere
   retrievable, not somewhere gone.
4. **Adoption is incremental.** No shape is worth a re-architecture; a workstream converts when it is next touched.
5. **Every claim names its enforcement, or admits it has none.**

## Where things live, and why this document carries no figures

| document | carries |
|---|---|
| [[CLAUDE]] | the normative rules, terse and operative |
| [[agent-eval-method]] | the **procedure** for changing and measuring an agent |
| the vault's own maintenance record | the **record** — what each round found, with figures |
| `sources/evals/` | the **verbatim measurements**, frozen and dated |
| this document | the **design** — the shape, the forces behind it, the falsifiers |

It links to those and restates none of them. The division is load-bearing rather than tidy: a rule or a figure copied
into a second home drifts, and the copy that drifts is often the one an agent reads first.

This document and [[agent-eval-method]] are generic enough that a clone wants them, so **both ship in
`dnsco/knowledge-base-template`** and `reference/` is a shared surface.

**This document carries no measurements. It does carry parameters.** The distinction matters and is easy to blur: a
**measured figure** is record and lives in `sources/evals/`, dated and frozen; a **chosen threshold** is a design
decision, revisable here. Where a claim rests on a measurement, it points.

**The mechanisms below are not calibrated.** None of them has run. Numbers in this document are **hypotheses for the
next round of evals**, and the design is explicitly the place to experiment with them and record what the experiment
said. A threshold that has never fired against a real corpus should be argued with, not obeyed.

## 2. The document ontology

A workstream's sub-unit is a **task**: a dated piece of work that owns its own frontier, holds the dumps written
during it, and **closes**. A task is a folder, not a file.

```
workstreams/<ws>/
  <ws>.md                        parent — task index + a thin restated subset + cross-task invariants. No date.
  YYYY-MM-DD-<task>/             a live task
    <task>.md                    its frontier — detailed, its own gates and PR numbers while live. Not dated.
    YYYY-MM-DD-<topic>.md        dumps written during it
  historical/                    LIVE, not done — unsorted pre-conversion context
  done/YYYY-MM-DD-<task>/        closed tasks, per-workstream. The retrieval surface.
  design/                        stable reference, no live status.

workstreams/done/<ws>/           ▢ a finished workstream, moved whole
```

*Terminology, because the vault spends these words:* a **task** is the sub-unit above. A line in a register is an
**item**. A dated document written during a task is a **dump**.

**A workstream was doing two incompatible jobs.** It was the unit of *work* — long-lived, accumulating, which is how
continuity survives — and simultaneously the unit of *retrieval*, which wants to be small and about one thing. The
accumulating job won. Splitting the two across a parent and its tasks is the partition §1 requires.

- ▢ **A task owns the detailed what's-next** — its own frontier, its own gates while live, its own PR numbers.
- ▢ **A task is where a dump lands.** A dated dump has an obvious home that is not the workstream root, which is what
  stops one piece of work's notes from being pushed at the next.
- ▢ **The parent is a task index, a thin restated subset, and a small set of cross-task invariants** — one line per
  task live or closed, only the warnings that bear on *every* task, and only the very highest-level state. **The
  register stays here** rather than moving to a document agents must be told to open, which is how a warning stops
  firing. Coaxing toward splitting is what keeps it short. ▢ A variant worth costing if it does not: **keep warnings
  that must fire unprompted resident in the parent, and move out only the already-mitigated ones**, which are
  reference rather than warnings.
- ▢ **Promotion to cross-task is an owner's or a `librarian`'s call, never a working agent's.** "Workstream-wide, not
  task-local" is the upgrade-direction distinction-collapse this system reliably fails at. **Default is task-local.**
- ✅ **A task folder carries the date stamp; its frontier does not.** `YYYY-MM-DD-<task>/<task>.md`. The date is what
  makes closing a task mechanical rather than a judgement call; a task with no date never closes. Dumps inside are
  dated individually. The parent folder-note is not dated.
- ✅ **`done/` is per-workstream**, and a live document points at what was archived out of it.
- ▢ **A finished workstream moves to `workstreams/done/<ws>/` whole**, and the repo's top-level `done/` should stop
  existing. That is a migration, not a rule anyone can apply piecemeal.

### `historical/` is live, and that is deliberate

▢ **Only an extant workstream gets one**, and only if it carries content predating the task ontology. A new
workstream has nothing to put there and should not have the folder.

▢ Pre-conversion context lands in `workstreams/<ws>/historical/` as a **live task**, and a `librarian` splits material
out of it into `done/` over time as it is understood.

**It must not go into `done/` on conversion.** Doing so claims consolidation over material nobody has read, which is
the same error as recording a skipped scope consolidated — and it is how context gets lost rather than partitioned. Live means: not
claimed as consolidated, still reachable, still a `librarian`'s to sort.

This is also what makes the lazy conversion in *Conversion is lazy* safe before the orientation check exists. Nothing
is archived, so nothing goes dark; the worst case is that material stays unsorted, which is where it already is.

### The parent points by default

A parent restates a thin set of high-level things — what this effort is, where it stands at the coarsest grain, what
must fire regardless of task. Everything else is a pointer.

✅ **A measurement carries the date it was taken.** An undated figure invites every later agent to correct it, and
correcting each other about mutable numbers is the expensive failure — not the number being stale. Write "9 KB at
2026-08-19", not "9 KB".

### The parent's budget, what it does not apply to, and what breaching it means

✅ **The parent carries a byte budget, asserted by a check** — because "thin" in prose does not fire and a size in an
exit code does. `tools/budget_check.py`, exit 1 over target and exit 2 over the signal, and it prints the largest
sections so *what to extract* is answerable from the same call. First run over this corpus: **four of the five named
workstreams are already over the signal** (2026-08-19), at 21–59 KB.

▢ **Starting hypothesis: 12 KB target, 16 KB the signal.** These separate today's smallest parent (~9 KB) from the
oversized ones (21–59 KB) and nothing more. **No parent has been built under this design, so the threshold is a guess
with a shape**, to be moved by the first eval against a converted workstream.

▢ **A task has a limit too.** A task whose frontier will not stay readable should be split and its finished part
archived. The parent's budget and the task's are different numbers for the same reason, and ▢ **sizing both is the
`scout`'s question** — see §3.

▢ **Over budget likely means the workstream should split — and splitting is not the first move.** Two responses,
cheaper first:

1. **Extract.** Material that is reference rather than a live warning, and useful beyond this workstream, goes to
   `reference/` or `design/`. This is how the vault already sheds weight, and it is right whenever the context is
   genuinely salient but not genuinely *this* effort's.
2. **Split.** When the parent is heavy because it is two efforts wearing one name.

▢ **It never means trimming the task index.** The summaries of what happened are among the most useful things here;
the pressure falls on the restated subset and the cross-task invariants, and the index grows freely as tasks close.

This is also the missing signal in §3: split *detection* has never fired because nothing measures the pressure. A
parent over budget is that measurement.

### Carry-across on open, not carry-up on close

▢ **When a task opens it pulls forward the warnings that bear on it** — from the workstream's closed tasks and from
`historical/` — into its own frontier. Selection is paid **once per task**, at the moment someone knows what the task
is about.

**Rejected: migrating still-live context up into the parent on close.** The parent then accumulates monotonically,
reproducing the problem one level up — and correctness makes that worse, since reversing an overreach means
re-*expanding* distinctions a previous pass collapsed, so a register grows while being deliberately drained. Figures:
the vault's own maintenance record.

**What this depends on, rather than assumes:** a closed task holds warnings that may still be live, and nothing is
lost *provided the pull happens*. Without a forced pull, promotion to `done/` is how a live warning goes dark quietly
— which is exactly why `historical/` stays live. See §3.

### Conversion is lazy, and that is the design

▢ There is no migration project.

- **An extant active workstream** gets its last few tasks split out as dated folders, and everything else folded into
  `historical/`.
- **Every other extant workstream gets only a `historical/`**, picked apart when it is next lit up.
- **A workstream created after this design needs no conversion and no `historical/`.**

**Conversion and normal operation are the same mechanism.** Being lit up means opening a task, and opening a task is
when relevant warnings get pulled forward. No workstream pays a conversion cost until someone is already reading it.

## 3. The role ontology — write authority, tools, and what each role loads

The organising principle is **who may write what**. Concentrating destructive operations in one role is what lets
append-only agents run in parallel without clobbering each other.

| role | write authority | may not |
|---|---|---|
| `context-dump` (skill) | appends a dated dump to the live task | touch a frontier; delete, merge, restructure, re-link |
| `frontier-clerk` | frontier state — flips, strikes, demotions, promotions to `done/` | move or merge docs; rewrite prose for quality; infer completion; record a pass consolidated |
| `librarian` | structure — consolidate, archive, re-link, sort `historical/` | make engineering decisions; infer completion; decide taxonomy alone |
| `head-librarian` | coordination, shared surfaces, invariants, anchors | curate a doc; make a taxonomy or engineering call |
| `scout` | nothing — it reports | write or curate anything; decide a taxonomy; answer its own questions |

### What each role loads, which is the cost that matters

- **`context-dump`** — the live task's frontier and its own new dump. Runs in the main loop, so its reads are the
  session's. ⏳ The only role with no transcript, and therefore the one never profiled.
  ✅ It **guesses the destination and asks** — never infers silently, never interrogates. The guess is the most
  recently edited task in the most recently edited workstream, which is usually right. That is also how work belonging
  to no task gets handled: a debugging session or a spike is asked about rather than appended wherever the session
  happened to be rooted. It asks the closure question too, since a dump is its moment. The chain: a merged PR
  *signals*, the dump *asks*, the owner *answers*, the `frontier-clerk` acts on the marker.
- **`frontier-clerk`** — the frontier's mutable slice plus the dump it reconciles. ✅ Slice mandated, and the mandate
  is what moves its load; naming the tool did not. ✅ **It no longer runs on every dump** (2026-08-19, owner): a
  multi-minute agent stood unconditionally in front of the system's most frequent action. It runs when the dump
  carries a marker that moves the frontier, or when `frontier_lag_check.py` says the frontier already lags — and a
  dump that owes one still waits for it, because reporting success over a stale frontier is the failure the split
  exists to prevent. A dump that owes none says so **and names the check**, which is the difference between a
  verifiable claim and a judgement call.
- **`librarian`** — the deepest reads in the system, and ✅ **slice mandated** as of 2026-08-19, unmeasured here.
  Most of a pass is floor rather than merge work.
- **`head-librarian`** — scope manifests, shared surfaces, invariant output. ✅ Slice mandated, unmeasured.
- **`scout`** — whatever it was sent to survey, in a context that is **discarded** on return so only the distillate
  costs the caller anything. ✅ Slice mandated. ✅ It carries **named briefs** rather than one job:
  **orientation** (read the closed tasks and `historical/`, return the warnings bearing on a task about to open),
  **sizing** (is this task or parent over budget), **closure** (which tasks look done), **recon** (the mechanical facts
  about a scope). Any role may send one; a full run always does.

  A separate role for orientation was considered and rejected on this document's own argument — adding a role to hold a
  duty that already has an owner pays a whole pass floor to fix a missing brief.

### Tools

Which role must reach for what is in the vault's tool-assignment doc, with the invocations. It is the assignment's home because an
inventory goes stale the way a count does, and this document carries neither.

**Vault machinery is defined by membership in `dnsco/knowledge-base-template`**, not by a list here. The rest of
`tools/` is one-off analysis of the project this vault serves, which no role runs — absent from the template, which is what makes the
boundary checkable: durable role machinery is shared upstream, one-off analysis is not.

▢ **Layout should follow ownership.** A tool one role uses belongs in a subdirectory named for that role; tools several
roles share belong in a cross-role directory; one-off scripts stay loose in `tools/`. That is file moves and path
changes in every definition, so it is a `librarian` migration rather than anything a working agent does.

▢ **A tool wants a spec, not a one-liner** — enough written down that a change to it can be checked against what it
was for. Those blocks live with the role that owns it, or in the vault's tool-assignment doc for shared ones.

### Never infer completion

The rule every role shares, and the load-bearing one. **A marker is an agent's only authority to act.** The
characteristic failure of this system is not fabrication — it is **distinction-collapse, always in the direction of
upgrade**: *failed* read as *never requested*, *encoded* as *discharged*, *settled* as *settled-and-executed*, a
parent marked done because most of its tasks were.

▢ The gap this leaves is that nobody asks. A marker only exists if someone raised the question, and no role's job is
raising it — so **the `scout` asks whether a task is done**, and the owner answers.

### Taxonomy calls: detect, propose, execute on approval

Whole-workstream merges and splits are not an agent's decision. [[CLAUDE]] holds the rule; `agents/librarian.md` holds
the pattern — *"never decide it yourself: detect, propose, and execute on approval."*

The pattern is right and ⏳ **it does not fire** — no split proposal has come back from any pass. Not an authority gap:
**nobody's job was asking.** Every role it was assigned to was busy doing something else, and a duty that competes
with the work in front of an agent loses.

▢ **So it becomes the `scout`'s question.** The `scout` writes nothing, which makes asking exactly the authority it
should hold: it surveys one workstream and raises whether a task is done, whether a task or parent is over its budget,
and whether the workstream is two workstreams. Other roles then act on an answer instead of being expected to
volunteer the question. ▢ The parent's budget is what makes the sizing question mechanical rather than a feeling.

### Enforcement

✅ **A shape check now forces a new task to review the closed ones** — `tools/orientation_check.py` requires a
`## Carried across` section citing what it reviewed, and treats *nothing applied* and *nobody looked* as different
states by refusing an uncited "nothing to carry". Encoded 2026-08-19 and **never yet fired on a real task**, because
nothing is converted; a mandatory step in a definition has failed to fire here before, which is why this one is a tool.
`historical/` staying live remains the mitigation until it has run.

## 4. Delta and full are two different jobs

- **Delta — the work at hand, going fast.** It does the work and stops. No restructuring.
- **Full — housekeeping whose purpose is to keep delta fast.** Consolidation, promotion to `done/`, sorting
  `historical/`, **semantic splits**. ▢ **Send a `scout` in first** — it returns the sizing and closure questions the
  run then answers.

▢ Splits are therefore a *named duty of a full run* rather than a threshold a delta might trip over. The trigger is
weight, and ▢ the parent's budget makes it measurable: **over budget → propose a full run**, and the full run opens
the conversation about extraction or splitting and then executes it.

### Recording what a pass did

✅ **A pass appends a timestamped record to a JSONL log, and that is the history.** `tools/pass_log.py`. It lets an
agent see that someone else touched this five minutes ago, and line-at-a-time appends collide far less than a shared
namespace does. **The git-tag mechanism it replaced is dead** (2026-08-19, owner): nothing reads or writes a tag, and
none were imported as baselines — a tag was one global name per scope, so it could say neither *when* a pass ran nor
that two agents were on the same ground, and importing a mechanism to keep a claim nobody had checked was the more
expensive option.

✅ **One shared log at the vault root** — `pass-log.jsonl` — and **every role emits a `start` and a `stop` around its
pass.** This reverses *one log per unit*, settled and then overturned the same day (2026-08-19, owner), on a reason
the per-unit shape cannot serve: **the question the log exists to answer is what another agent is doing right now**,
and answering it from N logs is not answering it. Passes run in parallel, in worktrees, over overlapping scopes, and
the failure they produce is stomping each other's edits. **Coordination is a global question, so it gets a global
file.** A `start` with no `stop` is either a live pass or an agent that died, which the tool separates by age.

The cost is real and accepted: the log is the one thing here that is *not* partitioned, and it grows without bound.
`--scope` filters it, one line per pass boundary stays small for years, and the direction is the safe one — merging
many logs into one is mechanical, splitting one is not.

✅ **A record carries the HEAD sha**, and the next pass diffs from it. So a
`stop` is recorded from the tree holding the merged work, and rewriting history afterwards orphans every anchor.
**Untracked**, because N worktrees appending to a tracked file conflict on every pass, and because this is machinery
state rather than corpus — nothing in the vault should cite it.

What a pass records has to answer one question — **what may a later pass skip:**

- **A full run's record means consolidated.** It is the only thing that establishes the baseline.
- **Deltas after it are incremental work, not yet consolidated.** They stack freely, and their accumulated weight *is*
  the signal that the next full run is due.
- **A scope a pass skipped is never recorded as consolidated** — that converts "not looked at" into "already
  handled", and the licence to skip rests on the claim being true. `historical/` is the same rule applied to a
  folder.

Rejected: a chain of delta anchors a later pass walks to reconstruct coverage. More machinery for the same guarantee —
the weight signal already says when to consolidate, and a chain adds a second thing that can be wrong.

### What to measure

**Measure what a role loads, and how much of it bore on the work at hand.** Tokens and wall clock are consequences;
relevance is the quantity this design moves. ✅ **The relevant fraction now exists**: on the first full pass run
under this design (2026-08-19), **69.8% for the `librarian`** over 165,132 B and 55 calls, **64.5% for its `scout`**
over 63,614 B and 27 calls, 68.3% together, with 14.3% duplicated between the two and 9.3% never used. Method and
per-read classification: `sources/evals/`. One data point, one workstream, and the denominator is a choice — read
the method before arguing with the number.

Two things easy to get backwards:

- **A pass has a floor, and the floor is most of it.** The floor is paid regardless of backlog, and input context is
  re-paid every turn, so it multiplies by turn count. Batching documents into one scope is nearly free. **Adding a
  scope costs a whole floor.**
- **A parent agent blocked while its children run is not a cost.** It costs no tokens, the children are working
  throughout, and a high blocked fraction is closer to evidence the role split is working. Report **span** and
  **slowest-child duration**. See §6's `[DEAD END]`.

Current figures for every role: `sources/evals/`, frozen and dated. **Weigh their age** — a profile of a role that has
since gained or lost required steps measures a system that no longer exists. And the token traps — cache-creation counted as
context, a resumed agent's figures summed — live in `reference/agent-eval-method.md` with the rest of the method.

### The north star: a typical operation inside two minutes

✅ The ceiling belongs to the **`frontier-clerk`**, which spawns nothing, so its wall clock is entirely its own work. A
fan-out pass is `max(child) + overhead` and was never a candidate; judging one against the ceiling produced two
sub-agents' confessions.

## 5. Invariants, with what would falsify each

Each is a claim, not a preference, and each names what would overturn it. **The operative wording lives in [[CLAUDE]]
and the agent definitions; on any conflict those win and this table is the stale copy.**

| invariant | why | falsified by |
|---|---|---|
| An agent is pushed what bears on its work | A surface of another task's warnings fails as a long one does | Recall flat in the irrelevant fraction |
| One frontier per live task | Two live copies of status must be hand-synced and diverge; tried and reversed in a day | A second live frontier held in sync for a month |
| A push surface must stay short | A dead end fires unprompted or not at all | Agents reliably reading a register they were not required to open |
| A measurement carries the date it was taken | Undated figures invite every later agent to correct them, which costs more than staleness | Agents agreeing on an undated figure across a month |
| Over budget likely means extract or split, and never means trim | The task summaries are among the most useful things here | A workstream held under budget only by deleting history, with nothing lost |
| A live document points at what was archived out of it | Otherwise archiving is how a warning goes dark | An archived warning found reliably with nothing pointing at it |
| Unread material is never marked consolidated | Applies to a skipped scope and to `historical/` alike | — definitional |
| Markers are the only authority to act | Every overreach found so far was an unlicensed upgrade | An agent inferring completion correctly and repeatably |
| One marker per separately-statused fact | Measured overreaches trace to composite markers covering several facts | Composite markers reconciled correctly across passes |
| Frozen tiers are corrected by appending | An edited transcript is no longer a transcript; every doc citing it now quotes something never said | — definitional |
| Shared surfaces are authored upstream first | A local edit guarantees a second divergence — the failure the extraction ended | — definitional |
| Prose in a definition does not fire; a tool with an exit code does | Every measured instance of a rule silently not firing was fixed by moving it into a tool | A rule holding across several passes on prose alone |

Evidence for each: the vault's own maintenance record and `sources/evals/`.

## 6. Standing tensions — open, deliberately

Only what is unresolved. An answered question is not a record; it becomes the design above and leaves here.

- **[OPEN Q] What is the heuristic for "this has stopped bearing on what happens next"?** Partly answered: **a merged
  PR signals that a discrete piece of work completed** — mechanical, dated externally, already tooled. **A heuristic,
  not a rule.** A task carries zero, one or many PRs; the task is the unit and the PR is evidence about it, so a merge
  is authority to *ask* whether a task is closed, never to close it — auto-promotion would be inferring completion.
  Tasks with no PR need no analogue: they close on their own markers and the heuristic does not fire. This vault's own
  work is the zero-PR case, since it is never pushed.
- **[OPEN Q] The budget numbers are guesses.** 12 KB / 16 KB separate today's smallest parent from today's oversized
  ones and nothing more. The eval that would settle them runs against a converted workstream and measures what an
  agent actually loads to open a task.
- **[OPEN Q] Where role tooling should live.** Durable machinery and one-off scripts share one `tools/`, distinguished
  only by what is shared upstream. Co-locating a role's tools with its definition was considered; the constraint is
  that **agent definitions are flat `.md` files symlinked into `~/.claude/agents/`**, whose registry reads `*.md`, so
  an agent becoming a directory stops registering. It also cuts against the assignment: several tools serve every
  role. **Owner's call; the constraint is stated so it can be made with the facts.**
- **Answered — a dump no longer calls the clerk unconditionally** (2026-08-19, owner), decided by the owner rather
  than by the measurement this document said would decide it. The shape: the clerk is owed when a marker moves the
  frontier or `frontier_lag_check.py` reports lag, and a dump that owes one still blocks on it. **The measurement is
  still worth taking** — what remains open is the *rate*, how many dumps actually owe a pass, and that only a
  converted workstream under real use can say. The other variant is untried: running `frontier_lag_check.py`
  **asynchronously** and letting the next session's pass absorb the lag, which trades the guarantee for the whole
  wait rather than gating it.
- **[OPEN Q] Do lists of typed facts beat synthesis?** The tension to design against: **promotion and synthesis pull
  in opposite directions** — promoting preserves register items as a list, synthesising destroys the list on purpose.
  §2 says *when* to promote and *what* to pull; it does not say which of those to reach for.
- **[OPEN Q] Which of a role's required steps earn their round trip.** Correctness requirements land on the most
  frequent operation in the system and each catches something real. The measurement wanted is **per-requirement**.
- **[DEAD END] Attacking a parent agent's blocked time.** Ranked the system's largest problem across three passes and
  it was never a cost: no tokens, children working throughout, fan-out wall clock `max(child) + overhead` by
  construction. Two attempts on record — a polling fix, then incremental merging — and both correctly failed to move a
  number that was never loss. **Do not re-propose** (2026-08-19, owner). The real lever is the **slowest child's
  duration**.
- **Marker spelling is inconsistent vault-wide.** **Evolve toward one form; do not rewrite the past unprompted** —
  sweeping old documents for consistency is slow, frustrating and wasteful. New writing picks the current form, tools
  tolerate both, and anything counting register items must read both.
- **[OPEN Q] Whether workstream-local `design/` docs cut the cost of proving nothing was dropped.** Checking a rewrite
  for silent losses has been expensive in agent time. Splitting reference out into smaller `design/` documents may make
  that check cheap enough to run adversarially at the point of the split. Open, and worth an eval.

## 7. How to read, maintain and develop this document

**Living document, and the place to experiment.** It states the current and desired state of the system and is the
platform for changing either. The mechanisms marked `▢` are untested and their numbers are hypotheses; run them,
measure, and amend here. Amended in place, dated amendments below.

**Every claim carries a marker** so *not built* is visible to a tool rather than buried in prose: `✅` built, `⏳`
partly, `▢` designed but not built, plus `[GATE]` / `[OPEN Q]` / `[DEAD END]` as elsewhere in the vault.

**Not normative** — [[CLAUDE]] and the agent definitions win on any conflict of wording, and encoding a `▢` means
authoring in `dnsco/knowledge-base-template` first. **Vocabulary lags there:** this document says *dump* where the
definitions still say *entry*, until that rename is ported.

**Not a frontier** — a `▢` means *the system is not this shape yet*, not *someone should go do this*. A PR number or a
next-move appearing here means it has become a second frontier.

**Developed through the loop in [[agent-eval-method]]** — author upstream, port, prove no rule was dropped, profile,
feed the findings back. That return edge is the difference between a design that stays true and one that becomes
aspirational.

## Amendments

**2026-08-19 — reframed around partitioning, and the `scout` becomes the asking role.** The driving force is *work
evolves, so context must be partitioned as pieces of it emerge and finish*; a register carrying another task's warnings
is what that failure looks like. The sub-unit becomes a **task**, a dated folder holding its own frontier and dumps.
Detect-and-propose is reassigned to the `scout` on the diagnosis that it never fired because no role's job was asking.
A parent and a task each carry a size budget, which is what makes the sizing question mechanical. Measurements are
dated rather than banned. Every figure and the tool assignment move out, to `sources/evals/`, the vault's own maintenance record and
the vault's tool-assignment doc.

Owner decisions encoded, all 2026-08-19: a blocked parent is not a cost; the parent is an index plus a thin
restated subset plus cross-task invariants; "never restates" is too strong; over budget means probably split, with
extraction as the cheaper alternative; the budget must not restrict what a task pulls in; a merged PR is a heuristic,
not a rule; conversion is lazy and lower priority than the machinery; a task is a dated folder and its frontier is not
separately dated; `historical/` is live, because marking it done loses context; finished workstreams move to
`workstreams/done/`; the sub-unit is a **task**, a register line an **item**, a dated document a **dump**; the
`context-dump` guesses the destination and asks rather than inferring silently; the `scout` owns the sizing, closure
and split questions; the register stays in the parent; this document and [[agent-eval-method]] ship upstream; marker
spelling evolves forward without rewriting the past unprompted.

**2026-08-19 (later the same day) — the machinery exists, and two decisions were reversed.** Phase 1 of the
implementation landed: `agents/scout.md` rewritten around its named briefs and the asking duty, the `context-dump`
skill guessing its destination and asking, a slice mandate for `librarian` / `head-librarian` / `scout`, "entry"
renamed to "dump" across the definitions, and three new checks — `tools/pass_log.py`, `tools/budget_check.py`,
`tools/orientation_check.py`, each with a hand-audited red and green case. Authored in
`dnsco/knowledge-base-template` (c8cde48, 5ef95ee) and ported down; `port_check.py` exit 0, `recall_check.py` run on
every rewritten file in both repos and every flag judged in writing.

Two owner reversals, both taken before the measurements this document said would decide them:

- **One shared pass log, not one per unit.** The per-unit shape cannot answer *what is another agent doing right
  now*, and every role now emits `start` and `stop` records so that it can. §4 carries the reasoning and the cost.
- **The `frontier-clerk` is no longer called on every dump.** It is slow and it stood in front of the most frequent
  action in the system. It runs when a marker moves the frontier or `frontier_lag_check.py` reports lag; a dump that
  owes one still waits. §3 and §6 carry the shape.

**Still unmeasured, and the same number as before:** the relevant fraction. Nothing is converted, so no check here
has fired on a real task and every threshold remains a hypothesis. The first conversion is the eval, not cleanup.

**2026-08-19 (third round, after the first pass) — the number exists, and the mandate that failed.** A full pass
converted one workstream under this design and was profiled. The relevant fraction is **68.3%** across the two
roles (§4), which is the first measurement of the quantity this document exists to move.

Three things the run falsified, each already fixed:

- **A `--section`-only slice mandate is unsatisfiable for a restructure.** The pass ran the tool **zero times**
  and read 137% of a 56 KB note by hand, because its diff had twenty hunks. An unsatisfiable requirement teaches
  an agent to ignore the tool, which is worse than no requirement. `--lines A,B` batched and `--numbered` exist
  now, and the rule is *never page with `sed`*, not *use one mode*.
- **A total-bytes parent budget is unreachable with a resident register.** Converting moved the parent from
  22,921 B to 18,730 B of non-register bytes — an 18% cut — while the total barely moved, because promotions grew
  the register. The budget is now non-register bytes, with the register on a soft mark that asks.
- **The asking duty did not fire on prose.** The definition already said a report raising no question has
  probably failed; the scout returned "Questions for the owner: None" while holding six. What did fire was the
  *schema* — the required `scope_recon` opening ran first, as written. Enforceable shape beats exhortation, again.

**Still open:** whether the gating of the clerk changed anything measurable, and the second conversion.
