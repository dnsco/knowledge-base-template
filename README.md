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
| **`context-dump` skill** — any session doing engineering | appends a dated journal entry; flips `status`; keeps the one live frontier truthful | deletes, merges, archives, restructures, re-links |
| **`librarian` agent** — a separate deliberate pass | consolidates overlapping docs into the one plan-of-record, archives finished work, fixes the `[[link]]` graph, syncs the map | engineering decisions; inferring that something is done |

Working agents are **append-only**, so any number of them can run in parallel without clobbering each other.
All destruction is concentrated in the librarian, which runs alone, with full context, at a phase boundary
("run the librarian" / "tidy the vault"). That's what makes the record safe to write to from many sessions and
still small enough to read.

## What's in the box

```
CLAUDE.md                    the operating manual — read by every session rooted here
GOTCHAS.md                   what bites after setup; measured, not assumed
README.md                    (this file; replaced by your knowledge base's map at bootstrap)
BOOTSTRAPPING.md             setup
skills/context-dump/         the append-only capture skill
agents/librarian.md          the compacting agent
tools/verify_pr_markers.py   batch PR-state check — the librarian verifies done-markers with it
values/                      two seeded evergreen principles: parse-dont-validate, laconic-terse-salient
grand-plans/<demo>/          folder-note + depth doc — the grand-plan shape; delete it
workstreams/<demo>/          folder-note + plan-of-record + done/ — the full workstream shape; delete it
obsidian-skills/             submodule: kepano/obsidian-skills (obsidian-cli, defuddle, …)
reference/ done/             empty tiers, see below
```

Two placeholders — `{{VAULT}}` (the vault's directory name) and `{{VAULT_PATH}}` — are filled in at bootstrap.

## The structure it grows into

Sorted by **rate of change**, not by topic. That's the one idea to keep:

- **`workstreams/<name>/`** — an active multi-session effort. Contains a `<name>.md` **folder-note** (its
  mini-map) and exactly **one plan-of-record**: the single place mutable state lives — status, gates, PR
  numbers, what's next, and one typed `Risks, gates & landmines` register. One frontier per workstream, no
  second copy anywhere.
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
