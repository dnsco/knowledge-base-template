---
type: reference
status: reference
date: 2026-08-19
tags: [vault, meta, agents, roles, tools, contracts]
---

# The agents, one at a time — what each does, what governs it, what it runs

A per-role reference. For each role: what it is for, the rules that actually govern it, and the tools it must reach
for with their contracts. Cross-role tools are at the end.

**Companion, different cut.** [[vault-and-agent-ontology]] holds the *design* — the document shape, why the write
boundaries sit where they do, and what is not built yet. This file holds the *role-by-role operating detail*.
the vault's tool-assignment doc holds invocations and the project-specific scripts no role runs. On any conflict of wording, [[CLAUDE]] and the
agent definitions in `agents/` win; both of these are reference.

**Marker vocabulary**, as elsewhere: `✅` built and in force, `⏳` partly, `▢` designed but not built.

## The one rule every role shares

**Never infer completion. A marker is an agent's only authority to act.** The characteristic failure here is not
fabrication — it is **distinction-collapse, always toward upgrade**: *failed* read as *never requested*, *encoded* as
*discharged*, *settled* as *settled-and-executed*, a parent marked done because most of its children were.

Two corollaries that decide arguments:

- **One marker per separately-statused fact.** A composite marker covering four facts is the single largest measured
  cause of a clerk overreaching.
- **Settled is not executed.** A decision made is not work done, and the two licence entirely different actions.

## `context-dump` — the skill that appends

A skill, not an agent: it runs in the main loop, so its reads are the session's reads and it has no transcript.
⏳ **The only role never profiled**, for that reason.

**What it does.** Writes one dated dump into the live task capturing what happened, the evidence-bearing markers, the
risks/gates/landmines block, and the reusable commands. Then dispatches the `frontier-clerk` **if the dump changes
frontier state**, and waits for it.

**Governing rules.**
- **Append only.** It may not touch a frontier — not a `status` flip, not striking a next-move it just finished.
- ✅ **It calls the clerk only when a dump changes frontier state** (2026-08-19, owner) — a state-changing marker,
  or `frontier_lag_check.py` reporting the frontier already lags. A purely additive dump reports *no clerk pass owed*
  **and names the check it ran**: "the check said clean" is verifiable later and "I judged it unnecessary" is not.
- **When one is owed it must not report success until the clerk returns.** A dump that reports done before the clerk
  lands leaves a stale frontier behind a success message, which is the silent failure the split exists to prevent.
  Gating *which* dumps pay for a clerk is the fix; skipping the wait on one that owes it is not.
- **Emit a marker for every owner decision**, dated and attributed, including ones taken in conversation. The clerk
  may act only on markers in the dump; an unwritten decision costs a second round trip.
- **Never hand the clerk a paraphrase.** Frontier lines are state plus a pointer.
- **Never hand the clerk a mutable measurement to transcribe.** Cite the reference and let a tool answer the number.
- ✅ **Guess the destination and ask.** The most recently edited task in the most recently edited workstream is the
  guess; the owner confirms or redirects. Never infer silently, never interrogate. Ask the closure question too.
- ✅ **Announce the pass and close it** — `pass_log.py start … --kind dump` before writing, `stop --result
  incremental` after committing. A dump never consolidates anything and the tool refuses the claim.
- ✅ **Never convert a workstream as a side effect.** Conversion is the `librarian`'s; a dump into an unconverted
  workstream goes to the root and says so.

**Tools.**

| tool | contract |
|---|---|
| `frontier_lag_check.py <workstream>` | has the plan-of-record fallen behind its own dumps? **exit 0** no signals · **exit 1** signals, read them and decide whether a clerk pass is owed · **exit 5** bad invocation. This is now the gate on calling the clerk at all |
| `orientation_check.py <task>` | does a new task cite what it reviewed? **exit 0** cited · **exit 1** cited but a `done/` or `historical/` goes unmentioned — judge it · **exit 2** no section or nothing cited: the pull did not happen · **exit 5** bad invocation |
| `pass_log.py start|stop` | announce and close the dump. `start` **exit 1** = a concurrent pass overlaps your scope, read it before writing |

## `frontier-clerk` — the register keeper

Spawns nothing, so its wall clock is entirely its own work. ✅ **The two-minute-per-operation ceiling is this role's**
and no other's; a fan-out pass is `max(child) + overhead` and was never a candidate.

