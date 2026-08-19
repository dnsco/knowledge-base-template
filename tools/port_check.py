#!/usr/bin/env python3
"""
Port check — did a backport leave template placeholders behind, or flatten a deliberate difference?

THE WORKFLOW THIS GUARDS
  Shared surfaces are authored in the template, ported down to a vault, tried on real work, and
  profiled; findings go back to the template. Only the port step is mechanical, and it has two
  failure modes that look like success.

  1. AN UNSUBSTITUTED PLACEHOLDER. A copied file still carrying a brace-delimited placeholder is
     broken in a way nothing else notices: an agent reads it literally, as a path, in its own system
     prompt. HARD FAIL, exit 2. (This docstring deliberately never writes one out — a mechanical
     substitution would rewrite the example and destroy the sentence explaining it. That happened.)

  2. A FLATTENED DIFFERENCE. Some divergence between the two copies is deliberate: the vault names
     its actual project, its real repos, dated evidence and concrete shas, where the template is
     generic. Copying wholesale erases that, and a byte-identity check REWARDS you for it. Measured:
     one port replaced a vault skill's project-specific description with generic template prose and
     introduced a live placeholder at the same time, and an identity check passed it.

  So this asserts no placeholders, then PRINTS the residual divergence for a human to judge rather
  than demanding it be zero. Byte-identity is the wrong gate for a file that is meant to differ.

USAGE
  python3 tools/port_check.py --vault <vault> [--template .] [PATH ...]

  With no PATHs it checks every file present in both trees under agents/, skills/, tools/, plus the
  four root docs. --vault-path overrides the substitution (default: the --vault value).

    exit 0   no placeholders; residue printed for review
    exit 2   an unsubstituted placeholder survived the port
    exit 3   bad invocation, or nothing to compare
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

PLACEHOLDER = re.compile(r"\{\{[A-Za-z0-9_]+\}\}")
FENCE = re.compile(r"^\s*(```|~~~)")


def live_placeholders(text):
    """Placeholders that would actually be read as a path.

    Skips fenced blocks and inline code spans: a doc explaining the port convention writes the
    placeholder in backticks on purpose, and flagging that trains the reader to ignore this check —
    the same false-positive class dangling_links.py separates for wikilinks.
    """
    hits, in_fence = set(), False
    for line in text.splitlines():
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        hits.update(PLACEHOLDER.findall(re.sub(r"`[^`\n]*`", "", line)))
    return sorted(hits)
DEFAULT = ["CLAUDE.md", "GOTCHAS.md", "README.md", "BOOTSTRAPPING.md"]
# Assembled, never written out. A port substitutes this token wherever it appears — including in
# the source of the tool that checks the port, whose comparison then silently becomes a no-op and
# reports every file as diverging. Measured: it happened, and cost a debugging round.
TOKEN = "{{" + "VAULT_PATH" + "}}"
# reference/ joined the shared set when the ontology design and the eval method shipped upstream:
# they are generic enough that a clone wants them, so they are authored here like any other surface.
DIRS = ["agents", "skills", "tools", "reference"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", required=True)
    ap.add_argument("--template", default=".")
    ap.add_argument("--vault-path", default=None,
                    help="the string {{VAULT_PATH}} was replaced with (default: --vault)")
    ap.add_argument("paths", nargs="*")
    a = ap.parse_args()

    vault, tmpl = Path(a.vault).expanduser(), Path(a.template).expanduser()
    if not vault.is_dir() or not tmpl.is_dir():
        sys.exit(3)
    vault_path = a.vault_path or a.vault

    rels = list(a.paths)
    if not rels:
        rels = [f for f in DEFAULT if (vault / f).is_file() and (tmpl / f).is_file()]
        for d in DIRS:
            for p in sorted((tmpl / d).rglob("*")):
                if p.is_file() and p.suffix in (".md", ".py"):
                    r = str(p.relative_to(tmpl))
                    if (vault / r).is_file():
                        rels.append(r)
    if not rels:
        print("nothing present in both trees to compare")
        return 3

    bad, checked = [], 0
    print(f"port check: {len(rels)} file(s) present in both trees\n")
    for r in rels:
        v = (vault / r).read_text()
        hits = live_placeholders(v)
        if hits:
            bad.append((r, hits))
            print(f"  PLACEHOLDER  {r}   <- {', '.join(hits)} survived the port")
        checked += 1

    print()
    for r in rels:
        v = (vault / r).read_text().replace(vault_path, TOKEN)
        t = (tmpl / r).read_text()
        if v == t:
            print(f"  identical    {r}")
            continue
        d = subprocess.run(["diff", "-", str(tmpl / r)], input=v,
                           capture_output=True, text=True)
        n = sum(1 for l in d.stdout.splitlines() if l[:1] in "<>")
        print(f"  DIVERGES     {r}   ({n} lines) — judge each, do not flatten to zero")

    print(f"\n{checked} checked, {len(bad)} with surviving placeholders")
    if bad:
        print("A placeholder in a shipped file means an agent reads it literally. Substitute and re-run.")
        return 2
    print("No placeholders. Now READ the divergence above: every line should be either the path")
    print("substitution or a deliberate project-specific difference. If a line is neither, the port")
    print("either dropped a template improvement or flattened something the vault meant to keep.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
