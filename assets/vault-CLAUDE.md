# How to use this knowledge base

**LLM knowledge base for engineering work** — the durable memory Claude Code sessions read from and write back
to, so context outlives the session that produced it. **One knowledge base across every repo I work in**, not
one per project: dated, long-form handoff/working docs. It's an Obsidian vault plus a git repo (hence "vault"
below, and "the graph" for its `[[link]]` structure). It is symlinked into each project root under its own name (local-only, via `.git/info/exclude`), so a session rooted in
a project can read and grep vault docs as in-tree paths. The map of what's here is **[[README]]**; this file is
how to use and maintain it. **[[GOTCHAS]]** is what bites after setup — starting with the fact that a session
rooted in a code project may never have loaded this file.

## Using it — start here
1. Open **[[README]]** — a thin map of what exists and where. Find the workstream you're touching.
2. Open that workstream's folder-note and **read the top**: the frontier gives the goal, the
   current state, and the next concrete move in a couple of minutes.
3. **Follow companion links only when a task needs the depth** — docs can be large; don't read them all by
   default. Open anything under `done/` only to re-examine completed work, not for current state.
4. **Read docs as a strong prior, not ground truth.** They're point-in-time: file paths, line numbers, and
   "current state" drift. Verify against the actual code before treating a claim as fact. **That caveat is about
   drift, so weigh the age** — a weeks-old line number earns a check; a dump written today has not had time to
   go stale.

## Maintaining it

**This is not an exhaustive record, and absence is not a gap.** The goal is not to track everything —
it is to keep what a future session actually needs. Do not propose sweeps to capture every artifact,
channel or shipped document for completeness' sake; a thing earns a place here because someone will
need it, not because it exists.

**Append is free; editing is what needs a check.** Adding a dump, appending to `done/`, appending a dated note
to `sources/` or `external/` — nothing can be lost by adding, so nothing gates it. **Editing a live document
needs a check, and the bar is semantic: keep every fact, and reword or merge redundant ones freely so long as
meaning is preserved.** What must never happen is a fact becoming unfindable. `recall_check.py` is the gate and
every flag is judged **in writing** — "reworded, fact intact" is an acceptable answer, a missing fact is not, and
you never reword a file to satisfy a flag.

**Roles — five of them, and only the dump is synchronous.** A working agent (any session doing engineering)
**only appends**: capture findings with the **`context-dump` skill** — a dated **dump** inside the live task,
plus emitting the marker that flips a doc's `status` the moment work lands or a question settles — and **never**
deletes, merges, archives, restructures, or re-links. Everything else runs in the background:

- **The `frontier-clerk`** reconciles one frontier against the dumps, and must be very cheap in tokens and time.
  It runs when a dump carries a state-changing marker, or when `frontier_lag_check.py` reports the frontier
  already lagging — not on every dump. A purely additive dump says *no clerk pass owed* and names the check it
  ran; judging it unnecessary is not a licence to make the clerk's edits yourself. The dump **dispatches** it and
  does not block on it, and says so rather than claiming a reconciled frontier.
- **The `librarian`** is the only role that destroys, and it works **one scope** — a task, a workstream or a
  grand plan — with **full autonomy inside it, bounded by losslessness rather than permission**: consolidate,
  reword, merge, split the workstream, split and merge tasks, archive finished ones, spin finished material out
  as its own task or workstream and move it to `done/`, sort `historical/`, convert. It does not ask; it reports
  a change list. Run it as a separate deliberate pass, or at a phase boundary. Spot overdue cleanup? **Flag it
  and recommend a pass**; don't do it inline.
- **The `curator`** is the role for *the vault feels messy*. It owns which scopes exist and everything crossing
  a boundary — fanning out one `librarian` per scope, merging their branches, repointing links across scopes,
  correcting a claim another scope's work falsified, normalizing a convention applied inconsistently, fusing two
  workstreams that are one effort — plus `README.md`, `CLAUDE.md` and the memory pointer, which nothing else
  writes. It never rewrites a document's substance. **One or two scopes overdue is a `librarian`, not a
  curator:** adding a scope costs a whole pass floor.
- **The `scout`** goes ahead read-only and returns findings and a recommendation with the inputs behind them,
  carrying named briefs — `orientation`, `sizing`, `closure`, `recon`. Its context is discarded on return, so its
  reads cost the caller only the answer. Send one rather than doing its reading in the context you need to keep.

