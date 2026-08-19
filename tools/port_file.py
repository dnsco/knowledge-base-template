#!/usr/bin/env python3
"""
Port a shared file between the template and a vault — and refuse to flatten it.

WHAT THIS GUARDS THAT port_check.py DOES NOT
  port_check.py inspects a port after the fact and hard-fails on a surviving placeholder. It
  says nothing about the other failure, which is the one that has actually cost work: a
  wholesale copy that ERASES the vault's deliberate divergence. Byte-identity then passes,
  because identity is exactly what that mistake produces.

  Measured 2026-08-18: one port of a shared skill replaced the vault's project-specific
  description, its build command, its example script and its path phrasing with generic
  template prose, AND left a live placeholder in a file agents load as a system prompt. Four
  losses and one break, in a step that reported success.

  So this does not overwrite. It substitutes, diffs, and shows what the destination WOULD LOSE
  — line by line — and writes only when you have seen that list and passed --apply.

THE THIRD FOOTGUN
  A mechanical substitution rewrites any shared file that contains the placeholder AS DATA. It
  corrupted port_check.py's own docstring, then its comparison code, turning the checker into a
  silent no-op that reported every file as diverging. So: the token is assembled at runtime and
  never written as a literal here, and substitution skips fenced blocks and inline code spans,
  where a placeholder is being discussed rather than used.

DIRECTION
  down (default)  template -> vault, substituting the placeholder for the vault's real path
  --up            vault -> template, replacing that path with the placeholder again

  Porting up is how a fix authored by mistake in the vault gets back where it belongs. It is
  not a licence to author there: a vault-side edit still guarantees a second divergence.

USAGE
  python3 tools/port_file.py <relpath>... --template DIR --vault DIR [--vault-path STR]
  python3 tools/port_file.py agents/scout.md --template . --vault ~/vault --apply
  python3 tools/port_file.py CLAUDE.md --template . --vault ~/vault --up --apply

    exit 0   in agreement, or applied
    exit 1   would change the destination — review the loss list, then --apply
    exit 2   a placeholder would survive the port (never applied)
    exit 5   bad invocation
"""

import argparse
import difflib
import re
import sys
from pathlib import Path

# Assembled, never written as a literal — a substitution pass over this file would otherwise
# rewrite the example and destroy the sentence explaining it. That has happened.
TOKEN = "{{" + "VAULT_PATH" + "}}"
NAME_TOKEN = "{{" + "VAULT" + "}}"
ANY_PLACEHOLDER = re.compile(r"\{\{[A-Za-z0-9_]+\}\}")
CODE = re.compile(r"`[^`\n]*`")
FENCE = re.compile(r"^\s*(```|~~~)")


def substitute(text, mapping):
    """Replace tokens outside FENCED blocks. Inline code spans ARE substituted.

    The two cases look alike and are not. A placeholder inside backticks is nearly always a
    real USAGE -- paths are written in backticks throughout these docs, so `<placeholder>/tools`
    is a path, not an example of one. A placeholder being DISCUSSED belongs in a fenced block,
    or is written out in prose, which the convention for shared files forbids precisely because
    a substitution pass cannot tell the two apart. So: fenced blocks are held; everything else
    is substituted; and anything still holding a placeholder afterwards is reported, INCLUDING
    inside inline spans, because at that point it is either a missed mapping or prose that
    should not have written a placeholder out in the first place.
    """
    out, in_fence = [], False
    for line in text.splitlines(keepends=True):
        if FENCE.match(line):
            in_fence = not in_fence
            out.append(line)
            continue
        if in_fence:
            out.append(line)
            continue
        for k, v in mapping.items():
            line = line.replace(k, v)
        out.append(line)
    return "".join(out)


def survivors(text):
    """Placeholders left after substitution, outside fenced blocks — inline spans included."""
    hits = set()
    in_fence = False
    for line in text.splitlines():
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        hits.update(ANY_PLACEHOLDER.findall(line))
    return sorted(hits)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--template", required=True)
    ap.add_argument("--vault", required=True)
    ap.add_argument("--vault-path", default=None,
                    help="what the path placeholder stands for (default: --vault)")
    ap.add_argument("--vault-name", default=None,
                    help="what the name placeholder stands for (default: the vault dir name)")
    ap.add_argument("--up", action="store_true", help="vault -> template")
    ap.add_argument("--apply", action="store_true", help="write; without this it only reports")
    args = ap.parse_args()

    tdir = Path(args.template).expanduser().resolve()
    vdir = Path(args.vault).expanduser().resolve()
    if not tdir.is_dir() or not vdir.is_dir():
        print("both --template and --vault must be directories", file=sys.stderr)
        return 5
    vault_path = args.vault_path or str(vdir)
    vault_name = args.vault_name or vdir.name

    down_map = {TOKEN: vault_path, NAME_TOKEN: vault_name}
    up_map = {vault_path: TOKEN}          # name is too generic to reverse safely

    worst = 0
    for rel in args.paths:
        src_dir, dst_dir = (vdir, tdir) if args.up else (tdir, vdir)
        src, dst = src_dir / rel, dst_dir / rel
        print(f"\n=== {rel}   ({'vault -> template' if args.up else 'template -> vault'})")
        if not src.is_file():
            print(f"  source missing: {src}")
            worst = max(worst, 5)
            continue

        ported = substitute(src.read_text(errors="replace"), up_map if args.up else down_map)

        left = survivors(ported)
        if left:
            print(f"  PLACEHOLDER SURVIVES: {', '.join(left)}")
            print("  Not applied. An agent reads an unsubstituted placeholder literally, as a path,")
            print("  in its own system prompt. Fix the mapping or the source.")
            worst = max(worst, 2)
            continue

        old = dst.read_text(errors="replace") if dst.is_file() else ""
        if old == ported:
            print("  already in agreement")
            continue

        o, n = old.splitlines(), ported.splitlines()
        sm = difflib.SequenceMatcher(None, o, n, autojunk=False)
        lost, gained = [], []
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag in ("delete", "replace"):
                lost += [(i1 + k + 1, o[i1 + k]) for k in range(i2 - i1)]
            if tag in ("insert", "replace"):
                gained += [(j1 + k + 1, n[j1 + k]) for k in range(j2 - j1)]

        print(f"  destination would LOSE {len(lost)} line(s), GAIN {len(gained)}")
        if lost:
            print("\n  --- lines the destination has and the port would remove ---")
            print("      Read every one. A line naming this vault's real project, repos, dated")
            print("      evidence or a concrete sha is DELIBERATE divergence, and losing it is")
            print("      the failure this tool exists to prevent — not a diff to be cleared.")
            for ln, text in lost[:60]:
                print(f"      -{ln:5} {text}")
            if len(lost) > 60:
                print(f"      … and {len(lost) - 60} more")
        if gained:
            print("\n  --- lines the port would add ---")
            for ln, text in gained[:40]:
                print(f"      +{ln:5} {text}")
            if len(gained) > 40:
                print(f"      … and {len(gained) - 40} more")

        if args.apply:
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(ported)
            print(f"\n  APPLIED -> {dst}")
        else:
            worst = max(worst, 1)

    print()
    if worst == 0:
        print("nothing to do" if not args.apply else "applied")
    elif worst == 1:
        print("Nothing written. Review the loss lists above, then re-run with --apply.")
    return worst


if __name__ == "__main__":
    sys.exit(main())