**What it does.** Reconciles a frontier against a dump just written — **the task's frontier by default**, the parent
only when a marker is genuinely cross-task: flips a `status`, strikes a next-move whose
completion is recorded, demotes an in-flight line a landed one supersedes, reorders within a list, and promotes a
closed item into the workstream's dated `done/` ledger.

**Governing rules.**
- **Acts strictly off the dump's markers.** It never infers completion and never decides that something is done.
- **May create and append to `done/`; may never rewrite existing text there.** That is the frozen-tier rule with one
  narrow licence.
- **Never moves or merges documents, never rewrites prose for quality, never records a pass as consolidated.**
  Those are the librarian's or nobody's.
- **Never rolls a parent item up over a live child.** Measured: it refused this three times in one round and named the
  reason each time. Correct behaviour, do not "fix" it.
- **Verify content survives before promoting it** — in the new dump, or in `done/`. That is the whole difference
  between tidying and losing the record.
- ✅ **Slice, do not read whole.** The mandate is what moves its load, not the tool existing: with it, ~22% of a 54 KB
  frontier; without it, ~92% of a 44 KB one.
- ✅ **Cite a `frontier_slice.py` line number for every changed line.** Naming the tool did not make it reach for it;
  requiring the citation did.
- ✅ **Default is task-local.** Promoting a task-local fact to the parent is the upgrade-direction collapse this
  system reliably fails at, and it is a `librarian`'s call or the owner's, never the clerk's.
- ✅ **Stop rather than race a live `librarian` pass.** `pass_log.py start` exit 1 names the overlap; a librarian
  mid-restructure is the one agent that can make the clerk's anchors vanish under it.

**Tools.**

| tool | contract |
|---|---|
| `frontier_slice.py <note> --section '<name>'` | the mutable part of a plan-of-record without the prose. `--find PATTERN --context N` replaces `sed` paging; `--stats` sizes it. Reads **both** marker spellings. Requirement: never read a frontier whole |
| `marker_licence_check.py <dump> <note> [--base A..B] --vault <path>` | did the edit claim more than the dump licenses? **exit 0** nothing to answer for · **exit 1** unlicensed-upgrade reports, read and judge · **exit 2** a self-contradiction or rollup — defects, not judgement calls · **exit 5** bad invocation |
| `verify_pr_markers.py <owner/repo#N> [N …]` | state, `mergedAt` and merge commit per cited PR in one GraphQL request. Refuses a bare number without `--repo` rather than guess. An ISSUE row does **not** set the exit code. **A bare `#N` is a shell comment** — quote refs or everything after the first is swallowed |
| `frontier_lag_check.py` | as above |
| `orientation_check.py` | as above |
| `pass_log.py` | `start --kind clerk` before editing, `stop --result incremental` after. Exit 1 on `start` = someone else is in this file |

## `librarian` — structure, and the only role that destroys

**What it does.** A deliberate curation pass over one workstream: consolidates overlapping notes into the one
plan-of-record, promotes finished work to `done/`, repairs the `[[link]]` graph, surfaces forward-useful `done/`
material, and syncs the map. ▢ It also sorts `historical/` out into `done/` over time, which no pass has done yet
because nothing has a `historical/`.

**Why destruction is concentrated here.** It is what lets append-only agents run in parallel without clobbering each
other. Every other role's restraint depends on this one existing.

**Governing rules.**
- **Curates only.** Never edits engineering code, never makes an engineering decision.
- **Never infers completion** — acts strictly on explicit done-markers.
- **Never decides a taxonomy alone.** Detect, propose, execute on approval.
- **Never starts on a dirty tree.** Uncommitted files break `git show` carry-forward and cannot have their links
  repointed, silently voiding two core steps.
- **Diff the originals before consolidating.** Measured losses come from merging without reading what is being merged.
- **Renames go through the Obsidian CLI**, which keeps inbound links intact. A hand-rename with eight inbound pointers
  breaks eight documents.
- **Frozen tiers — `done/`, `sources/`, `external/` — take an appended dated note, never an edit.** An edited
  transcript is no longer a transcript, and every document citing it now quotes something never said.
- ⏳ **Refusal is correct behaviour and is on record.** A sub-librarian declined to promote 25 dead ends — the larger
  half by bytes, and what a literal reading of its mandate asked — citing two of the owner's own rulings. Do not
  optimise that away.
- ✅ **Slice mandated** as of 2026-08-19, and unmeasured here — it does the deepest reads in the system, so this is
  where the mandate has the most to move. Most of a pass is floor rather than merge work.