**Act, then report for correction** — not ask, then act. Structural changes are made on the agent's best
judgement and returned as a **change list**: every move, merge, reword and split, one line each, with how to
reverse it. *Detect, propose, execute on approval* produced zero proposals in two separate homes. What still goes
to the owner rather than into the diff is the small set that is not cheaply reversible — inventing or renaming a
top-level folder, relocating a grand plan, an engineering decision.

**Why the roles are split is time management, not judgement.** Dumping agents that also tidied the vault got
sidetracked onto vault corrections and ate the working task's context. Keeping housekeeping off the working
session's clock is the point. What keeps parallel background passes off each other's files is the shared pass log
below, not a partition of who may write what. Each role's playbook lives in its own definition, not here.

**Roles that measure the machinery are a different class**, and the budgets above do not apply to them: a
profiling or eval run's subject is another agent's run rather than the corpus, and capping it buys a cheaper
profile by reading less.

The risky case is a session rooted in a **code project**, which sees this vault as just another directory in its
tree and will happily hand-edit it — see [[GOTCHAS]] §1–2.

**Conventions (per doc).**
- **Placement & filenames** — `grand-plans/` (long-horizon direction), `workstreams/` (active efforts; a named
  one gets a subfolder + a `<folder>/<folder>.md` folder-note as its mini-MOC), `reference/` (subsystem maps
  traced from source, cross-workstream — no status, no next-moves), `values/` (evergreen principles), `done/`
  (finished work), `sources/` (raw verbatim inputs, subdivided by kind — `sources/transcriptions/`),
  `external/` (artifacts written for an outside audience), `tools/` (runnable scripts, not notes). Files are
  `YYYY-MM-DD-topic.md`; evergreen concepts and folder-notes skip the date. **`topic` names the work, not its
  state** — this bites hardest in `done/`, where every document is by definition landed and closed, so a name
  saying so distinguishes nothing and a reader hunting one closure has to open all of them. Take the theme at a
  glance and spend no thought on it: **a rough name beats a generic one**, and a generically-named `done/` doc
  is a `librarian`'s to rename on the next pass.
- **`sources/` and `external/` are read-only — correct them by appending, never by editing.** `sources/` holds
  raw verbatim inputs (meeting and session transcripts, clipped articles); a transcript that has been edited is
  no longer a transcript, and every doc citing it now quotes something that was never said. `external/` holds
  artifacts already delivered to an audience; editing one retroactively makes the record disagree with what
  people actually received. When either carries a claim that has since gone stale, **append a dated note** saying
  so and leave the original text intact — the same move `done/` already allows.
- **A workstream's sub-unit is a task**, because work evolves and context has to be partitioned as pieces of it
  emerge and finish. A task is a dated folder that closes:

  ```
  workstreams/<ws>/
    <ws>.md                    parent — task index + a thin restated subset + cross-task invariants. No date
    YYYY-MM-DD-<task>/         a live task
      <task>.md                its frontier — its own gates and PR numbers while live. Not dated
      YYYY-MM-DD-<topic>.md    dumps written during it
    historical/                LIVE, not done — unsorted pre-conversion context
    done/YYYY-MM-DD-<task>/    closed tasks, per workstream. The retrieval surface
    design/                    stable reference, no live status
  ```

  *Terminology the vault spends: a **task** is that sub-unit, a line in a register is an **item**, a dated
  document written during a task is a **dump**.* **One frontier per live task** — a second live copy of any
  mutable state has to be hand-synced and diverges. The parent points by default: it restates only the coarsest
  state and the warnings that bear on *every* task, and **the register stays in it** rather than moving to a
  document agents must be told to open, which is how a warning stops firing. `historical/` is live because
  marking it done claims consolidation over material nobody has read. *Stable* — a `design/` subfolder of
  still-consulted reference that **carries no live status**; *inert* — `done/`, frozen history you open only to
  re-examine completed work.
- **Conversion is lazy, and there is no migration project.** A workstream converts when it is next touched, by
  the `librarian` pass that is already operating it: its last few tasks split out as dated folders, everything
  else folded into `historical/`. A workstream created after this design needs no conversion and no `historical/`.
