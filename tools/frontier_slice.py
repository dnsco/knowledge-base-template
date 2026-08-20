#!/usr/bin/env python3
"""
Frontier slice — the mutable part of a plan-of-record, without the prose around it.

WHY
  The clerk's cost floor is structural: it must read the whole folder-note on every dump, and a
  mature folder-note is tens of KB. Measured 2026-08-18: one frontier at 41KB (~10k tokens) with
  a best-case clerk run of 48,811 tokens / 13 calls / 117s, of which nine calls were `sed -n`
  ranges paging through that file looking for the parts it is allowed to touch.

  But the clerk only ever edits four things: a frontmatter `status`, a line carrying a state
  marker, a typed risk item, and an ordered "what's next" entry. Everything else in a folder-note
  is orienting prose it must not rewrite. So hand it those, with line numbers, and the paging
  disappears -- along with the temptation to read prose it has no licence to change.

  Line numbers are the point. They make the output an index INTO the file rather than a
  substitute for it, so the clerk still edits the real doc with a uniquely-anchored replacement.

WHAT IT ACTUALLY SAVES — MEASURED, BECAUSE THE HEADLINE NUMBER IS THE SMALL ONE
  On a 41,430-char folder-note:
    whole-file slice              28,060 chars   68.3%   <- only a third off
    --section "What's next"       10,413 chars   25.1%
    --section "Gates in force"     3,829 chars    9.2%
  A mature frontier is MOSTLY markers and typed risks, so dropping prose barely helps. The win
  is `--section`: fetch the one block you were sent to reconcile. Reach for the section form
  first, and treat the whole-file slice as orientation rather than as the saving.

WHAT COUNTS AS MUTABLE
  - the frontmatter block, always
  - any line carrying a state marker: done / in-flight / not-started / superseded
  - any line opening a typed risk item: GATE, LANDMINE, OPEN Q, DEAD END
  - any heading, so the caller can see the shape and ask for a section by name
  - continuation lines of a matched item, so a wrapped marker line is not truncated mid-sentence

USAGE
  python3 tools/frontier_slice.py <folder-note.md> [--section 'What's next'] [--stats]
  python3 tools/frontier_slice.py <note> --find PATTERN [--context N]     # where is X mentioned
  python3 tools/frontier_slice.py <note> --lines 55,120 --lines 380,410   # numbered ranges, batched
  python3 tools/frontier_slice.py <note> --numbered                       # the whole file, numbered

    exit 0   printed
    exit 1   --find matched nothing
    exit 5   no such file, or a --lines range that is not A,B

WHY --lines AND --numbered EXIST: A RESTRUCTURE CANNOT USE --section
  Measured on the first pass under the mandate (2026-08-19): a librarian told to slice ran the tool
  ZERO times and read 137% of a 55,990 B folder-note through six `sed`/`awk` pages and three
  anchored reads -- worse than the 92% an unmandated clerk managed. The reason was not defiance. Its
  diff had TWENTY hunks spanning lines 55-597, and `--section` serves one section at a time, so the
  mandate as written was unsatisfiable for the work in front of it. An unsatisfiable requirement
  teaches an agent to ignore the tool, which is worse than having no requirement.

  So: `--lines` takes batched ranges in one call, and `--numbered` prints the whole file with line
  numbers for the case where the honest answer is that the pass needs all of it. Declaring that is
  the point -- a pass that prints the whole file has said so, where six `sed` pages say nothing.
"""

import argparse
import re
import sys
from pathlib import Path