- ✅ **It is the mechanism that converts a workstream.** Conversion is lazy: last few tasks out as dated folders,
  everything else into a **live** `historical/`, `done/` per workstream, the register left in the parent.

**Tools.**

| tool | contract |
|---|---|
| `recall_check.py <pre-change-ref> <path>` | did a rewrite silently drop a rule? **exit 0** clean · **exit 1** flagged, judge every one. `--mode all --threshold 0.25` for prose, `--into <survivor>` when content moved. **Requirement: never reword a file to satisfy a flag** |
| `obsidian.py` | vault query or a refusal, never a wrong answer. The link-preserving route for renames and moves |
| `dangling_links.py <vault-root> [memory-dir]` | which `[[links]]` resolve to nothing. **exit 1** if any dangle. Separates the three false-positive classes; the memory-dir argument is optional and only classifies memory-note links |
| `assert_isolated.py <base>` | first command in any worktree — see cross-role below |
| `frontier_slice.py` | mandated as of 2026-08-19: `--section` first, `--stats` before any whole read |
| `budget_check.py <ws>` | **exit 2** = over the signal, so extract or split — never trim the index. Prints the largest sections |
| `pass_log.py baseline\|start\|stop` | the anchor, the announcement, and the record of what a pass established |
| `orientation_check.py <task>` | **exit 2** = a new task cited nothing it reviewed |

## `head-librarian` — coordination, and it curates nothing

Despite the name this is not the senior librarian; it is the one that does no shelving.

**What it does.** Screens and partitions scope, spawns one sub-librarian per scope in its own worktree, then does what
none of them can: merges their branches, applies cross-scope link repoints, corrects claims that went false in another
agent's files, syncs the shared surfaces, runs the invariant checks, and commits.

**Governing rules.**
- **Never curates a document itself. Never makes a taxonomy or engineering call.**
- **A pass is not over until every spawned scope has returned or been accounted for.** ⏳ **Regressed once after being
  fixed** — an orchestrator said it would wait and then returned, costing a full context resume. It owned this plainly:
  *"saying I would wait is not waiting."* Third data point that prose does not hold across runs; **live and
  unmitigated in prose.**
- **Two scopes in one invocation run sequentially, never in parallel** — both write the shared map and the memory
  pointer, so parallel passes clobber each other. Partitioning by path and having the orchestrator own the shared files
  is the workaround.
- **A scope a pass skipped is never recorded as consolidated.** That converts "not looked at" into "already handled",
  and the licence to skip rests on the claim being true.
- **A delta pass must never scope its *writes* to the delta.** Reading only changed documents leaves a new dump
  un-merged into an untouched frontier while the pass reports success.
- **Only use several scopes when several workstreams are genuinely overdue.** For one workstream invoke the `librarian`
  directly — **adding a scope costs a whole floor**, and the floor is most of a pass.
- ✅ **Send a `scout` in first**, with its briefs named — `recon` always, `sizing` and `closure` when the run may
  restructure or close anything — and answer what it brings back.
- ✅ **Slice mandated** (2026-08-19, unmeasured).
- ✅ **Open a pass-log record per scope before the spawn, with `--parent` set**, and close every one at the end —
  including the scopes it skipped, which are recorded `skipped` and never `consolidated`.

**Tools.**

| tool | contract |
|---|---|
| `pass_invariants.py <base-ref>` | every end-of-pass check in one call, run once. **exit 0** clean, skips reported not hidden · **exit 1** an invariant failed — read the section, do not re-run hoping · **exit 5** bad invocation. Reports SKIPPED rather than failed when the index refuses inside a worktree, which is correct there |
| `frozen_tier_check.py <base-ref>` | did a pass alter substance in a frozen tier, or only repoint and append? **exit 0** checked and clean · **exit 1** a SUBSTANCE or DELETED verdict · **exit 2** your filter matched nothing, so nothing was checked. **Exit 2 exists because the tool shipped reporting "nothing changed" nine times having read no diff.** Pass frozen **file** paths, never a directory |
| `scope_manifest_validate.py <manifest> <branch>` | does a sub-agent's structured return match the branch it wrote? **exit 0** holds, UNVERIFIED reported not hidden · **exit 1** an assertion failed · **exit 5** bad invocation or unparseable. Unknown keys are preserved and reported, never rejected |
| `vault_commit.py -m "…" -- <paths>` | refuses a bare commit and a half-rename. **exit 0** committed · **exit 2** a rule refused it, message says which · **exit 3** nothing under those pathspecs · **exit 5** bad invocation |
| `dangling_links.py`, `recall_check.py` | as above |
| `budget_check.py <ws>` | is a parent or task over budget, and so due extraction or a split? **exit 2** = over the signal |
| `pass_log.py` | `start` per scope with `--parent`, `stop` per scope after the merge. The record carries the HEAD sha the next pass diffs from |

