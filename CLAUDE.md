# How to use this knowledge base

**LLM knowledge base for engineering work** — the durable memory Claude Code sessions read from and write back
to, so context outlives the session that produced it. **One knowledge base across every repo I work in**, not
one per project: dated, long-form handoff/working docs. It's an Obsidian vault plus a git repo (hence "vault"
below, and "the graph" for its `[[link]]` structure). It lives at `{{VAULT_PATH}}` and is
symlinked into each project root as `{{VAULT}}/` (local-only, via `.git/info/exclude`), so a session rooted in
a project can read and grep vault docs as in-tree paths. The map of what's here is **[[README]]**; this file is
how to use and maintain it. **[[GOTCHAS]]** is what bites after setup — starting with the fact that a session
rooted in a code project may never have loaded this file.

## Using it — start here
1. Open **[[README]]** — a thin map of what exists and where. Find the workstream you're touching.
2. Open that workstream's folder-note, then the plan-of-record it points to, and **read the top**: the
   frontier gives the goal, the current state, and the next concrete move in a couple of minutes.
3. **Follow companion links only when a task needs the depth** — docs can be large; don't read them all by
   default. Open anything under `done/` only to re-examine completed work, not for current state.
4. **Read docs as a strong prior, not ground truth.** They're point-in-time: file paths, line numbers, and
   "current state" drift. Verify against the actual code before treating a claim as fact.

## Maintaining it

**Two roles — keep them separate.** A working agent (any session doing engineering) **only appends**: capture
findings with the **`context-dump` skill** — a dated journal entry, plus flipping a doc's `status` the moment
work lands or a question settles — and **never** deletes, merges, archives, restructures, or re-links. Those
destructive ops belong to the **`librarian` agent**, run as a separate deliberate pass ("run the librarian" /
"tidy the vault", or at a phase boundary). Concentrating destruction there is what keeps parallel append-only
agents from clobbering each other. Spot overdue cleanup? **Flag it and recommend a librarian pass**; don't do
it inline. The librarian's playbook and hard rules live in its agent definition, not here.

The risky case is a session rooted in a **code project**, which sees this vault as just another directory in its
tree and will happily hand-edit it — see [[GOTCHAS]] §1–2.

**Conventions (per doc).**
- **Placement & filenames** — `grand-plans/` (long-horizon direction), `workstreams/` (active efforts; a named
  one gets a subfolder + a `<folder>/<folder>.md` folder-note as its mini-MOC), `reference/` (subsystem maps
  traced from source, cross-workstream — no status, no next-moves), `values/` (evergreen principles), `done/`
  (finished work), `tools/` (runnable scripts, not notes). Files are `YYYY-MM-DD-topic.md`; evergreen concepts
  and folder-notes skip the date.
- **A mature workstream tends toward three tiers.** *Live* — the folder-note MOC plus exactly **one**
  plan-of-record holding all mutable state (status, gates, PR#s, what's next). *Stable* — a `design/`
  subfolder of still-consulted reference (the "why", as-built design, recipes) that **carries no live
  status**. *Inert* — `done/`, the finished record. The distinction: `done/` is frozen history you open only
  to re-examine completed work; `design/` is living reference a current task leans on. Consolidate toward
  this shape, and keep mutable state single-sourced in the one plan-of-record.
- **Parked (`workstreams/parked/`)** — shared shelf for on-hold efforts (`status: parked`/`deferred`) that may
  revive; distinct from `design/` (settled reference) and `done/` (frozen). A parked doc keeps its `up:`.
- **Long-horizon work gets a stub, not a paragraph.** Work that is real but far off earns its own
  `status: stub` doc plus a frontier line carrying its gates — never prose buried in a journal entry or a
  handoff section. Handoffs get consumed and superseded; a stub with a name survives and accumulates detail.
  Record a baseline measurement in the stub where one exists, so the premise stays checkable later.
- **The README is a thin map** — one line per doc: what it is and which effort it serves. It carries **no
  mutable state**; status, PR numbers, dates and next-moves live only in the workstream's folder-note. Do not
  expand it into an annotated table of contents — that makes it a second frontier that silently drifts out of
  date.
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
- **Commit** — this is its own git repo; commit doc changes in `{{VAULT_PATH}}` (don't conflate with the git of
  whatever repo you're working in). Via the symlink, `cd <project>/{{VAULT}} && git …` resolves to the *vault's*
  repo, not the project's — convenient, and a trap if you forget which one you're in.

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
