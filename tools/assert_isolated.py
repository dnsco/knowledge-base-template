#!/usr/bin/env python3
"""
Isolation assertion — am I actually in my own worktree, at the base I was told?

WHY THIS IS A TOOL AND NOT A PARAGRAPH
  The orchestrator's definition mandates worktree isolation and devotes a paragraph to why.
  Measured 2026-08-18: all three sub-librarian spawns carried exactly `description`, `prompt`
  and `subagent_type` — the isolation key was never passed. Every sub-agent ran in the
  orchestrator's own tree and committed to its branch, and the mandatory "HEAD == base" check
  each one dutifully ran PASSED TRIVIALLY and proved nothing. The prose did not fire. Nothing
  failed loudly; the guarantee simply was not there, and the pass reported success.

  So the check moves to where it can refuse. Every sub-agent runs this as its FIRST command.
  A missing isolation key now fails at the sub-agent in one call, instead of being discovered
  thirty calls later by the orchestrator — which is what happened, at a cost of two wasted
  calls and a published misdiagnosis.

THE TWO HALVES ARE COUPLED, AND NEITHER IS SUFFICIENT
  Isolation without a base assertion: isolation has silently handed agents a STALE tree, and in
  a stale tree the delta still computes and still looks clean. Six scopes once ran 16 commits
  behind the base they were told they had, and one found all three journals it was sent to
  consolidate simply absent — left unchecked it would have reported nothing-to-consolidate,
  clean and green, having done nothing.

  A base assertion without isolation: exactly the 2026-08-18 failure. HEAD equals the base
  because you are standing in the tree that defines it.

HOW ISOLATION IS DETECTED
  A linked worktree has its own git dir under the common one, so `--git-dir` and
  `--git-common-dir` differ. In a main checkout they are the same path. That is a git fact, not
  a heuristic, and it costs one subprocess.

USAGE
  python3 tools/assert_isolated.py <base-ref>
  python3 tools/assert_isolated.py <base-ref> --allow-main    # for a role that runs centrally

    exit 0   isolated (or --allow-main) AND HEAD == base AND tree clean
    exit 2   not in a worktree
    exit 3   HEAD is not the base you were given
    exit 4   working tree is dirty
    exit 5   bad invocation, or not a git repository
"""

import argparse
import subprocess
import sys
from pathlib import Path


def git(*args):
    """Run a git command, returning stripped stdout. Raises on failure."""
    r = subprocess.run(["git", *args], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout).strip())
    return r.stdout.strip()


def die(code, *lines):
    for line in lines:
        print(line, file=sys.stderr)
    sys.exit(code)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("base", help="the ref you were told is your base")
    ap.add_argument("--allow-main", action="store_true",
                    help="skip the worktree requirement (for a centrally-running role)")
    ap.add_argument("--allow-dirty", action="store_true",
                    help="skip the clean-tree requirement")
    args = ap.parse_args()

    try:
        git_dir = Path(git("rev-parse", "--absolute-git-dir"))
        common = Path(git("rev-parse", "--path-format=absolute", "--git-common-dir"))
        head = git("rev-parse", "HEAD")
        toplevel = git("rev-parse", "--show-toplevel")
    except RuntimeError as e:
        die(5, f"not a git repository, or git failed: {e}")

    isolated = git_dir != common

    if not isolated and not args.allow_main:
        die(2,
            "NOT ISOLATED — this is a main checkout, not a linked worktree.",
            f"  git dir     {git_dir}",
            f"  common dir  {common}",
            "",
            "Your brief says you run in your own worktree. You do not.",
            "Whoever spawned you did not pass the isolation key, so any 'HEAD == base'",
            "assertion you make from here is self-confirming and proves nothing.",
            "Halt and report this rather than working in a tree you share.")

    try:
        base = git("rev-parse", args.base)
    except RuntimeError:
        die(5, f"base ref does not resolve: {args.base}")

    if head != base:
        try:
            behind = git("rev-list", "--count", f"{head}..{base}")
            ahead = git("rev-list", "--count", f"{base}..{head}")
            drift = f"  {ahead} commit(s) ahead, {behind} behind the base"
        except RuntimeError:
            drift = "  (the two are not comparable — unrelated histories?)"
        die(3,
            "HEAD IS NOT THE BASE YOU WERE GIVEN.",
            f"  base  {args.base}  ->  {base}",
            f"  HEAD                  {head}",
            drift,
            "",
            "In a stale tree the delta still computes and still looks clean, so this",
            "would not have announced itself. Halt; ask for the base you were meant to have.")

    if not args.allow_dirty:
        dirty = git("status", "--porcelain")
        if dirty:
            n = len(dirty.splitlines())
            die(4,
                f"WORKING TREE IS DIRTY — {n} path(s).",
                *[f"  {line}" for line in dirty.splitlines()[:10]],
                "" if n <= 10 else f"  … and {n - 10} more",
                "Uncommitted files break `git show` carry-forward and cannot have their",
                "links repointed. Halt rather than silently voiding those steps.")

    print(f"isolated   {'yes' if isolated else 'no (--allow-main)'}")
    print(f"worktree   {toplevel}")
    print(f"HEAD       {head}  == {args.base}")
    print(f"tree       {'clean' if not args.allow_dirty else 'unchecked (--allow-dirty)'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
