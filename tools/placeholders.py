#!/usr/bin/env python3
"""
The template placeholders — defined once, imported by every tool that ports or checks a port.

WHY THIS FILE EXISTS
  The placeholder substitution has broken in a new way almost every time it has been touched,
  and each break was a different tool re-deriving the same rules slightly differently:

    - a port left a live placeholder in a file agents load as a system prompt, and the check
      of the day (byte-identity) passed it;
    - a mechanical substitution rewrote a tool's own docstring, which was DESCRIBING the
      placeholder, then rewrote its comparison code, making the checker a silent no-op that
      reported every file as diverging;
    - a private vault path leaked into the public template on the way back up;
    - and a port tool skipped inline code spans as "discussion", which silently left every
      REAL usage unsubstituted, because paths in these docs are always written in backticks.

  Every one of those is a disagreement about two questions: which tokens exist, and where a
  token may legally appear. So both answers live here, and nothing re-derives them.

THE TOKENS
  PATH   the absolute path of the vault             -> e.g. /home/you/vault
  NAME   the directory name it is symlinked as      -> e.g. vault

  Assembled at import, never written as a literal anywhere in this file. A substitution pass
  over the tools directory would otherwise rewrite these definitions into real paths and take
  the whole mechanism with it. That is not hypothetical; it happened.

WHERE A TOKEN MAY APPEAR — the authoring rule
  USE a token freely in prose and in inline code spans. That is a real usage and a port
  substitutes it.

  Do NOT write a token as an EXAMPLE outside a fenced block. A substitution cannot tell an
  example from a usage, so it will rewrite your example and turn the sentence explaining it
  into nonsense. If you must show one, put it in a fenced block — those are held — or describe
  it in words without writing it out.

  `hazards()` finds violations of that rule so it fails loudly instead of being remembered.
"""

import re

# Assembled, never literal. See above.
_OPEN, _CLOSE = "{" * 2, "}" * 2
PATH = _OPEN + "VAULT_PATH" + _CLOSE
NAME = _OPEN + "VAULT" + _CLOSE

#: every placeholder this project defines, longest first so PATH is matched before NAME
TOKENS = (PATH, NAME)

ANY = re.compile(r"\{\{[A-Za-z0-9_]+\}\}")
FENCE = re.compile(r"^\s*(```|~~~)")

#: files that are shared between template and vault, and so get ported
SHARED_GLOBS = ("agents/*.md", "skills/*/*.md", "tools/*.py",
                "CLAUDE.md", "GOTCHAS.md", "README.md", "BOOTSTRAPPING.md")


def mapping(vault_path, vault_name):
    """template -> vault. Longest token first so no substitution eats another's prefix."""
    return {PATH: vault_path, NAME: vault_name}


def reverse_mapping(vault_path):
    """vault -> template. Only the PATH is reversed.

    The NAME is a bare directory name — reversing it would rewrite every innocent occurrence of
    that word in the prose. A private path leaking upward is the failure that matters, and it
    is the one this catches.
    """
    return {vault_path: PATH}


def outside_fences(text):
    """Yield (lineno, line) for every line not inside a fenced block."""
    in_fence = False
    for i, line in enumerate(text.splitlines(), 1):
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        if not in_fence:
            yield i, line


def survivors(text, ignore_documented=True):
    """Placeholders left after a substitution — the hard-fail condition.

    Inline code spans are INCLUDED. A placeholder in backticks is a usage, so one still sitting
    there after a port is a missed mapping, not a false positive.

    But a ported doc may legitimately DESCRIBE the porting step, and then a placeholder on that
    line is documentation, not a break. Those lines are exactly the ones `hazards()` names, so
    they are excluded by default: a check that stays red on correct content is one readers learn
    to dismiss, and the real survivor goes with it. Pass ignore_documented=False for the raw set.
    """
    skip = {ln for ln, _ in hazards(text)} if ignore_documented else set()
    hits = set()
    for ln, line in outside_fences(text):
        if ln in skip:
            continue
        hits.update(ANY.findall(line))
    return sorted(hits)


def hazards(text):
    """Placeholders written where a port will substitute them but an author meant an example.

    Heuristic and deliberately narrow: a token on a line that also reads like an explanation of
    the porting mechanism. Reported as a warning, never a hard failure — the hard failure is a
    survivor, and a warning that fires on real usages would train readers to ignore both.
    """
    telltale = re.compile(
        r"\b(substitut|placeholder|replace|token|literal|system prompt|port(ing|ed)?\b)", re.I)
    out = []
    for i, line in enumerate_lines(text):
        if ANY.search(line) and telltale.search(line):
            out.append((i, line.strip()))
    return out


def enumerate_lines(text):
    for i, line in outside_fences(text):
        yield i, line


if __name__ == "__main__":
    import argparse
    from pathlib import Path
    ap = argparse.ArgumentParser(description="check placeholder usage in shared files")
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--ported", action="store_true",
                    help="these files have already been substituted, so ANY placeholder is a "
                         "hard failure. Without this, files are treated as template-side, where "
                         "placeholders are expected and only hazards are reported.")
    a = ap.parse_args()
    if not a.paths:
        print(__doc__.strip())
        print(f"\ntokens: {' '.join(TOKENS)}")
        raise SystemExit(0)
    bad = 0
    for f in a.paths:
        t = Path(f).read_text(errors="replace")
        if a.ported:
            for tok in survivors(t):
                print(f"{f}: SURVIVOR {tok} — an agent reads this literally, as a path")
                bad = 2
        for ln, line in hazards(t):
            print(f"{f}:{ln}: HAZARD — placeholder written on a line about porting; a "
                  f"substitution will rewrite it and break the sentence")
            print(f"    {line[:110]}")
    raise SystemExit(bad)
