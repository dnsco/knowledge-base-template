#!/usr/bin/env python3
"""
Frontier lag check — has a workstream's plan-of-record fallen behind its own entries?

WHY IT EXISTS
  The dump is append-only and may not touch the frontier; a clerk reconciles it afterwards. The
  guarantee that matters is that a dump cannot report success over a stale frontier. Today that
  is bought by BLOCKING: the dump waits for the clerk. That is a ~2-minute agent in front of the
  system's most frequent action.

  This is the instrument for deciding whether the guarantee can be bought another way. It turns
  "the frontier is behind" from something a human notices into something with an exit code. Run
  it after an unblocked dump, or in any session that wants to know before trusting a frontier.

  It does NOT decide whether the dump should block. It makes the question measurable.

WHAT LAG LOOKS LIKE, MECHANICALLY
  1. ORPHAN ENTRY — a dated doc in the workstream that the folder-note does not link, directly
     or through a doc the folder-note links. An entry nothing points at is one nobody will read.
  2. NEWER ENTRY — an entry whose last commit is newer than the folder-note's last commit. The
     record moved; the register did not.
  3. UNCONSUMED MARKER — a `done`-state marker in an entry naming a PR, commit or gate whose
     identifier appears nowhere in the folder-note. This is the class the clerk exists to move.

  Each is a SIGNAL, not a verdict. A frontier can legitimately not mention a done marker (the
  item may never have been on it). The check reports what it found and which rule fired, so the
  reader judges -- it never edits, and it never infers completion.

USAGE
  python3 tools/frontier_lag_check.py <workstream-dir-or-folder-note> [--vault PATH] [--quiet]

    exit 0   no lag signals
    exit 1   at least one signal -- read them, then decide whether a clerk pass is owed
    exit 5   bad invocation
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

DATED = re.compile(r"^\d{4}-\d{2}-\d{2}-")
WIKI = re.compile(r"\[\[([^\]\n|#]+)")
DONE = re.compile(r"✅")
IDENT = re.compile(r"(#\d{2,6}|\b[0-9a-f]{7,40}\b)")
FROZEN = {"done", "sources", "external", "design"}


def git(vault, *args):
    r = subprocess.run(["git", *args], cwd=vault, capture_output=True, text=True)
    return r.returncode, r.stdout.strip()


def last_commit_epoch(vault, path):
    code, out = git(vault, "log", "-1", "--format=%ct", "--", str(path))
    if code != 0 or not out:
        return None
    try:
        return int(out.splitlines()[0])
    except ValueError:
        return None


def linked_names(text):
    return {m.strip() for m in WIKI.findall(text)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target", help="a workstream directory, or its folder-note")
    ap.add_argument("--vault", default=".")
    ap.add_argument("--quiet", action="store_true", help="only print signals")
    args = ap.parse_args()

    vault = Path(args.vault).expanduser().resolve()
    t = Path(args.target).expanduser()
    if not t.is_absolute():
        t = (vault / t)
    if t.is_dir():
        note = t / f"{t.name}.md"
        wsdir = t
    elif t.is_file():
        note = t
        wsdir = t.parent
    else:
        print(f"no such workstream or folder-note: {t}", file=sys.stderr)
        return 5
    if not note.is_file():
        print(f"no folder-note at {note}", file=sys.stderr)
        return 5

    note_text = note.read_text(errors="replace")
    direct = linked_names(note_text)

    # one hop: a doc the folder-note links may itself link the entry
    reachable = set(direct)
    for p in wsdir.rglob("*.md"):
        if p.stem in direct:
            reachable |= linked_names(p.read_text(errors="replace"))

    entries = []
    for p in sorted(wsdir.rglob("*.md")):
        if p == note:
            continue
        parts = p.relative_to(wsdir).parts
        if FROZEN & set(parts[:-1]):
            continue          # design/ and done/ are not the live record
        if not DATED.match(p.name):
            continue
        entries.append(p)

    signals = []
    note_epoch = last_commit_epoch(vault, note.relative_to(vault))

    for p in entries:
        rel = p.relative_to(vault)
        if p.stem not in reachable:
            signals.append(("ORPHAN ENTRY", f"{rel} — the folder-note does not reach it"))
        e = last_commit_epoch(vault, rel)
        if e and note_epoch and e > note_epoch:
            signals.append(("NEWER ENTRY", f"{rel} — committed after the folder-note last was"))
        elif e and note_epoch is None:
            signals.append(("NEWER ENTRY", f"{rel} — the folder-note has no commit of its own"))

        text = p.read_text(errors="replace")
        for line in text.splitlines():
            if not DONE.search(line):
                continue
            for ident in set(IDENT.findall(line)):
                if len(ident) > 12 and not ident.startswith("#"):
                    ident = ident[:9]          # compare shas by prefix
                if ident not in note_text:
                    signals.append(("UNCONSUMED MARKER",
                                    f"{rel} — done-marker cites {ident}, absent from the folder-note"))

    seen, uniq = set(), []
    for kind, msg in signals:
        if (kind, msg) not in seen:
            seen.add((kind, msg))
            uniq.append((kind, msg))

    if not args.quiet:
        print(f"frontier {note.relative_to(vault)}")
        print(f"entries checked: {len(entries)}\n")
    if not uniq:
        print("no lag signals")
        return 0
    width = max(len(k) for k, _ in uniq)
    for kind, msg in uniq:
        print(f"  {kind:{width}}  {msg}")
    print(f"\n{len(uniq)} signal(s). Each is a signal, not a verdict — a frontier may legitimately")
    print("not carry an item. Read them, then decide whether a clerk pass is owed.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
