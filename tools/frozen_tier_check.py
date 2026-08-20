#!/usr/bin/env python3
"""
Frozen-tier check — did a pass alter substance in done/, sources/ or external/?

WHAT IT DOES
  Rule F lets the librarian fix `[[links]]` in the frozen tiers and append a dated note,
  but never alter existing wording. Those two allowed edits are hard to tell apart from a
  prose rewrite by eye, so this decides it mechanically: collapse every wikilink and
  backticked span to one placeholder, then compare.

    identical after collapsing        -> LINK-ONLY   (allowed)
    new starts with old               -> APPEND      (allowed)
    otherwise                         -> SUBSTANCE   (rule F violation)

  A deleted frozen file is reported too. `done/` is write-only for the librarian, so a
  deletion there is a finding even though it alters no wording.

WHY COLLAPSE TO A PLACEHOLDER RATHER THAN TO THE LINK TARGET
  Normalising a link to its own target makes an intentional repoint look like a prose
  change. On one pass that buried the single real defect under 23 deliberate repoints. A
  placeholder makes every repoint vanish and leaves only wording behind.

USAGE
  python3 tools/frozen_tier_check.py <git-ref> [path-or-prefix ...]
  python3 tools/frozen_tier_check.py librarian/h2db/full/2026-08-18
  python3 tools/frozen_tier_check.py main --ref-b HEAD
  python3 tools/frozen_tier_check.py <base> workstreams/h2db/      # scope filter

  The verdict set always comes from the diff. Extra arguments FILTER that set — an exact
  path, or a directory prefix, which is what every caller reaches for. --ref-b compares two
  refs instead of a ref against the working tree.

OUTPUT
  The considered path set first, then one line per changed frozen file, and for a SUBSTANCE
  verdict the old lines that are absent from the new.

    exit 0   checked, nothing wrong
    exit 1   a SUBSTANCE or DELETED verdict
    exit 2   your filter matched nothing, so nothing was checked

  --vault PATH is accepted like every other tool's: without it the tool answers about the
  CONFIGURED vault rather than the tree you are standing in, which is how it handed a green
  to every agent working somewhere else.

WHY EXIT 2 EXISTS — THE BUG THIS TOOL SHIPPED WITH
  Arguments used to be filtered through the frozen-tier pattern and then used as the path
  list, so a workstream prefix such as `workstreams/h2db/` matched no frozen *file*, the
  list came out empty, the diff was never read, and it printed "no frozen-tier files
  changed" and exited 0. Nine per-scope checks in one run proved nothing that way; only the
  one unscoped invocation verified anything. A verifier must distinguish CHECKED, NOTHING
  WRONG from CHECKED NOTHING — a silent pass is worse than no verifier, because it
  manufactures confidence. Hence: the considered set is always printed, and a filter that
  selects nothing is a hard error rather than a clean run.

  Two smaller bugs went with it. Explicit paths were never intersected with the diff, so an
  untouched frozen doc printed LINK-ONLY and was counted in "N frozen file(s) changed" —
  corrupting the one line a reviewer reads. And a directory argument reached `open()`,
  which raised, and the except-clause read that as DELETED: a rule-F violation reported for
  a file nobody had touched. Both are gone now that every verdict derives from
  `git diff --name-status` rather than from whether a read happened to fail.

GOTCHA THIS ENCODES
  An appended dated note is legitimate, so APPEND passes — but only as a strict prefix
  match. A note inserted mid-file reads as SUBSTANCE, which is correct: it means the
  surrounding text moved, and moved text is exactly what a reader would no longer find
  where a citing doc says it is.

  It cannot tell a violation from the commit that REPAIRS one — restoring the original
  wording is itself a wording change, so both flag. Measured on real history: it found the
  one violation among 23 changed frozen files and called the other 22 LINK-ONLY, passed a
  26-file de-link sweep clean, and also flagged the commit that restored the wording the
  violation had rewritten. Read the flag and judge it; do not edit a legitimate restoration
  to satisfy the script.
"""

import argparse
import os
import re
import subprocess

GIT_CWD = None   # set from the resolved vault in main(); git must run in the vault
import sys

FROZEN = re.compile(r"(^|/)(done|sources|external)/")


def git(*args):
    p = subprocess.run(["git", *args], capture_output=True, text=True, cwd=GIT_CWD)
    if p.returncode:
        sys.exit(p.stderr.strip() or f"git {' '.join(args)} failed")
    return p.stdout


def norm(t):
    t = re.sub(r"\[\[[^\]\n]+\]\]", "<L>", t)
    t = re.sub(r"`[^`\n]+`", "<L>", t)
    return "\n".join(line.rstrip() for line in t.split("\n")).strip()


def show(ref, path):
    p = subprocess.run(["git", "show", f"{ref}:{path}"], capture_output=True, text=True,
                       cwd=GIT_CWD)
    return None if p.returncode else p.stdout