## `scout` — it looks, it asks, it writes nothing

**What it does.** Surveys one workstream and returns a distillate. Its context is **discarded** on return, so the
sifting costs the caller nothing but the answer. ✅ It carries **named briefs** rather than one job:

- **orientation** — read the closed tasks and `historical/`, return the warnings bearing on a task about to open.
- **sizing** — is this task or parent over budget.
- **closure** — which tasks look done.
- **recon** — the mechanical facts about a scope: anchors, deltas, inventories, frontmatter, the link graph.

**Governing rules.**
- **Writes nothing. Curates nothing. Proposes no taxonomy. Answers none of its own questions.** It asks; the owner
  answers. ✅ **Including the pass log** — it *reads* the log and reports who else is on the ground, and the
  dispatching role is the one that appends. The write-nothing boundary is worth more than the record of a read-only
  survey.
- ✅ **It is the asking role, and that is the point.** Detect-and-propose produced zero split proposals across every pass
  it was assigned to — not an authority gap but the fact that **nobody's job was asking**, and a duty competing with
  the work in front of an agent loses. Any role may dispatch a scout; a full run always does.
- ✅ **No sixth role was added for orientation.** A role for a duty that already has an owner pays a whole pass floor to
  fix a missing brief.
- ⏳ **Its mandatory dispatch has never fired.** Encoded, unexercised — 14 recon commands ran in a context that had to
  survive to reconciliation, with no scout sent.
- ✅ **Open its report with `scope_recon.py`'s raw output.** Naming the tool did not make it reach for it.
- ✅ **Slice mandated**, with one carve-out: the `orientation` brief reads closed-task bodies, because there reading
  *is* the job.
- ✅ **Two mandatory report sections**: `## Questions for the owner` and `## Not looked at`. A report raising no
  question has almost certainly failed, and an announced gap costs the caller one command where a silent one reads
  as a clean result.

**Tools.**

| tool | contract |
|---|---|
| `scope_recon.py <scope> […]` | every mechanical fact about a set of scopes in one call. Replaced 20–30 forensic calls. Does not emit refs the verifier aborts on |
| `assert_isolated.py <base>` | first command if isolated — see below |
| `budget_check.py <ws>` | the `sizing` brief. **exit 1** over target · **exit 2** over the signal → extract or split, never trim · **exit 5** bad invocation. Prints the largest sections, so *what to extract* comes from the same call |
| `pass_log.py active --scope <s>` | who else is on this ground. Read-only for this role |
| `frontier_slice.py` | mandated, as for the clerk |

## Cross-role tools

### `assert_isolated.py <base>` — every sub-agent's **first** command

**exit 0** isolated (or `--allow-main`) and `HEAD == base` and tree clean · **exit 2** not in a worktree · **exit 3**
HEAD is not the base you were given · **exit 4** working tree dirty · **exit 5** bad invocation or not a git repository.

**Why it is the most valuable tool in the set.** `isolation: "worktree"` cuts from `origin/main`, and this vault is
deliberately never pushed, so `origin/main` is a hundred-plus commits stale and **every harness-isolated sub-agent
lands in a tree where recent work does not exist**. Deterministic, and the gap grows with every commit. Two
sub-librarians caught this as their first command in one round and reset before writing; one reported a folder-note 22
KB smaller than the one it was sent to edit. Uncaught, it curates a tree in which most of its material does not yet
exist and reports clean.

**Requirement:** provision with `git worktree add … <base>` when it halts. Do not repair by reading the shared
checkout — refusing to do that is correct behaviour and is on record.

### Porting a shared surface

`CLAUDE.md`, `GOTCHAS.md`, `README.md`, `agents/*.md`, `skills/*`, `tools/*.py` and `reference/*` (the vault-machinery
ones — this document, [[vault-and-agent-ontology]] and [[agent-eval-method]]) are shared with
`dnsco/knowledge-base-template`, which is **upstream**. Author there first; a vault-side edit guarantees a second
divergence, which is the failure the extraction exists to end.

