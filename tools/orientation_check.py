#!/usr/bin/env python3
"""
Orientation check — did this task pull forward the warnings that bear on it.

WHY THIS IS THE CHECK THE WHOLE PARTITION RESTS ON
  The design's move is carry-across on open, not carry-up on close: when a task opens it pulls
  the still-live warnings out of the workstream's closed tasks and out of historical/ into its own
  frontier, and selection is paid once, by whoever knows what the task is about. Nothing is lost
  PROVIDED THE PULL HAPPENS. Without it, promotion to done/ is exactly how a live warning goes
  dark quietly -- and quietly is the whole problem, because a dead end that does not fire is
  indistinguishable from one that was never recorded.

  A mandatory step written into a definition has failed to fire in this system before -- measured,
  repeatedly. So the requirement is a check with an exit code, and `historical/` staying live is
  the interim mitigation until every workstream is converted.

WHAT COUNTS AS CITING
  A section headed `Carried across` (or Carried forward / Orientation / Pulled forward) holding
  either:
    - one or more items that cite a source -- a [[wikilink]], or a path under done/ or historical/;
      or
    - an explicit nothing-to-carry statement that still names what was read, e.g.
      `- Reviewed [[done/2026-07-01-x]] and historical/ -- nothing bears on this task.`
  The escape hatch is deliberate and deliberately not silent: a task genuinely opening on new
  ground must still say what it looked at, because "nothing applied" and "nobody looked" are the
  two states this check exists to keep apart.

USAGE
  python3 tools/orientation_check.py workstreams/<ws>/2026-08-19-<task>/
  python3 tools/orientation_check.py workstreams/<ws>/2026-08-19-<task>/<task>.md
  python3 tools/orientation_check.py workstreams/<ws>            # every live task in it

EXIT CODES
  0  every task cites what it reviewed
  1  cited, but the workstream has a done/ or historical/ the frontier never mentions -- read it
     and judge whether the pull was complete
  2  a defect: no orientation section, or one with nothing cited. The pull did not happen
  5  bad invocation
"""

import argparse
import os
import re
import sys

HEADING = re.compile(r"^#{1,4}\s+(carried\s+(across|forward)|orientation|pulled\s+forward)\b",
                     re.I)
ANY_HEADING = re.compile(r"^#{1,4}\s+")
CITATION = re.compile(r"\[\[[^\]]+\]\]|(?<![\w/])done/|(?<![\w/])historical/")
NOTHING = re.compile(r"nothing (bears|applies|carried|to carry)|no (live )?warnings? (bear|apply)",
                     re.I)
TASK_DIR = re.compile(r"^\d{4}-\d{2}-\d{2}-")
DATED_DOC = re.compile(r"^\d{4}-\d{2}-\d{2}-.*\.md$")


def frontier_of(task_dir):
    cands = [f for f in sorted(os.listdir(task_dir))
             if f.endswith(".md") and not DATED_DOC.match(f)]
    if not cands:
        return None
    named = TASK_DIR.sub("", os.path.basename(task_dir.rstrip("/"))) + ".md"
    return os.path.join(task_dir, named if named in cands else cands[0])


def targets(path):
    path = path.rstrip("/")
    if os.path.isfile(path):
        return [path]
    if not os.path.isdir(path):
        return []
    if TASK_DIR.match(os.path.basename(path)):
        f = frontier_of(path)
        return [f] if f else []
    out = []
    for entry in sorted(os.listdir(path)):
        sub = os.path.join(path, entry)
        if os.path.isdir(sub) and TASK_DIR.match(entry):
            f = frontier_of(sub)
            if f:
                out.append(f)
    return out


def orientation_block(text):
    lines, block, inside = text.splitlines(), [], False
    for line in lines:
        if HEADING.match(line):
            inside = True
            continue
        if inside and ANY_HEADING.match(line):
            break
        if inside:
            block.append(line)
    return block if inside else None


def check(frontier):
    """(exit_code, message) for one task frontier."""
    text = open(frontier, encoding="utf-8").read()
    block = orientation_block(text)
    if block is None:
        return 2, ("no orientation section. Add one headed `## Carried across` naming the closed "
                   "tasks and historical/ material you reviewed, and what you pulled forward.")
    body = "\n".join(block)
    cited = CITATION.findall(body)
    if not cited:
        if NOTHING.search(body):
            return 2, ("the orientation section says nothing was carried but names nothing it "
                       "read. Cite what you reviewed -- 'nothing applied' and 'nobody looked' "
                       "must not be spelled the same way.")
        return 2, "the orientation section cites nothing. The pull did not happen."

    ws = os.path.dirname(os.path.dirname(os.path.abspath(frontier)))
    unmentioned = [d for d in ("done", "historical")
                   if os.path.isdir(os.path.join(ws, d)) and d + "/" not in body
                   and not re.search(r"\[\[[^\]]*" + d + r"[^\]]*\]\]", body, re.I)]
    if unmentioned:
        return 1, (f"cites {len(cited)} source(s), but this workstream has "
                   f"{'/ '.join(unmentioned)}/ that the section never mentions. Judge whether the "
                   f"pull was complete; say so explicitly if it was.")
    return 0, f"cites {len(cited)} source(s)"


def main(argv):
    ap = argparse.ArgumentParser(
        description="Does a task frontier cite what it reviewed on open.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""WHAT COUNTS AS CITING (measured: an agent read this tool's source to find out,
which is 6 KB it should not have had to load)

  A section headed `Carried across` (or Carried forward / Orientation / Pulled forward), holding
  EITHER one or more items citing a source -- a [[wikilink]], or a path under done/ or historical/ --
  OR an explicit nothing-to-carry line that STILL names what was read:
      - Reviewed [[done/2026-07-01-x]] and historical/ -- nothing bears on this task.

  The escape hatch is deliberate and deliberately not silent: "nothing applied" and "nobody looked"
  are the two states this check exists to keep apart.

  exit 0 cited · exit 1 cited but a done/ or historical/ goes unmentioned, judge it · exit 2 no
  section or nothing cited: the pull did not happen · exit 5 bad invocation""")
    ap.add_argument("paths", nargs="+")
    args = ap.parse_args(argv)
    import vault_config
    args.paths = [vault_config.anchor(p) or p for p in args.paths]

    frontiers = []
    for p in args.paths:
        if not os.path.exists(p):
            print(f"no such path {p!r}", file=sys.stderr)
            return 5
        found = targets(p)
        if not found:
            print(f"skip  no dated task folder in {p} -- nothing to check "
                  f"(an unconverted workstream has no tasks yet)")
            continue
        frontiers.extend(found)

    worst = 0
    for f in frontiers:
        code, msg = check(f)
        label = {0: "ok", 1: "JUDGE", 2: "MISSING"}[code]
        print(f"{label:8} {f}\n         {msg}")
        worst = max(worst, code)
    return worst


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
