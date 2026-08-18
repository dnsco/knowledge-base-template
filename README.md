# knowledge-base-template

Seed for an **LLM knowledge base**: durable cross-session memory for engineering work — a git repo + Obsidian
vault that Claude Code sessions write long-form handoff docs into, plus the two agents that keep it from rotting.

**One knowledge base, N code repos** — not one per project. It lives beside your project checkouts and is
symlinked into each project root (excluded locally via `.git/info/exclude`, so it never lands in a teammate's
tree or a PR diff). A workstream is a thread of *work*, which routinely spans several repos.

Setup: **[BOOTSTRAPPING.md](BOOTSTRAPPING.md)**. Conventions once bootstrapped: **[CLAUDE.md](CLAUDE.md)**. What
bites afterwards — above all, a project-rooted session that never read those conventions and hand-edits the
record anyway: **[GOTCHAS.md](GOTCHAS.md)**. "Vault" throughout is the Obsidian term for the same thing.

## Why a knowledge base, and why two roles

A session's context dies with the session. This is where it survives — dated working docs a cold session can
orient from in two minutes. The problem with agents writing docs is not writing; it's **rot**: N sessions each
add a doc, the same mutable state (status, PR#s, "what's next") gets restated in five places, and four copies go
stale.

The fix is a split, and it's the whole design:

| | writes | never |
|---|---|---|
| **`context-dump` skill** — any session doing engineering | a dated journal entry, and nothing else | the frontier; deletes, merges, archives, restructures, re-links |
| **`frontier-clerk` agent** — spawned by the dump | frontier state only: `status` flips, marker moves, striking items whose completion is recorded | moving content between docs; inferring completion; tagging |
| **`librarian` agent** — a separate deliberate pass | structure within one workstream: consolidates overlapping docs into its one folder-note, archives finished work, fixes the `[[link]]` graph | engineering decisions; inferring that something is done |
| **`head-librarian` agent** — several workstreams at once | shared surfaces, commits, anchor tags | any doc's substance; taxonomy calls |
| **`scout` agent** — read-only reconnaissance | nothing at all | — |

Each boundary is a **capability, not a request for restraint**: the appending agent *cannot* rewrite, so the
illegal state is unrepresentable rather than checked for afterwards. Working agents being append-only is what
lets any number run in parallel without clobbering each other, and concentrating all destruction in the
librarian — alone, with full context, at a phase boundary ("run the librarian" / "tidy the vault") — is what
keeps the record safe to write to from many sessions and still small enough to read.

## What's in the box

```
CLAUDE.md                    the operating manual — read by every session rooted here
GOTCHAS.md                   what bites after setup; measured, not assumed
README.md                    (this file; replaced by your knowledge base's map at bootstrap)
BOOTSTRAPPING.md             setup
skills/context-dump/         the append-only capture skill
agents/librarian.md          the compacting agent
agents/frontier-clerk.md     reconciles a frontier against a dump's entry, and writes nothing else
agents/head-librarian.md     orchestrates one librarian per scope, in isolated worktrees, when
                             several workstreams are overdue at once — rare; prefer the librarian
agents/scout.md              read-only reconnaissance; reports, writes nothing
tools/                       the librarian's verification tools: verify_pr_markers.py (batch
                             PR-state check), recall_check.py (did a rewrite drop a rule),
                             frozen_tier_check.py (was frozen-tier substance altered),
                             dangling_links.py (which [[links]] resolve to nothing)
values/                      two seeded evergreen principles: parse-dont-validate, laconic-terse-salient
grand-plans/<demo>/          folder-note + depth doc — the grand-plan shape; delete it
workstreams/<demo>/          folder-note (map + frontier) + done/ — the full workstream shape; delete it
obsidian-skills/             submodule: kepano/obsidian-skills (obsidian-cli, defuddle, …)
reference/ done/             empty tiers, see below
```

Two placeholders — `{{VAULT}}` (the vault's directory name) and `{{VAULT_PATH}}` — are filled in at bootstrap.

## The structure it grows into

Sorted by **rate of change**, not by topic. That's the one idea to keep:

- **`workstreams/<name>/`** — an active multi-session effort. Its `<name>.md` **folder-note** *is* the plan of
  record: map and single frontier in one file, the only place mutable state lives — status, gates, PR numbers,
  what's next, and one typed `Risks, gates & landmines` register. One frontier per workstream, no second copy
  anywhere; there is no separate plan doc, because a workstream with one has two frontiers waiting to diverge.
- **`workstreams/<name>/design/`** — still-consulted reference that no longer moves: the "why", as-built
  design, recipes. Carries no status.
- **`done/`** — finished and frozen. Opened only to re-examine completed work, never for current state.
- **`sources/`** and **`external/`** — read-only: raw verbatim inputs, and artifacts already delivered to an
  audience. Correct either by appending a dated note, never by editing.
- **`workstreams/parked/`** — shared shelf for on-hold efforts that may revive.
- **`grand-plans/`** — the long-horizon direction the workstreams serve.
- **`reference/`** — subsystem maps traced from source, cross-workstream. Kept so agents re-read instead of
  re-tracing.
- **`values/`** — evergreen principles that outlive any effort, linkable by name from any doc.
- **`tools/`** — runnable scripts an agent can call, not notes.
- **`README.md`** — a **thin map**: one line per doc, what it is and which effort it serves. No status, no PR
  numbers, no dates. The moment it grows annotations it becomes a second frontier and starts drifting.

Docs are `YYYY-MM-DD-topic.md`, wired with `[[wikilinks]]`; frontmatter carries `type` / `status` / `date` /
`tags` / `up`. Full rules in [CLAUDE.md](CLAUDE.md).