| tool | contract |
|---|---|
| `port_check.py --vault <v> --template <t>` | **exit 0** no placeholders, residue printed for review · **exit 2** an unsubstituted placeholder survived — hard fail, because an agent otherwise reads a literal placeholder in its own system prompt · **exit 3** bad invocation or nothing to compare. **Deliberately not a byte-identity check**: the vault names real repos, shas and dated evidence where the template stays generic, so diffing to zero destroys the part meant to differ |
| `port_file.py <path>` then `--apply` | copies down, reporting what it would flatten. **`--apply` is a wholesale copier and will flatten deliberate divergence** — it would have deleted 18 lines of project-specific wording from one skill and 19 from one tool. Dry-run, read the loss list, hand-port anything real |
| `placeholders.py` | the placeholders defined once and imported by every tool that ports or checks a port. Imported, not invoked |

### `agent_transcript.py` — read another agent's run without reading it

| command | contract |
|---|---|
| `--list [--cwd PATH]` | every session under that project slug and its subagent transcripts, newest first, with sizes, agent types, and a LIVE marker on anything still being appended. **A worktree session has its own slug**, so `--cwd` is how you reach it |
| `<agent-id>` | calls, per-tool byte totals, and cost with the traps applied — peak `cache_read` never a sum, `cache_creation` reported separately and never added, newlines rendered ` <NL> ` because collapsing them to `|` fabricates pipelines |
| `<agent-id> --calls --min-bytes N` · `--grep PATTERN` | the expensive reads; whether a mandated tool actually fired |

Bytes returned per call is the **denominator** of a relevant-fraction measurement. The classification — load-bearing
/ duplicated / never used — is judgement and stays with the profiler.

### `recall_check.py` — the check that earns its keep

Run it in **both** repos for every rewritten file. In one design rewrite it caught four real drops, including a trap
recorded nowhere else in the vault. **Judge every flag; never reword a file to satisfy one** — and a "moved to X"
claim is a claim about X, so verify X actually received it.

### ✅ The pass log — one file, and every role announces itself in it

`tools/pass_log.py`, appending to `pass-log.jsonl` at the vault root. **One shared log, not one per unit** (reversed
2026-08-19, owner): the question it exists to answer is *what is another agent doing right now*, and answering that
from N logs is not answering it. Untracked, because N worktrees appending to a tracked file conflict every pass.

| command | contract |
|---|---|
| `start <role> "<desc>" [--scope S] [--kind K] [--parent ID]` | prints the pass id, which you keep. **exit 1** = a concurrent open pass overlaps your scope — judge it before writing. `--parent` keeps an orchestrator's own run from reading as a conflict with its children |
| `stop <role> "<desc>" [--result R]` | `consolidated` \| `incremental` \| `skipped` \| `aborted`. Records `span_s`, `commits` and `files_changed` **itself**, from git — an agent composing figures by hand is the expensive way to get a worse number, so there is no metric flag. Per-call figures come from `agent_transcript.py`. **exit 2** = a defect, not a judgement call: a non-full pass claiming `consolidated`, a stop with no start, a double stop |
| `active [--scope S]` | open passes, with age, and STALE on any older than `--stale-hours` (default 4) — an agent that died, not one still working |
| `baseline [--scope S]` | the last `consolidated` full run, its HEAD sha as the delta anchor, and the deltas since. **exit 1** = no baseline, so the pass is necessarily full |
| `history [--scope S]` | what the recent passes did, and when |

What it keeps claiming, now enforced rather than asked: **a full run's record means consolidated**, **deltas stack**
(the tool refuses `consolidated` from a delta), and **a skipped scope is recorded `skipped`, never consolidated**. A
record carries the HEAD sha, so rewriting history orphans every anchor.

**The one failure mode is an unclosed `start`**, and it fails safe: another agent backs off unnecessarily. Every role
closes what it opened, including scopes it skipped.

## Two tool-design rules the set was built on

- **Prefer a tool that refuses to prose that asks.** Measured: a scope-screening condition shipped unsatisfiable and
  went unnoticed until used; a mandatory dispatch did not fire across fourteen recon commands; an agent told to prefer
  the Obsidian CLI never checked whether it was answering about the right tree; a verifier reported "nothing changed"
  nine times having read no diff. Every one was fixed by moving the rule into a tool with an exit code. It is also the
  cheaper end — a definition is a system prompt paid on every invocation.
- **A check that stays red on correct content gets dismissed.** A fourth marker-licence rule was tried and **removed**
  at 1 true positive against 3 false. Do not re-add a rule without per-item locality, and give every new check a
  hand-audited red case and green case.
