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
plan-of-record** parked next to the real one.

Three mitigations. Use all three, because each covers a different hole:

1. The `~/.claude/CLAUDE.md` pointer from bootstrap step 5 — that one every session does load.
2. Invoke `/context-dump` instead of hand-writing docs; the skill carries the conventions and tells the agent to
   read the rest.
3. Say it out loud when the work is substantial: *"read `{{VAULT}}/CLAUDE.md` before you write anything."*

Default assumption: if a session did not invoke the skill, it has not read the conventions.

## 2. Reads are free; writes go through the skill, destruction through the librarian

A project session sees `{{VAULT}}/` in its tree and treats it like any other directory — it will edit a doc in
place, "tidy" a section that reads as stale, delete what looks obsolete, or rewrite a frontier it has half the
context for. Unlike a bad code change, nothing fails: the record is just quietly worse, and the loss shows up
weeks later as a re-derived dead end.

The discipline, worth stating in the invocation whenever a session will touch the knowledge base:

- **Read freely.** Any session may read and grep it. (As a strong prior, not ground truth — docs are
  point-in-time; verify against the code.)
- **Write only via `/context-dump`** — append a dated entry, flip a `status`. Not a hand-edit that restructures.
- **Delete / merge / archive / re-link: librarian only**, as its own deliberate pass, on a clean tree.
- **Never touch `done/`.** It is frozen.
- Spotted overdue cleanup? **Recommend a librarian pass**; don't do it inline.

## 3. It is a different git repo, and a dirty tree blocks the librarian

Via the symlink, `cd <project>/{{VAULT}} && git …` operates on **this** repo, not the project's. Convenient, and
a trap: a turn that touches code and docs leaves commits owed in two repos, and the knowledge-base ones are the
easy ones to forget.

That matters more than tidiness. The librarian **halts on a dirty tree** (its hard rule 6) — it cannot `git show`
an uncommitted original, so its carry-forward guarantee does not hold. One forgotten uncommitted doc is enough to
block the next pass. Commit here in the same turn you write.

## 4. Search tools do not find it by default

Two independent blocks stack: `.git/info/exclude` hides it from anything honoring git ignore rules, **and** it is
a symlinked directory, which most walkers won't follow. Measured from a project root with the knowledge base
symlinked in:

| command | finds it? | why |
|---|---|---|
| `rg <pat>` | **no** | git exclude |
| `rg --no-ignore <pat>` | **no** | still a symlink |
| `rg --no-ignore --follow <pat>` | yes | both defeated |
| `rg <pat> {{VAULT}}/` | yes | explicit path arg overrides both |
| `grep -r` | **no** | `-r` doesn't follow symlinks |
| `grep -R` | yes | `-R` does |
| `find .` | **no** | needs `-L` |
| `find -L .` | yes | |

So an agent told to "search the codebase" will not see the knowledge base, and will not know it missed it.
**Name the path** — `rg 'encabulator' {{VAULT}}/` — rather than flipping `--follow` on globally. The default
exclusion is a feature: your notebook should not pollute code searches or land in a PR diff.

## 5. Project worktrees do not have the symlink

`git worktree add` produces a checkout with no untracked files, and the symlink is untracked by design. Measured:
**0 of 7** existing worktrees in a real project had it. A session in a worktree cannot see the knowledge base at
all — including the agent-created worktrees Claude Code uses.

Fix per worktree, with an absolute target since a worktree sits at a different depth and is disposable anyway:

```bash
ln -s ~/workspace/{{VAULT}} {{VAULT}}
```

If `git status` in that worktree then shows it untracked, add `/{{VAULT}}` to its exclude too.

## 6. A librarian pass is slow and expensive — it is a deliberate operation, not a reflex

The append side is cheap: `/context-dump` is a normal end-of-session step. The compacting side is not. A pass
reads the workstream spine itself, fans out a reader per journal doc, `git show`s every original it is about to
merge away, resolves every PR the docs cite, then writes the unified doc **single-threaded on a strong model**
because that is where losslessness is won or lost. That cost buys the guarantee that no single-source gotcha is
dropped.

What follows from that:

- **Never automate it.** Not a hook, not `/loop`, not a reflexive "tidy the vault" at the end of every session.
- **Never point it at the whole vault**, and never run it on a small model when it will delete docs.
- **Small and often beats big and rarely.** One workstream, at a phase boundary. Cost scales with the **delta
  since the last pass** — each pass tags the vault, and the next one reads only what changed — so frequent
  passes get cheap while a neglected workstream gets expensive. Nine docs and four same-day journals is a big
  pass; two or three docs is a quick one.
- **A delta pass is not a full one.** It scopes what gets *read*, never what may be written into, and it skips
  the `done/` sweep. Ask for a full pass at phase boundaries; that is also the only thing that renews the
  licence to skip untouched docs.
- **Front-load the decisions.** It is required to stop and ask on structural moves (merging or splitting whole
  workstreams, relocating a doc across them, collapsing two plans-of-record). Every question handed back costs
  another pass, so pre-answer the ones you already know and name what is authoritative where docs disagree.
- **Commit first.** A dirty tree halts the pass outright (§3) — the most common way to spend an invocation and
  get nothing.
