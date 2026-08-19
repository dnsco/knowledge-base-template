#!/usr/bin/env python3
"""
Budget check — is a parent folder-note or a task frontier over its size budget.

WHY A TOOL AND NOT A SENTENCE
  The design's requirement is that a push surface stays short enough to be read at the moment of
  proposing. "Thin" written in prose does not fire; a size in an exit code does. This is also the
  measurement that split detection never had: detect-and-propose produced zero split proposals
  across every pass it was assigned to, partly because nothing measured the pressure. A parent
  over budget IS that measurement.

WHAT OVER BUDGET MEANS -- AND THE ONE THING IT NEVER MEANS
  Two responses, cheaper first:
    1. EXTRACT. Material that is reference rather than a live warning, and useful beyond this
       workstream, goes to reference/ or design/.
    2. SPLIT. When the parent is heavy because it is two efforts wearing one name.
  It NEVER means trimming the task index or deleting history. The summaries of what happened are
  among the most useful things in the vault; the pressure falls on the restated subset and the
  cross-task invariants. A workstream held under budget by deleting history has failed the check
  it appeared to pass, so this tool prints that with every breach.

THE NUMBERS ARE HYPOTHESES
  Parent: 12 KB target, 16 KB signal. Calibrated against one corpus and nothing else -- they
  separate today's smallest parent (~9 KB) from the oversized ones (21-59 KB). Task: 8 KB / 12 KB,
  a guess with a shape, on the argument that a task frontier is read more often than a parent and
  carries pulled-forward warnings on top of its own. No unit built under this design has been
  measured. Expect to move all four; that is what --parent-target and friends are for.

USAGE
  python3 tools/budget_check.py workstreams/<ws>                 # parent + every task in it
  python3 tools/budget_check.py workstreams/<ws>/<ws>.md         # one file, judged as a parent
  python3 tools/budget_check.py workstreams/<ws>/2026-08-19-x/   # one task
  python3 tools/budget_check.py workstreams/*  --quiet           # the whole corpus, breaches only

EXIT CODES
  0  everything under target
  1  over target, under the signal -- watch it
  2  over the signal -- the workstream probably wants extraction or a split. Read the section
     table and decide which; do not trim the index
  5  bad invocation
"""

import argparse
import os
import re
import sys

PARENT_TARGET, PARENT_LIMIT = 12 * 1024, 16 * 1024
TASK_TARGET, TASK_LIMIT = 8 * 1024, 12 * 1024
TASK_DIR = re.compile(r"^\d{4}-\d{2}-\d{2}-")
DATED_DOC = re.compile(r"^\d{4}-\d{2}-\d{2}-.*\.md$")


def sections(path):
    """(heading, bytes) for each top-level-or-deeper heading, largest first."""
    try:
        text = open(path, encoding="utf-8").read()
    except OSError:
        return []
    parts, cur, buf = [], "(frontmatter/preamble)", []
    for line in text.splitlines(keepends=True):
        if line.startswith("#"):
            parts.append((cur, sum(len(b.encode()) for b in buf)))
            cur, buf = line.strip(), []
        else:
            buf.append(line)
    parts.append((cur, sum(len(b.encode()) for b in buf)))
    return sorted(parts, key=lambda p: -p[1])


def frontier_of(task_dir):
    """A task's frontier: the one undated .md in the folder. Dumps inside are dated."""
    cands = [f for f in sorted(os.listdir(task_dir))
             if f.endswith(".md") and not DATED_DOC.match(f)]
    if not cands:
        return None
    named = os.path.basename(task_dir.rstrip("/"))
    named = TASK_DIR.sub("", named) + ".md"
    return os.path.join(task_dir, named if named in cands else cands[0])


def units(target):
    """Yield (kind, path) for whatever the caller pointed at."""
    target = target.rstrip("/")
    if os.path.isfile(target):
        parent = os.path.basename(os.path.dirname(target))
        kind = "task" if TASK_DIR.match(parent) else "parent"
        return [(kind, target)]
    if not os.path.isdir(target):
        return []
    base = os.path.basename(target)
    if TASK_DIR.match(base):
        f = frontier_of(target)
        return [("task", f)] if f else []
    out = []
    note = os.path.join(target, base + ".md")
    if os.path.exists(note):
        out.append(("parent", note))
    for entry in sorted(os.listdir(target)):
        sub = os.path.join(target, entry)
        if os.path.isdir(sub) and TASK_DIR.match(entry):
            f = frontier_of(sub)
            if f:
                out.append(("task", f))
    return out


def main(argv):
    ap = argparse.ArgumentParser(description="Is a parent or task frontier over its byte budget.")
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--parent-target", type=int, default=PARENT_TARGET)
    ap.add_argument("--parent-limit", type=int, default=PARENT_LIMIT)
    ap.add_argument("--task-target", type=int, default=TASK_TARGET)
    ap.add_argument("--task-limit", type=int, default=TASK_LIMIT)
    ap.add_argument("--quiet", action="store_true", help="print breaches only")
    ap.add_argument("--sections", type=int, default=4,
                    help="how many largest sections to show on a breach (0 = none)")
    args = ap.parse_args(argv)

    rows, seen = [], set()
    for p in args.paths:
        if not os.path.exists(p):
            print(f"no such path {p!r} -- expected a workstream folder, a folder-note, or a dated "
                  f"task folder", file=sys.stderr)
            return 5
        found = units(p)
        if not found:
            # A real directory holding no unit -- a shelf like workstreams/parked/, or a folder
            # whose docs are flat. Skipped and named, never a failure: a check that goes red on
            # correct content gets dismissed, and then it protects nothing.
            if not args.quiet:
                print(f"skip  --     no parent folder-note or dated task folder in {p}")
            continue
        for kind, path in found:
            if path in seen:
                continue
            seen.add(path)
            tgt = args.parent_target if kind == "parent" else args.task_target
            lim = args.parent_limit if kind == "parent" else args.task_limit
            size = os.path.getsize(path)
            state = "OVER" if size > lim else ("WATCH" if size > tgt else "ok")
            rows.append((state, kind, path, size, tgt, lim))

    worst = 0
    for state, kind, path, size, tgt, lim in rows:
        if state == "ok" and args.quiet:
            continue
        print(f"{state:5} {kind:6} {size:6}B  target {tgt}B  signal {lim}B  {path}")
        if state != "ok" and args.sections:
            for head, nbytes in sections(path)[:args.sections]:
                if nbytes:
                    print(f"        {nbytes:6}B  {head[:96]}")
        worst = max(worst, {"ok": 0, "WATCH": 1, "OVER": 2}[state])

    if worst == 2:
        print("\nOver the signal. Two responses, cheaper first:")
        print("  1. EXTRACT reference-rather-than-warning material to reference/ or design/.")
        print("  2. SPLIT, when the parent is heavy because it is two efforts wearing one name.")
        print("It never means trimming the task index or deleting history -- a unit held under "
              "budget that way\nhas failed the check it appears to pass. The pressure belongs on "
              "the restated subset and the\ncross-task invariants. Splitting is an owner's call: "
              "propose it, do not execute it.")
    elif worst == 1:
        print("\nOver target, under the signal. Nothing to do yet; the section table above is "
              "where the weight is.")
    return worst


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
