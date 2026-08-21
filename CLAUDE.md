# Lipika — the machinery that operates a knowledge-base vault

**This repo is a tool, not a vault.** It holds the agent definitions, the capture skill and the tools
that maintain an external Obsidian-vault-plus-git-repo of long-form engineering docs. The vault lives
somewhere else and is named in config; nothing here hardcodes a path to one.

*Lipika* — Blavatsky's celestial scribes, who inscribe the Akashic records. The vault is the record;
this is the scribe.

## The one rule that shapes everything

**There is exactly one copy of every file here.** This repo used to be a template that a vault copied,
and every change ran a four-step port loop — author upstream, port down, prove no rule was dropped in
both repos, judge the residual divergence — with six files needing hand-ports. That loop is gone.
Author here, once. If you find yourself substituting a placeholder or diffing two copies of a
definition, something has regressed.

The vault reaches these files through `~/.claude/` (symlinks, or a plugin install), so **the machinery
was never read through the vault-as-project** — which is what made the split possible.

## Layout

```
agents/       role definitions — flat .md, because the registry reads *.md and a directory stops registering
skills/       the capture skill; SKILL.md is read from disk at invocation, so edits take effect at once
tools/        runnable python; every one resolves the vault rather than assuming cwd
design/       this machinery's own design docs — the ontology, the eval method, the gotchas
templates/    what a new vault is seeded from, `.template` suffixed so it reads as a template rather than
              as this repo's config. `vault-CLAUDE.md.template` is the corpus half of a vault's
              conventions and points here for the machinery half
ai_docs/      symlink to the vault this is developed against. Local, gitignored
```

`design/vault-and-agent-ontology.md` is the specification — the shape, the forces, and what would
falsify each invariant. `design/agent-eval-method.md` is the procedure for changing and measuring a
role. Read the second before you touch a definition.

## Working on it

**The vault is this project's own memory too.** Its `workstreams/vault-maintenance` carries the record
of how this machinery got here, reachable as `ai_docs/` above. Read it as a strong prior, not ground
truth, and **weigh the age** — a figure from today has not had time to drift.

**Write into the vault only through the sanctioned routes** — the `context-dump` skill to append, the
`frontier-clerk` for frontier state, a `librarian` or `curator` for anything that destroys. Editing vault
documents by hand from a session rooted here is the failure those roles exist to prevent, and it is
easy to do because the vault looks like just another directory in this tree.

**The loop, and it is a loop:** author here → try it on real work → prove no rule was dropped
(`lipika recall-check <pre-change-ref> <path>`, every flag judged in writing, never reword to satisfy one) →
profile it, qualitative read before any figure → summarise the round where the next agent will read it →
feed the findings back. That return edge is the difference between a design that stays true and one that
becomes aspirational.

**Why a tool rather than a careful re-read:** a grep checklist searches for what its author still remembers
keeping, so the one loss it cannot find is the one that matters — a rule the cutter forgot was there.

**Prefer a tool that refuses to prose that asks.** Measured repeatedly: a rule written into a definition
gets read past, and the same rule with an exit code fails loudly. A definition is also a system prompt
paid for on every invocation, so a tool is the cheaper end as well.

**A role that measures the machinery is exempt from the span and byte budgets.** Its subject is another
agent's run rather than the corpus, so a cap buys a cheaper profile by reading less. `eval-profiler` has
recorded passes in the pass log and **no definition on disk** — it runs as an ad-hoc brief against
`design/agent-eval-method.md`, and it owes one. The pass log has no `eval` kind yet, so such a run files itself
as an operating one.

## Landmines

- **A definition change is served stale for a few minutes.** Rewrite `agents/*.md` and spawn that role
  immediately and the *old* text runs, with nothing in the transcript saying which version it was. Probe
  with a question the two versions answer differently before profiling anything. `SKILL.md` is exempt.
- **A sub-agent in an unexpected tree reports clean.** Worktree isolation is retired (2026-08-20) — the
  partition and the pass log do that job — but the failure it was catching outlives it: a tree at a
  different commit still computes a delta that still looks clean. Harness isolation is the sharpest case,
  cutting from an `origin/main` this vault never pushes. So **every sub-agent given a base ref checks
  `git rev-parse HEAD` against it first**, and no agent in a shared checkout ever changes HEAD.
- **The `Edit` tool needs its own `Read`.** A slice read through Bash does not satisfy the guard, so the
  first `Edit` fails. Read the ten lines around your anchor rather than re-reading the file — and do not
  route around the guard with in-place scripts, which trades auditability for a call.
- Everything else that bites, measured: `design/GOTCHAS.md`.

## Voice

Terse and factual, for a first-time reader. No agent-local codenames — say what a thing *is*, not the
label it got mid-session. **Harder for anything that leaves the conversation** — PR bodies, commit
messages, review replies carry the salient facts and none of the conversational frame. Commit subjects
under 72 characters, and end messages with:

```
Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
```