MARKERS = re.compile(r"(✅|⏳|▢|⚠️|🔲|❌)")
# BOTH spellings. The bracketed form was the only one matched, and the bold-prefix form is live in
# real notes -- measured, 18 typed items in one folder-note and 8 in another were invisible to this
# slice, i.e. it silently omitted exactly the lines a clerk is allowed to edit. Normalising the
# corpus to one spelling was considered and declined (the convention emerged rather than being
# designed), so reading both IS the settled resolution here, not a stopgap.
TYPED = re.compile(r"\[(GATE|LANDMINE|OPEN Q|DEAD END)\]|\*\*(GATE|LANDMINE|OPEN Q|DEAD END)\b")
HEADING = re.compile(r"^(#{1,6})\s+(.*)")
# A wrapped item continues while the line is indented and non-empty and starts no new item.
CONT = re.compile(r"^\s+\S")
ITEM = re.compile(r"^\s*([-*+]|\d+\.)\s")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--section", default=None,
                    help="restrict to one heading's body (matched case-insensitively, as a substring)")
    ap.add_argument("--stats", action="store_true", help="print the size reduction and nothing else")
    ap.add_argument("--find", action="append", default=[], metavar="PATTERN",
                    help="every line matching PATTERN (case-insensitive regex), with line numbers; "
                         "repeatable. Use this INSTEAD of paging with sed -- one call, many needles.")
    ap.add_argument("--context", type=int, default=0, metavar="N",
                    help="with --find, also print N lines either side of each hit")
    ap.add_argument("--lines", action="append", default=[], metavar="A,B",
                    help="print lines A through B with numbers; repeatable, so a restructure "
                         "touching nine sections is ONE call rather than nine sed pages")
    ap.add_argument("--numbered", action="store_true",
                    help="the whole file with line numbers. For a pass that genuinely needs all of "
                         "it -- and saying so is the point")
    args = ap.parse_args()
    import vault_config
    args.path = vault_config.anchor(args.path) or args.path

    p = Path(args.path).expanduser()
    if not p.is_file():
        print(f"no such file: {p}", file=sys.stderr)
        return 5
    lines = p.read_text(errors="replace").splitlines()

    if args.lines or args.numbered:
        want = []
        for spec in args.lines:
            try:
                a, b = (int(x) for x in spec.split(",", 1))
            except ValueError:
                print(f"--lines takes A,B (two integers), not {spec!r}", file=sys.stderr)
                return 5
            want.append((max(1, a), min(len(lines), b)))
        if args.numbered:
            want = [(1, len(lines))]
        shown, prev = 0, 0
        for a, b in sorted(want):
            if prev and a > prev + 1:
                print(f"     … {a - prev - 1} line(s)")
            for i in range(max(a, prev + 1), b + 1):
                print(f"{i:5}\t{lines[i - 1]}")
                shown += 1
            prev = max(prev, b)
        total = len(lines)
        pct = 100.0 * shown / total if total else 0
        print(f"\n{shown} of {total} line(s) ({pct:.0f}%) of {p.name}. Line numbers index the real "
              f"file: edit it with a uniquely-anchored replacement, not from this output.")
        return 0

    # --find: the anti-paging mode. Measured on one clerk run -- 7 separate Bash round trips
    # doing `sed -n '117,152p'`-style line-range guessing to locate 5 mentions, ~25KB of a 51KB
    # file re-read by hand, ~60s of a 258s run. The slice's --section could not answer "where is
    # X mentioned", so the agent fell back to guessing ranges. One --find call replaces all of it.
    if args.find:
        pats = [re.compile(pat, re.I) for pat in args.find]
        hits = {i for i, l in enumerate(lines, 1) if any(pt.search(l) for pt in pats)}
        if not hits:
            print(f"no line matches {args.find!r} in {p}")
            return 1
        show = set()
        for i in sorted(hits):
            for j in range(max(1, i - args.context), min(len(lines), i + args.context) + 1):
                show.add(j)
        prev = 0
        for i in sorted(show):
            if prev and i > prev + 1:
                print(f"     … {i - prev - 1} line(s)")
            print(f"{i:5}{'>' if i in hits else ' '}\t{lines[i - 1]}")
            prev = i
        print(f"\n{len(hits)} matching line(s) for {len(pats)} pattern(s); '>' marks a hit.")
        return 0

    # frontmatter
    keep = set()
    if lines and lines[0].strip() == "---":
        for i, l in enumerate(lines[1:], 2):
            keep.add(i - 1)
            keep.add(i)
            if l.strip() == "---":
                break

    # section restriction
    lo, hi = 1, len(lines)
    if args.section:
        needle = args.section.lower()
        start = None
        depth = 0
        for i, l in enumerate(lines, 1):
            m = HEADING.match(l)
            if not m:
                continue
            if start is None and needle in m.group(2).lower():
                start, depth = i, len(m.group(1))
            elif start is not None and len(m.group(1)) <= depth:
                hi = i - 1
                break
        if start is None:
            print(f"no heading matching {args.section!r}", file=sys.stderr)
            return 5
        lo = start

    interesting = []
    for i in range(lo, hi + 1):
        l = lines[i - 1]
        if HEADING.match(l) or MARKERS.search(l) or TYPED.search(l):
            interesting.append(i)

    for i in interesting:
        keep.add(i)
        # pull in the wrapped remainder of the item
        j = i + 1
        while j <= hi and j - 1 < len(lines):
            nxt = lines[j - 1]
            if not nxt.strip():
                break
            if ITEM.match(nxt) or HEADING.match(nxt):
                break
            if not CONT.match(nxt):
                break
            keep.add(j)
            j += 1

    out = sorted(keep)
    if args.stats:
        full = sum(len(l) + 1 for l in lines)
        cut = sum(len(lines[i - 1]) + 1 for i in out)
        pct = (100 * cut / full) if full else 0
        print(f"{p}")
        print(f"  whole file   {len(lines):5} lines  {full:7} chars")
        print(f"  slice        {len(out):5} lines  {cut:7} chars   ({pct:.1f}%)")
        return 0

    prev = 0
    for i in out:
        if prev and i > prev + 1:
            print(f"     … {i - prev - 1} line(s) of prose")
        print(f"{i:5}\t{lines[i - 1]}")
        prev = i
    return 0


if __name__ == "__main__":
    sys.exit(main())
