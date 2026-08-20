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

WHY THE PARENT IS JUDGED ON NON-REGISTER BYTES
  Measured on the first pass run under this design (2026-08-19): converting a 56 KB parent moved it to 54 KB
  and the tool still exited 2 -- because the register (26 KB) plus the live gates (7 KB) are ~34 KB, which is
  2.1x the 16 KB signal BY CONSTRUCTION. The register stays in the parent: that is a settled owner decision and
  a recorded DEAD END, on the argument that a document agents must be told to open is how a warning stops
  firing. So a total-bytes signal on such a parent is permanently red, and a check that is permanently red gets
  read past -- the exact failure this vault cites for prose.

  So the parent's budget is measured against everything that is NOT the register and NOT the task index: the
  restated subset, the prose, the companion lists. That is where the design says the pressure belongs. The
  register is reported beside it with its own softer threshold, because the lever there is different and is a
  question rather than a rule: move out the ALREADY-MITIGATED items, which are reference, and keep resident the
  warnings that must fire unprompted.

THE NUMBERS ARE HYPOTHESES
  Parent: 8 KB target, 12 KB signal, against NON-REGISTER bytes. Task: 8 KB / 12 KB against the
  whole file, since a task's gates are its live surface and it has no index to protect. Register:
  a 20 KB soft mark that reports and asks, and never fails.

  Where they come from: the first two frontiers built under this design landed at 7.3 and 7.6 KB
  with no effort (2026-08-19), which is what set the task numbers; the same pass's parent carried
  18.7 KB of non-register bytes, so the parent signal is set to bite it. The earlier 12/16 KB pair
  was against total bytes and was unreachable by construction on any parent with a real register.
  Expect to move all of these; that is what --parent-target and friends are for.

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
import subprocess
import sys

# Fallbacks only. The live numbers come from ~/.config/lipika/config.json via vault_config, so
# that a threshold has one home instead of being restated in prose that then goes stale -- which
# is exactly what happened to the earlier 12/16 KB pair. Flags still win over both.
PARENT_TARGET, PARENT_LIMIT = 8 * 1024, 12 * 1024      # non-register bytes
TASK_TARGET, TASK_LIMIT = 8 * 1024, 12 * 1024
REGISTER_SOFT = 20 * 1024                              # report, ask, never mandate


def _configured():
    """(parent, task, register_soft) from config, falling back to the constants above.

    A tool that only measures must never die because a config is absent or malformed: it reports
    what it can. The refusal-on-unresolvable rule is for tools that WRITE to a vault.
    """
    try:
        import vault_config
        v = vault_config.resolve()
        return v.budget("parent"), v.budget("task"), v.soft("register") or REGISTER_SOFT
    except Exception:
        return (PARENT_TARGET, PARENT_LIMIT), (TASK_TARGET, TASK_LIMIT), REGISTER_SOFT
# A heading is register-or-index if it matches this. Both are exempt from the parent budget: the
# register by owner decision, the index because "over budget never means trimming the task index".
EXEMPT_HEADING = re.compile(
    r"risk|gate|landmine|dead[ -]end|open q|register|task index|tasks\b|landed|closed|done\b", re.I)
REGISTER_HEADING = re.compile(r"risk|gate|landmine|dead[ -]end|open q|register", re.I)
TASK_DIR = re.compile(r"^\d{4}-\d{2}-\d{2}-")
DATED_DOC = re.compile(r"^\d{4}-\d{2}-\d{2}-.*\.md$")