- **A parent and a task each carry a byte budget, checked by a tool** — because "thin" in prose does not fire and
  a size in an exit code does:
  ```bash
  lipika budget-check workstreams/<ws>     # exit 1 over target, exit 2 over the signal
  ```
  Parent 12 KB / 16 KB, task 8 KB / 12 KB — **hypotheses, calibrated against one corpus and nothing else.** Over
  budget means **extract** reference-not-warning material to `reference/` or `design/`, or **split** a parent
  that is two efforts wearing one name. It **never** means trimming the task index or deleting history; a unit
  held under budget that way has failed the check it appears to pass. **Nor may the budget restrict what a task
  pulls forward** — a check that makes an agent carry less context has done harm. **Splitting a workstream is
  the `librarian`'s to execute and report**, like any other structural change; a **grand plan**, and inventing
  or renaming a top-level folder, are the owner's.
- **A task pulls forward what bears on it when it opens** — the still-live GATEs, LANDMINEs, DEAD ENDs and
  settled decisions from the workstream's closed tasks and `historical/`, into a `## Carried across` section of
  its frontier, each cited by source. Selection is paid once, by whoever knows what the task is about.
  ```bash
  lipika orientation-check workstreams/<ws>/YYYY-MM-DD-<task>/   # exit 2 = no pull
  ```
  Nothing carries *up* on close, and the pull is what makes that safe: without it, promotion to `done/` is how a
  live warning goes dark quietly.
- **Parked (`workstreams/parked/`)** — shared shelf for on-hold efforts (`status: parked`/`deferred`) that may
  revive; distinct from `design/` (settled reference) and `done/` (frozen). A parked doc keeps its `up:`.
- **Long-horizon work gets a stub, not a paragraph.** Work that is real but far off earns its own
  `status: stub` doc plus a frontier line carrying its gates — never prose buried in a dump or a
  handoff section. Handoffs get consumed and superseded; a stub with a name survives and accumulates detail.
  Record a baseline measurement in the stub where one exists, so the premise stays checkable later.
- **The README is a thin map** — one line per doc: what it is and which effort it serves. It carries **no
  mutable state**; status, PR numbers, dates and next-moves live only in the workstream's folder-note. Do not
  expand it into an annotated table of contents — one that did became a second frontier and silently drifted
  out of date.
- **One shared pass log, and every role announces itself in it.** `pass-log.jsonl` at the vault root — untracked,
  append-only, one file for the whole vault so an agent can see what the others are doing right now:
  ```bash
  lipika pass-log active --scope workstreams/<ws>    # who is in here
  lipika pass-log start <role> "<one line>" --scope <s> --kind <k>
  lipika pass-log stop <role> "<what you did>" --result <r>
  ```
  Emit a `start` before you write and a `stop` when you finish — the pair is what keeps parallel agents off each
  other's files. It replaced git-tag anchors, which are **dead**: nothing reads or writes one, and none were
  imported (2026-08-19, owner). A record carries the HEAD sha, so the next pass still has something to diff from. **Only a full run's
  `--result consolidated` establishes a baseline**; deltas stack, and a scope you skipped is recorded `skipped`,
  never consolidated — "not looked at" must not be spelled the same way as "already handled".
- **Frontmatter** — keep `type` / `status` / `date` / `tags` current (plus `up` / `links` for tier relationships).
- **Links** — `[[wikilinks]]` for intra-vault references; leave code-repo paths as literal text. Docs span
  repos, so **name the repo** when a path is ambiguous — `acme-server: docs/…`, not a bare `docs/…`.
- **Voice** — terse and factual, written for a first-time reader: cut chat-context and rationale-noise, keep
  the reasoning future-you will need, and use **no agent-local codenames** ("Option C", "Track B", workflow
  IDs) — say what a thing *is*, not the label you gave it mid-session.
- **The same voice, harder, for anything that leaves the conversation** — PR bodies, review replies, commit
  messages, issue comments. Laconic, terse, salient, and carrying **no leaked frames**: no "correcting my
  last comment", no "as discussed", no account of which files you did and did not open. A fresh observer was
  not in the room, and the artifact outlives the exchange. See [[laconic-terse-salient]].
