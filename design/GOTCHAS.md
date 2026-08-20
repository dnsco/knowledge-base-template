---
type: reference
status: evergreen
tags: [vault, gotchas]
---

# Gotchas

What bites after setup. None of it is visible from inside a session, which is why it is written down.

The first two are about **discipline** and cost you the record itself. The rest are mechanical, and every claim
below was measured rather than assumed.

## 1. A project session may not read this knowledge base's CLAUDE.md — say so explicitly

Claude Code loads `CLAUDE.md` from the current directory, its parents, and `~/.claude/`. A session rooted in a
**code project** therefore loads the *project's* — this knowledge base's `CLAUDE.md` sits in a subdirectory, and
a symlinked one at that, so whether it gets read is a coin flip.

An agent that writes here without it produces exactly what the conventions exist to prevent: an undated
filename, a doc in the wrong tier, chat voice, agent-local codenames ("Option C"), or worst, a **rival
frontier** parked next to the workstream's real one.

Three mitigations. Use all three, because each covers a different hole:

1. The `~/.claude/CLAUDE.md` pointer from bootstrap step 5 — that one every session does load.
2. Invoke `/context-dump` instead of hand-writing docs; the skill carries the conventions and tells the agent to
   read the rest.
3. Say it out loud when the work is substantial: *"read `<vault>/CLAUDE.md` before you write anything."*

Default assumption: if a session did not invoke the skill, it has not read the conventions.

## 2. Reads are free; writes go through the skill, frontier and structure through their own agents

A project session sees `<vault>/` in its tree and treats it like any other directory — it will edit a doc in
place, "tidy" a section that reads as stale, delete what looks obsolete, or rewrite a frontier it has half the
context for. Unlike a bad code change, nothing fails: the record is just quietly worse, and the loss shows up
weeks later as a re-derived dead end.

The discipline, worth stating in the invocation whenever a session will touch the knowledge base:

- **Read freely.** Any session may read and grep it. (As a strong prior, not ground truth — docs are
  point-in-time; verify against the code.)
- **Write only via `/context-dump`** — append a dated entry, and nothing else. Not a hand-edit that
  restructures, and not a frontier edit either.
- **The frontier — `status` flips, striking a completed item: `frontier-clerk` only.** The dump dispatches it in
  the background; it is not something to do by hand on the way past.
- **Delete / merge / archive / close / re-link: librarian only**, as its own deliberate pass, on a clean scope,
  and it has full autonomy inside the scope you give it — including closing a finished task and rolling its
  live residue into a successor. Several workstreams overdue at once, or anything crossing a scope boundary, is
  the `curator`'s.
- **`done/` is append-only, not untouchable.** Never alter what is already written there. A clerk may drain a
  closed item into a dated ledger, and a librarian may archive a whole closed task folder into it and append to
  an existing doc — frozen means the existing record, not the directory.
- Spotted overdue cleanup? **Recommend a librarian pass**; don't do it inline.

## 3. It is a different git repo, and a dirty scope blocks the librarian

Via the symlink, `cd <project>/<vault> && git …` operates on **this** repo, not the project's. Convenient, and
a trap: a turn that touches code and docs leaves commits owed in two repos, and the knowledge-base ones are the
easy ones to forget.

That matters more than tidiness. The librarian **halts on a dirty scope** (its hard rule H) — it cannot
`git show` an uncommitted original, so its carry-forward guarantee does not hold. One forgotten uncommitted doc
in the workstream it is sent to is enough to block the pass. (Dirt *elsewhere* it reports and works around;
a whole-tree halt would hand any session's work-in-progress a veto over every pass.) Commit here in the same
turn you write.

## 4. Search tools do not find it by default

Two independent blocks stack: `.git/info/exclude` hides it from anything honoring git ignore rules, **and** it is
a symlinked directory, which most walkers won't follow. Measured from a project root with the knowledge base
symlinked in:

| command | finds it? | why |
|---|---|---|
| `rg <pat>` | **no** | git exclude |
| `rg --no-ignore <pat>` | **no** | still a symlink |
| `rg --no-ignore --follow <pat>` | yes | both defeated |
| `rg <pat> <vault>/` | yes | explicit path arg overrides both |
| `grep -r` | **no** | `-r` doesn't follow symlinks |
| `grep -R` | yes | `-R` does |
| `find .` | **no** | needs `-L` |
| `find -L .` | yes | |

So an agent told to "search the codebase" will not see the knowledge base, and will not know it missed it.
**Name the path** — `rg 'encabulator' <vault>/` — rather than flipping `--follow` on globally. The default
exclusion is a feature: your notebook should not pollute code searches or land in a PR diff.

## 5. Project worktrees do not have the symlink

`git worktree add` produces a checkout with no untracked files, and the symlink is untracked by design. Measured:
**0 of 7** existing worktrees in a real project had it. A session in a worktree cannot see the knowledge base at
all — including the agent-created worktrees Claude Code uses.

Fix per worktree, with an absolute target since a worktree sits at a different depth and is disposable anyway:

```bash
ln -s ~/workspace/<vault> <vault>
```

If `git status` in that worktree then shows it untracked, add `/<vault>` to its exclude too.

## 6. A librarian pass is slow and expensive — it is a deliberate operation, not a reflex

The append side is cheap: `/context-dump` is a normal end-of-session step. The compacting side is not. A pass
reads the workstream spine itself, fans out a reader per journal doc, `git show`s every original it is about to
merge away, resolves every PR the docs cite, then writes the unified doc **single-threaded on a strong model**
because that is where losslessness is won or lost. That cost buys the guarantee that no single-source gotcha is
dropped.

What follows from that:

- **Never fire it from a hook.** Not a reflexive "tidy the vault" at the end of every session, and never on a
  small model when it will delete docs. Asking for one deliberately, including on a loop you are watching, is
  fine — what is not fine is a pass nobody reads the report of.
- **Never point one librarian at the whole vault.** Several scopes at once is a `curator`, which partitions.
- **Cost scales with scopes, not with documents.** Measured: the marginal work of reading three overlapping
  documents and writing the survivor was ~10% of a single-scope pass; the other 90% is a floor every scope pays
  again — its own system prompt, the conventions, the spine, recon, self-checks, report. So batch documents into
  one scope, and be reluctant about adding scopes. *Small and often* is right about drift and wrong about cost.
- **Judge a scope on shape, not delta.** A zero-file delta is not a proxy for nothing-to-do: the two largest
  restructures of one run had empty deltas, because folder-note size, what sits at the top level and a live
  `status:` inside `design/` are precisely what a delta cannot see. A delta scopes what gets *read*, never what
  may be written into, and it skips the `done/` sweep — so ask for a full pass at phase boundaries. **A full
  pass is also the only thing that renews the licence to skip untouched docs**, since only a full run records a
  `consolidated` baseline and every later delta leans on that.
- **Do not front-load the decisions.** *Detect, propose, execute on approval* produced **zero structural
  proposals across every pass it was assigned to**, in two separate homes; a pass now acts on its own judgement
  inside its scope and hands back a change list with a reversal per entry. Name what is authoritative where the
  docs disagree, and correct the change list afterwards — that is cheaper than a question round trip, and it is
  the only version of this that has ever produced a structural change.
- **Commit first.** A dirty scope halts the pass (§3) — the most common way to spend an invocation and get
  nothing.