def delta_since(path, ref, kind):
    """Budgeted bytes now vs at a git ref. A pass needs to know it moved the number."""
    d = os.path.dirname(os.path.abspath(path)) or "."
    try:
        # Resolve against the FILE's repo, not the caller's cwd -- these tools are invoked by
        # absolute path from anywhere, and `git show ref:./rel` silently means the wrong tree.
        top = subprocess.run(["git", "-C", d, "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True, check=True).stdout.strip()
        rel = os.path.relpath(os.path.abspath(path), top)
        blob = subprocess.run(["git", "-C", d, "show", f"{ref}:{rel}"],
                              capture_output=True, text=True, check=True).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return f"not readable at {ref} (new file, or a ref that does not resolve)"
    tmp = f"/tmp/.budget_check_{os.getpid()}.md"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(blob)
    try:
        t0, r0, e0, b0 = split_bytes(tmp)
        t1, r1, e1, b1 = split_bytes(path)
        was, now = (b0, b1) if kind == "parent" else (t0, t1)
        sign = "+" if now >= was else ""
        return f"budgeted {was}B -> {now}B ({sign}{now - was}B), register {r0}B -> {r1}B"
    finally:
        os.unlink(tmp)


def split_bytes(path):
    """(total, register, index_and_other_exempt, budgeted) in bytes for one doc."""
    total = os.path.getsize(path)
    reg = exempt = 0
    for head, nbytes in sections(path):
        if REGISTER_HEADING.search(head):
            reg += nbytes
        elif EXEMPT_HEADING.search(head):
            exempt += nbytes
    return total, reg, exempt, max(0, total - reg - exempt)


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
    (p_tgt, p_lim), (t_tgt, t_lim), reg_soft = _configured()
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--parent-target", type=int, default=p_tgt)
    ap.add_argument("--parent-limit", type=int, default=p_lim)
    ap.add_argument("--task-target", type=int, default=t_tgt)
    ap.add_argument("--task-limit", type=int, default=t_lim)
    ap.add_argument("--register-soft", type=int, default=reg_soft)
    ap.add_argument("--quiet", action="store_true", help="print breaches only")
    ap.add_argument("--sections", type=int, default=4,
                    help="how many largest sections to show on a breach (0 = none, -1 = all). "
                         "Measured: with only the top four printed, a pass hand-rolled the rest")
    ap.add_argument("--since", metavar="REF",
                    help="also report the budgeted-byte delta against a git ref, so a pass can see "
                         "whether it moved the number. Without it a mid-pass run can report a parent "
                         "LARGER than it started and say nothing about why")
    args = ap.parse_args(argv)

    rows, seen = [], set()
    try:
        import vault_config
        args.paths = [vault_config.anchor(p) or p for p in args.paths]
    except Exception:
        pass
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
            total, reg, exempt, budgeted = split_bytes(path)
            # A task frontier is judged whole: its own gates ARE its live surface, and it has no
            # index to protect. Only a parent gets the register carve-out.
            size = budgeted if kind == "parent" else total
            state = "OVER" if size > lim else ("WATCH" if size > tgt else "ok")
            rows.append((state, kind, path, size, tgt, lim, total, reg, exempt))

    worst, reg_flags = 0, []
    for state, kind, path, size, tgt, lim, total, reg, exempt in rows:
        if state == "ok" and args.quiet and reg <= args.register_soft:
            continue
        label = "budgeted" if kind == "parent" else "bytes"
        print(f"{state:5} {kind:6} {size:6}B {label}  target {tgt}B  signal {lim}B  {path}")
        if kind == "parent":
            print(f"        of {total}B total: register {reg}B, index/ledger {exempt}B, "
                  f"budgeted {size}B")
            if reg > args.register_soft:
                reg_flags.append((path, reg))
        if args.since:
            print(f"        since {args.since}: {delta_since(path, args.since, kind)}")
        if state != "ok" and args.sections:
            secs = sections(path) if args.sections < 0 else sections(path)[:args.sections]
            for head, nbytes in secs:
                if nbytes:
                    print(f"        {nbytes:6}B  {head[:96]}")
        worst = max(worst, {"ok": 0, "WATCH": 1, "OVER": 2}[state])

    for path, reg in reg_flags:
        print(f"\nREGISTER {reg}B in {path} -- above the {args.register_soft}B soft mark, and not a breach.")
        print("The register is resident by decision, so this is a question and not a rule: are the "
              "ALREADY-MITIGATED\nitems still warnings? Those are reference and can move to design/; "
              "the ones that must fire unprompted\nstay. Ask the owner. Never trim history to answer it.")

    if worst == 2:
        print("\nOver the signal. Two responses, cheaper first:")
        print("  1. EXTRACT reference-rather-than-warning material to reference/ or design/.")
        print("  2. SPLIT, when the parent is heavy because it is two efforts wearing one name.")
        print("It never means trimming the task index or deleting history -- a unit held under "
              "budget that way\nhas failed the check it appears to pass. The pressure belongs on "
              "the restated subset and the\ncross-task invariants. A librarian executes the split "
              "inside its own scope and reports it;\nrelocating a grand plan, or inventing a "
              "top-level folder, stays the owner's.")
    elif worst == 1:
        print("\nOver target, under the signal. Nothing to do yet; the section table above is "
              "where the weight is.")
    return worst


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
