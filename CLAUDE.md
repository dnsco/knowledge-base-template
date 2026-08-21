# Lipika — the machinery that operates a knowledge-base vault

**This repo is a tool, not a vault.** It holds the two capture skills, the agent definitions and the
tools that maintain an external Obsidian-vault-plus-git-repo of long-form engineering docs. The vault
lives somewhere else and is named in config; nothing here hardcodes a path to one.

*Lipika* — Blavatsky's celestial scribes, who inscribe the Akashic records. The vault is the record;
this is the scribe.

**You are almost certainly here to change the machinery, not to use it.** Using it is two skills —
`pickup` and `context-dump` — and they explain themselves. What follows is how to develop them.

## What the machinery believes

One rule, and everything else follows from it: **every document in the vault is a record or a view.**

- **A record is never edited.** Dumps, `reference/` traces, `sources/`, `external/`, and every
  orientation already written. A record is corrected by a newer document, never by a change to it.
- **A view is regenerated wholesale, never patched.** Each thread's current orientation, and the vault
  index. Safe to rewrite from scratch precisely because the records behind it are intact.
- **`architecture/` is the owner's** — the one long-lived edited view. Agents produce the traces behind
  it and contradict it with them; they do not write it.

The design, with the forces and the falsifiers: `design/vault-and-agent-ontology.md`. Its §8 is the list
of what this system used to do and why each piece is gone — **read it before re-proposing anything**,
because most obvious ideas here have already been built, measured and retired.

## Layout

```
agents/       role definitions — flat .md, because the registry reads *.md and a directory stops registering
skills/       pickup and context-dump; SKILL.md is read from disk at invocation, so edits take effect at once
tools/        runnable python; every one resolves the vault rather than assuming cwd
design/       this machinery's own design docs — the ontology, the eval method, the gotchas
templates/    what a new vault is seeded from, `.template` suffixed
ai_docs/      symlink to the vault this is developed against. Local, gitignored
```

## Reaching the vault from here

**Never write a path to it.** `vault_config` resolves it — flag, then `$LIPIKA_VAULT`, then
`~/.config/lipika/config.json`, then the checkout — and it **refuses rather than guessing**, because a
tool that guesses its target curates the wrong tree and reports success. It returns a `Vault`, whose
existence is the proof it is one; `.path` is the string.

```bash
cd "$(lipika vault-config path)"     # every tool takes --vault as an override
lipika vault-config show
lipika doctor                        # is everything wired
```

**Call every tool by name — `lipika <command>`.** A plugin's `bin/` is on `PATH`;
`${CLAUDE_PLUGIN_ROOT}` is **empty** in a subagent's shell, measured, so a definition that interpolates
a path fails at its first call in the role least able to explain why.

**The vault is this project's own memory too**, and the machinery's own record lives in it. Read it as a
strong prior, not ground truth, and **weigh the age** — a figure from today has not had time to drift.

**Write into it only through the skills.** `pickup` on the way in, `context-dump` on the way out. Editing
vault documents by hand from a session rooted here is easy, because the vault looks like just another
directory in this tree, and it is how a record stops being evidence of a moment.

## Developing the machinery

**There is exactly one copy of every file here.** This repo used to be a template that a vault copied,
and every change ran a four-step port loop. That loop is gone. If you find yourself substituting a
placeholder or diffing two copies of a definition, something has regressed.

**The loop, and it is a loop:**

1. **Author here**, once.
2. **Probe behaviourally.** Never ask a role to quote its own definition — one did exactly that and
   returned a rule that has never existed in any version of the file, in any repo. Ask a question the two
   versions *answer differently*.
3. **Try it on real work**, then profile it: `lipika agent-transcript`, qualitative read before any
   figure. A size is not a finding.
4. **Summarise the round where the next agent will read it**, and feed the findings back. That return
   edge is the difference between a design that stays true and one that becomes aspirational.

`design/agent-eval-method.md` is the procedure in full. Read it before you touch a definition.

**`lipika recall-check <pre-change-ref> <path>` proves a rewrite dropped no rule.** Its subject is a
definition here, not a vault document — nothing in the vault is edited, so nothing there needs it. **It
is not the way to check a deliberate deletion**: a pass whose purpose is removing rules flags every one
of them, and judging a hundred intended retirements in writing is a great deal of work for no signal.
There, the deletions are the deliverable and `git diff` is the record.

**Prefer a tool that refuses to prose that asks.** A rule in a definition gets read past; the same rule
with an exit code fails loudly. A definition is also a system prompt paid on every invocation, so the
tool is the cheaper end too. **Give every new check a hand-audited red case and a green case** — a check
that stays red on correct content gets dismissed, and one that stays green on a real fault is worse.

## Landmines

- **A definition change is served stale for a few minutes.** Rewrite `agents/*.md` and spawn that role
  immediately and the *old* text runs, with nothing in the transcript saying which version it was. Probe
  before profiling. `SKILL.md` is exempt — it is read from disk at invocation.
- **A new skill needs a symlink.** `~/.claude/skills/<name> -> <repo>/skills/<name>`, or it never
  registers. Same for `~/.claude/agents/<name>.md`. Deleting a definition means deleting its symlink too.
- **A sub-agent in an unexpected tree reports clean.** A tree at a different commit still computes a
  delta that still looks clean. Every sub-agent given a base ref checks `git rev-parse HEAD` against it
  first, and **no agent in a shared checkout ever changes HEAD** — creating a branch moves it for every
  session in that tree.
- **A sub-agent inherits your cwd while every tool resolves the *configured* vault.** Dispatching from a
  worktree makes a pass read one tree and index another.
- **The `Edit` tool needs its own `Read`.** A slice read through Bash does not satisfy the guard.
- **`git push` over SSH fails here while `gh` is authenticated.** Push with
  `git -c credential.helper='!gh auth git-credential' push https://github.com/dnsco/lipika.git <branch>`.
- Everything else that bites, measured: `design/GOTCHAS.md`.

## Voice

Terse and factual, for a first-time reader. No agent-local codenames — say what a thing *is*, not the
label it got mid-session. **Harder for anything that leaves the conversation** — PR bodies, commit
messages and review replies carry the salient facts and none of the conversational frame. Commit subjects
under 72 characters, and end messages with:

```
Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
```