def _read(path):
    """Read a vault-relative path from the VAULT, not from wherever the process was launched.

    THE DEFECT THIS FIXES: `open(path)` resolved against the process cwd, so every caller not
    standing inside the vault got `None` back for a file that exists -- which this tool then
    reported as `DELETED`, a rule-F violation, for files nobody had touched. Two false DELETED
    findings reproduced 2026-08-20 from a sibling checkout. Paired with the tool having had no
    `--vault` flag, it could be wrong in both directions at once.
    """
    try:
        with open(os.path.join(GIT_CWD or ".", path)) as fh:
            return fh.read()
    except OSError:
        return None


def untracked_frozen():
    """Frozen-tier files git does not know about yet.

    THE DEFECT THIS FIXES (tenth recorded instance of this check reporting on a diff it did
    not read): the verdict set comes from `git diff`, so a brand-new UNTRACKED file under
    sources/ or done/ is invisible and the tool answers "no frozen-tier files changed" --
    green, to a tier that just gained a document. An addition is usually sanctioned, but the
    check cannot tell a sanctioned one from an unsanctioned one by staying silent about both.
    Reproduced 2026-08-20 writing an eval into sources/evals/.
    """
    out = git("status", "--porcelain", "--untracked-files=all")
    rows = []
    for line in out.splitlines():
        if not line.startswith("??"):
            continue
        path = line[3:].strip().strip('"')
        if path.endswith(".md") and FROZEN.search(path):
            rows.append(("?", path))
    return rows


def changed_frozen(ref, ref_b):
    """Every frozen-tier markdown file the diff touches, as (status, path).

    Status comes from git, never from a failed read: that is what stops a directory
    argument being reported as a deleted file.
    """
    out = git("diff", "--name-status", ref, *([ref_b] if ref_b else []))
    rows = []
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        status, path = parts[0], parts[-1]        # for R/C the last field is the new path
        if path.endswith(".md") and FROZEN.search(path):
            rows.append((status[0], path))
    return rows


def selected(rows, filters):
    """Filters narrow the diff. An exact path or a directory prefix both work."""
    if not filters:
        return rows
    keep = []
    for status, path in rows:
        for f in filters:
            if path == f or path.startswith(f.rstrip("/") + "/"):
                keep.append((status, path))
                break
    return keep


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ref")
    ap.add_argument("paths", nargs="*",
                    help="filter the diff to these exact paths or directory prefixes")
    ap.add_argument("--ref-b", default=None,
                    help="compare <ref> against this ref instead of the working tree")
    import vault_config
    vault_config.add_argument(ap)
    a = ap.parse_args()
    global GIT_CWD
    _v = vault_config.resolve_or_exit(getattr(a, "vault", None), "frozen_tier_check")
    GIT_CWD = str(_v.path)
    a.paths = [vault_config.vault_relative(p, _v) for p in a.paths]

    rows = changed_frozen(a.ref, a.ref_b)
    # Untracked additions only exist relative to the working tree; a ref-to-ref comparison
    # has no room for them.
    new_rows = [] if a.ref_b else selected(untracked_frozen(), a.paths)
    rows = sorted(set(selected(rows, a.paths)), key=lambda r: r[1])

    # Say what was considered, always. A pass that printed nothing was indistinguishable
    # from a pass that looked at nothing.
    against = a.ref_b or "the working tree"
    scope = " ".join(a.paths) if a.paths else "the whole tree"
    print(f"considering: {a.ref}..{against}, frozen tiers under {scope}")

    if not rows and not new_rows:
        if a.paths:
            print(f"  NOTHING MATCHED your filter, so nothing was checked: {scope}")
            print("  frozen-tier files this diff touches, unfiltered:")
            allrows = changed_frozen(a.ref, a.ref_b)
            for _, path in sorted(allrows) or [(None, "    (none)")]:
                print(f"    {path}")
            return 2
        print("  no frozen-tier files changed in this diff")
        return 0

    for _, path in rows:
        print(f"  considered  {path}")
    for _, path in new_rows:
        print(f"  UNTRACKED   {path}  (new file in a frozen tier — sanctioned addition, or not?)")
    print()

    bad = []
    for status, path in rows:
        old = show(a.ref, path)
        new = show(a.ref_b, path) if a.ref_b else _read(path)
        if status == "D" or new is None:
            print(f"  DELETED    {path}   <- done/ is write-only; deleting is a finding")
            bad.append(path)
            continue
        if old is None:
            print(f"  ADDED      {path}")
            continue
        o, n = norm(old), norm(new)
        if o == n:
            print(f"  LINK-ONLY  {path}")
        elif n.startswith(o):
            print(f"  APPEND     {path}")
        else:
            print(f"  SUBSTANCE  {path}   <- rule F violation")
            missing = [l for l in o.split("\n") if l.strip() and l not in n.split("\n")]
            for l in missing[:12]:
                print(f"               - {l[:150]}")
            if len(missing) > 12:
                print(f"               … {len(missing) - 12} more")
            bad.append(path)

    tail = f", {len(new_rows)} untracked addition(s)" if new_rows else ""
    print(f"\nchecked {len(rows)} changed frozen file(s), {len(bad)} needing attention{tail}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
