# Bootstrapping a knowledge base from this template

Ten minutes, mostly symlinks. `<vault>` below is your vault's directory name — pick something boring and
specific (`acme-docs`, `platform-notebook`).

**One vault for all your work, not one per project.** It lives as a **sibling of your project checkouts**
(`~/workspace/<vault>` next to `~/workspace/<project>`) and gets symlinked into each project root in step 5.
Sibling placement is what makes those symlinks relative, so they survive moving `~/workspace`.

## 0. Prereqs

- **Claude Code** — the skill and agent are wired in as symlinks under `~/.claude/`.
- **git**, **python3**, and **`gh`** authenticated (`gh auth status`) — `tools/verify_pr_markers.py` shells out
  to `gh api graphql`.
- **Obsidian** (optional). Nothing requires it, but the `obsidian-cli` skill talks to a running Obsidian and is
  the only way to rename/move a note while keeping inbound `[[links]]` intact.

## 1. Make your repo

Clone the template with its submodule, then point it at your own remote:

```bash
git clone --recurse-submodules https://github.com/dnsco/knowledge-base-template.git ~/workspace/<vault> && cd ~/workspace/<vault> && git remote remove origin
```

Cloning (rather than copying the directory) is what keeps the `obsidian-skills` submodule wired up. If you'd
rather start with no history: copy the tree, `rm -rf .git .gitmodules obsidian-skills`, `git init`, then
`git submodule add https://github.com/kepano/obsidian-skills.git obsidian-skills`.

## 2. Fill in the two placeholders

`{{VAULT_PATH}}` — the vault path agents will paste into shell commands (`~/workspace/<vault>`; keep it
shell-usable, so `~` not `$HOME`). `{{VAULT}}` — just the directory name (`<vault>`), which is also the symlink
name step 5 creates in each project root.

```bash
grep -rl '{{' --include='*.md' --exclude-dir=obsidian-skills --exclude=BOOTSTRAPPING.md --exclude=README.md . | xargs perl -pi -e 's|\Q{{VAULT_PATH}}\E|~/workspace/<vault>|g; s|\Q{{VAULT}}\E|<vault>|g'
```

Then prove none are left — this should print nothing:

```bash
grep -rn '{{' --include='*.md' --exclude-dir=obsidian-skills --exclude=BOOTSTRAPPING.md --exclude=README.md .
```

Placeholders live in `CLAUDE.md`, `skills/context-dump/SKILL.md` and every file in `agents/` — including their
frontmatter `description:`, which is what Claude Code matches on to decide whether to invoke them. An
unreplaced placeholder there degrades triggering, so don't skip the check.

## 3. Wire the skill and agents into Claude Code — at **user** level

```bash
mkdir -p ~/.claude/skills ~/.claude/agents && ln -s ~/workspace/<vault>/skills/context-dump ~/.claude/skills/context-dump && for a in ~/workspace/<vault>/agents/*.md; do ln -s "$a" ~/.claude/agents/; done
```

**User level (`~/.claude/`), not the vault's `.claude/`** — you invoke `context-dump` and the librarian from a
session rooted in the *code* repo, not from a session rooted in the vault. Symlinks rather than copies, so the
one you edit is the one that runs and every change is versioned in the vault.

If you'd rather not make them global, symlink them into the code repo's `.claude/skills/` and `.claude/agents/`
instead. Anything that only works when you happen to be rooted in the vault is the wrong place.

## 4. Wire the Obsidian skills in too — same user level

```bash
for s in ~/workspace/<vault>/obsidian-skills/skills/*/; do ln -s "${s%/}" ~/.claude/skills/"$(basename "$s")"; done
```

Five symlinks: `obsidian-cli`, `obsidian-markdown`, `obsidian-bases`, `json-canvas`, `defuddle`. User level rather
than the vault's own `.claude/skills/`, for the same reason as step 3 — you reach the knowledge base from a session
rooted in a *code* project, and `obsidian-cli` is the only link-preserving way to rename a note. Scoping it to the
vault would put it exactly where you aren't.

After a fresh clone without `--recurse-submodules`, run `git submodule update --init` or all five dangle.

## 5. Symlink the vault into every project you work in

```bash
cd ~/workspace/<project> && ln -s ../<vault> <vault> && printf '/%s\n' '<vault>' >> .git/info/exclude
```

Repeat per project — one vault, N symlinks. Three details carry the weight:

- **`.git/info/exclude`, not `.gitignore`.** The exclude is local and never committed, so your knowledge base
  stays out of a teammate's tree and out of PR diffs. Anchor it (`/<vault>`) so it only matches the root.