- **An owner's account of what happened outranks your inference about it.** They were there; you have
  artifacts. When a measurement contradicts what they told you — especially a flat statement, or anything
  recorded today — **surface the conflict and stop**: say what you saw, ask which to record, and leave the
  record alone until they answer. Never rewrite a frontier or a memory note on your own inference about events
  you did not witness. The usual cause is measuring a **different quantity** than the claim: an image existing
  in a registry is not a deployed tag, and a merge time is not a rollout time. Read hedges as instructions —
  "I think" invites a check, a flat statement is the answer — and verification costs a turn, so it needs a
  reason: would the answer change your next action? This is **not deference**: silently swallowing a real
  contradiction is the same failure as silently overturning one. Say it once, plainly, either way.
- **Commit** — this is its own git repo; commit doc changes in this vault (don't conflate with the git of
  whatever repo you're working in). Via the symlink, `cd <project>/<vault> && git …` resolves to the *vault's*
  repo, not the project's — convenient, and a trap if you forget which one you're in.

## Changing the machinery — it does not live here

The agent definitions, the capture skill and the tools are **not in this vault**. They live in Lipika
(`github.com/dnsco/lipika`), installed as a Claude Code plugin, and there is exactly one copy of each.
Nothing is shared-by-copy with this vault and nothing is ported into it.

**So: never hand-edit a definition, a skill or a tool from a session rooted here.** Author it in Lipika,
where the loop is: author → try it on real work → `lipika recall-check <pre-change-ref> <path>` to prove
no rule was dropped, every flag judged in writing → profile it, qualitative read before any figure →
write the round's summary where the next agent will read it → feed the findings back. That last edge is
what makes it a loop rather than a pipeline.

What this vault holds is the **corpus** — the documents. What Lipika holds is the machinery that maintains
them, plus its own design docs.

**Where the two meet.** Tools are called by name (`lipika <command>`) because a plugin's `bin/` is on
`PATH`; the vault's location comes from `~/.config/lipika/config.json`, which also carries the size and
span budgets the tools enforce. **A number lives in the config, not in this document** — restating a
threshold here is how it goes stale while a tool quietly enforces something else. That happened: this
file advertised a parent budget of 12 KB / 16 KB long after the tool had superseded it with 8 KB / 12 KB
against non-register bytes. Run `lipika vault-config show` for what is actually in force.

**The lesson behind all of it.** Instructions added to a definition repeatedly fail to fire, while a
script with an exit code holds. Measured across one session: a scope-screening condition shipped
unsatisfiable and nobody noticed until it was used; "dispatch a scout if recon runs past a handful of
commands" did not fire across fourteen recon commands; and an agent told to prefer the Obsidian CLI never
checked whether it was answering about the right tree. Each was fixed by moving the rule into a tool,
where it fails loudly instead of being read past. **Prefer a tool that refuses to prose that asks.** It
is also the cheaper end: a definition is a system prompt paid for on every invocation.

## Values — `values/`
Evergreen principles that outlive any one effort, and that the docs here lean on by name. Two are seeded:

- **[[parse-dont-validate]]** — push constraint-checking into types at the boundary: return a refined type that
  carries the proof, not a `bool` that throws the knowledge away. Make illegal states unrepresentable.
- **[[laconic-terse-salient]]** — anything read by someone who was not in the room (PR body, review reply,
  commit message, code comment) carries the salient facts and none of the conversational frame.

Add to this folder when a principle starts getting restated across docs — that's the signal it's evergreen and
belongs in one place under a name others can link to.

## Bundled skills — `obsidian-skills/`
The official Obsidian Agent Skills (`kepano/obsidian-skills`) ship as a git submodule, each symlinked into
`~/.claude/skills/` so they're invocable as slash-commands (`/obsidian-cli`, …) from **any** session — including
one rooted in a code project, which is where you usually are. `git submodule update --remote` upgrades it;
`git submodule update --init` after a fresh clone, or the symlinks dangle.

- **obsidian-cli** — vault ops from the CLI. **Use it for renames/moves** — it keeps inbound `[[links]]`
  intact — and for vault-wide search.
- **defuddle** — web page → clean markdown. Use instead of WebFetch for non-`.md` URLs.
- **obsidian-markdown** — Obsidian-flavored markdown when writing notes here.
- **obsidian-bases** (`.base` views over notes) and **json-canvas** (`.canvas` visual maps).
