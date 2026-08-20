# Lipika

Agents and tools that maintain a **knowledge-base vault** — an Obsidian-vault-plus-git-repo of dated,
long-form engineering docs that Claude Code sessions write to and read back, so context outlives the
session that produced it. One vault spans every project you work in.

*Lipika* — the celestial scribes who inscribe the Akashic records. The vault is the record; this is the
scribe.

**This repo is not a vault.** It holds the machinery; the vault lives wherever you keep it and is named
in config. Nothing here hardcodes a path to one.

## Install

```bash
/plugin marketplace add dnsco/lipika
/plugin install lipika
```

Then tell it where your vault is:

```bash
mkdir -p ~/.config/lipika && cat > ~/.config/lipika/config.json <<'JSON'
{
  "default": "notes",
  "vaults": { "notes": "/absolute/path/to/your/vault" }
}
JSON
lipika vault-config show
```

The config also carries the thresholds the tools enforce — size budgets, per-role time budgets, which
directories are append-only — so a number has one home instead of being restated in prose that goes
stale. Every command resolves the vault the same way: `--vault`, then `$LIPIKA_VAULT`, then the config,
then the checkout you are standing in. **A command that cannot resolve a vault refuses rather than
guessing**, because a tool that guesses its target curates the wrong tree and reports success.

`lipika doctor` says whether the wiring is intact — the two halves resolve differently, so it checks them
separately.

## Set up a vault

A vault is a git repo of markdown, readable as an Obsidian vault. It needs one document at its root saying how
its documents are placed, named and maintained:

```bash
cp templates/vault-CLAUDE.md.template /path/to/your/vault/CLAUDE.md
```

That template carries the **corpus half** — placement, filenames, frontmatter, voice, and what the byte budgets
are for. It points here for the machinery half and for every threshold's value, because a rule restated in two
places diverges and a number restated in prose goes stale while a tool enforces something else.

A vault's copy diverges on purpose: it should name your real repos, your dated evidence, your concrete shas.
**Edit the template here; never port a copy back.**

## The roles

Five, and only the first is synchronous — the rest run in the background so housekeeping stays off the
working session's clock.

| role | what it may do |
|---|---|
| **`context-dump`** (skill) | appends a dated entry. Cannot touch the plan of record |
| **`frontier-clerk`** | owns one plan of record's state: flips a status, strikes a finished item, drains a closed one |
| **`librarian`** | structure inside **one** scope, with full autonomy there — merge, split, archive, re-link — bounded by losslessness rather than by permission |
| **`curator`** | anything crossing a scope boundary, plus the shared surfaces no scope owns |
| **`scout`** | reads and reports. Writes nothing, and its context is discarded on return |

Each acts and then reports a change list with a reversal per entry, rather than asking first —
detect-propose-execute-on-approval produced zero proposals in two separate homes.

## The tools

```bash
lipika                 # every command, with what it does
lipika budget-check <path>
lipika recall-check <ref> <path>     # did a rewrite silently drop a fact?
lipika pass-log active               # who else is working in this vault right now
```

They are reached by name because a plugin's `bin/` is on `PATH`. `${CLAUDE_PLUGIN_ROOT}` is **not**
populated in a subagent's shell — measured — so no definition here interpolates a path.

## Changing a role

One copy of every definition, skill and tool exists, so authoring is the whole of it. The loop:

**author here → try it on real work → `lipika recall-check <pre-change-ref> <path>` → profile it → summarise the
round where the next agent will read it → feed the findings back.** Every recall-check flag is judged in writing,
and you never reword a file to satisfy one. That last edge is what makes it a loop.

Two things bite immediately. **A definition change is served stale for minutes** and the agent registry caches at
session start, so probe with a question the old and new text answer differently before trusting any measurement —
`SKILL.md` is exempt, being read from disk at invocation. And **`${CLAUDE_PLUGIN_ROOT}` is empty in a subagent's
shell**, measured, so no definition may interpolate a path; that is why tools are called by name.

`CLAUDE.md` here is the working guide for this repo. `design/` carries its own documents:
`vault-and-agent-ontology.md` (the shape, the forces, and what would falsify each invariant),
`agent-eval-method.md` (how a role gets changed and measured — read it before touching a definition),
`GOTCHAS.md` (what bites, all of it measured).