- **Relative target (`../<vault>`)**, so the link survives moving or renaming `~/workspace`.
- **Why bother when the vault already has an absolute path:** a session rooted in the project can then read and
  grep its docs as in-tree paths — no out-of-tree access prompt — and a plain `ls` shows the knowledge base is
  there. Note that `cd <project>/<vault> && git …` operates on the **vault's** repo, not the project's.

Then make sure sessions know to look. One line in `~/.claude/CLAUDE.md` covers every project at once:

> Engineering handoff docs live in `~/workspace/<vault>` — its own git repo, symlinked into each project root as
> `<vault>/`. Orient from its `README.md` before starting multi-session work, and read its `CLAUDE.md` before
> writing anything there. Capture findings with the `context-dump` skill; never hand-edit, restructure or delete
> its docs.

That last clause is the one that earns its keep — a session rooted in a code project treats the knowledge base as
just another directory. `GOTCHAS.md` §1–2 covers why, and what to say when it matters.

## 6. Replace README.md with your vault's map

This template's `README.md` describes the template. Overwrite it with the thin map — one line per doc, and
**no** status, PR numbers, or dates (those live in each workstream's folder-note, and a README that carries
them becomes a second frontier that silently drifts):

```markdown
---
type: moc
status: active
tags: [vault, index]
---

# <vault> — knowledge base map

What lives here and where. **[[CLAUDE]]** is the operating manual: conventions, the
append-vs-librarian split, and the bundled skills. **[[GOTCHAS]]** is what bites after
setup.

**This map carries no state.** Status, PR numbers and next-moves live only in each
workstream's folder-note — go there for "where are we".

## Workstreams
Active multi-session efforts, in `workstreams/`. A named one has a folder plus a
`<folder>/<folder>.md` folder-note that holds its frontier.

- (nothing yet — the first `context-dump` will add one)

## Grand plans
Long-horizon direction the workstreams serve, in `grand-plans/`.

## Reference
Subsystem maps traced from source, in `reference/`. No status, no next-moves.

## Reusable assets
- `values/` — evergreen principles: [[parse-dont-validate]], [[laconic-terse-salient]].
- `tools/` — runnable helpers: `verify_pr_markers.py` (batch PR-state check), `recall_check.py` (did a doc
  rewrite drop a rule).
- `skills/` — vault-authored skills symlinked into `~/.claude/skills/`: `context-dump`.
- `obsidian-skills/` — bundled Obsidian Agent Skills, also symlinked into `~/.claude/skills/`.
  See [[CLAUDE]] for what each is for.

## Shelves
- `done/` — finished work, frozen. Open only to re-examine something completed.
- `workstreams/parked/` — on-hold efforts that may revive.
- `sources/` — raw verbatim inputs (transcripts, clipped articles). Read-only.
- `external/` — artifacts written for an outside audience. Read-only once delivered.
```

**Then delete the two demo folders.** `grand-plans/fix-some-fundamental-architecture/` and
`workstreams/re-encode-quantum-encabulator/` are worked examples of the shapes described above — a folder-note
that is both the map and the single frontier, carrying the typed `Risks, gates & landmines` register, and a
`done/` entry with an evidence-bearing marker. Read them once, then
drop them: left in place they give every future session a fake workstream to trip over.

```bash
git rm -rq grand-plans/fix-some-fundamental-architecture workstreams/re-encode-quantum-encabulator
```

## 7. Commit

```bash
git add -A && git commit -m "seed vault from knowledge-base-template"
```

The seed commit is the one time a blanket add is fine. After this, stage specific files — `git add -A` in a
repo with a submodule is how you accidentally commit a dirty `obsidian-skills` pointer.

## 8. Verify

Start Claude Code **in a code project**, not in the vault — everything is wired at user level, so that is the
real test. You should see `context-dump` plus the five Obsidian skills in the skills list, and `librarian` among
the agents. Then check the tool works end to end against any PR you can read:

```bash
python3 tools/verify_pr_markers.py <owner>/<repo>#<n>
```

One row, `state MERGED|OPEN|CLOSED`. `MISSING` means the PR number is wrong, not that the tool is broken; an
`ISSUE` row means the doc cited a tracking issue as a PR.

## 9. First real use

- **End of a work session, in the code repo:** "dump context" → the skill writes
  `workstreams/<name>/YYYY-MM-DD-topic.md`, creating the workstream if it's new, and updates the frontier.
- **At a phase boundary:** commit the vault (a dirty tree halts the pass by design), then "run the librarian on
  `<workstream>`". Tell it what's authoritative and pre-answer any taxonomy calls you already know — each
  question it has to hand back costs another pass. Details in `agents/librarian.md`.

## 10. Upkeep

```bash
git submodule update --remote obsidian-skills
```

Commit the resulting pointer bump. Everything else is the librarian's job.
