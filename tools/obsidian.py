#!/usr/bin/env python3
"""
Obsidian CLI wrapper — answers the query, or refuses. Never a wrong answer.

USAGE
  python3 tools/obsidian.py backlinks <file>      # who links to this doc
  python3 tools/obsidian.py search <query>
  python3 tools/obsidian.py <any obsidian subcommand> [k=v ...]

    exit 0   stdout is the answer
    exit 3   CLI disabled, Obsidian not running, or not installed — message says which
    exit 4   the CLI indexes a different tree than your cwd; nothing was run

WHY A WRAPPER AND NOT A PREFLIGHT
  Two failure modes, and only one of them announces itself.

  Disabled or not running: the CLI prints "Command line interface is not enabled" and exits
  in ~0.00s. Cheap to hit, and the reason is legible — so calling it directly and reading
  the error is fine. This wrapper only translates it into an exit code and the actual fix.

  Indexing a different tree: THE CALL SUCCEEDS. The CLI resolves one configured vault path
  and knows nothing about git worktrees, so from a worktree it confidently answers about
  another tree's committed state. Measured mid-pass: a merged doc that existed only in the
  worktree came back "No matches found", and three docs the pass had already deleted were
  still readable. No error, no signal, a plausible answer.

  That second one is why "just try it and check for failure" is not enough, and why this
  refuses rather than warns. Accurate data about the wrong quantity is the failure class
  this vault exists to prevent, and a silent success is worse than no tool.

WHEN IT REFUSES WITH EXIT 4
  That is the normal, correct state inside a worktree — not something to fix by enabling
  anything. Use `grep` over your own tree. Note grep is not identical: `grep -rln '[[x]]'`
  counts a file's own self-links, which `backlinks` correctly excludes, so drop the file
  itself from grep's result.

WHY IT IS WORTH REACHING FOR AT ALL
  On the tree it does index: `backlinks` ~0.02s from Obsidian's resolved index, and
  `search` ~0.01s on a query whose grep equivalent has died with
  "ugrep: exceeds complexity limits" inside a call that ran 105s.
"""

import subprocess
import sys
from pathlib import Path


def die(code, *lines):
    for l in lines:
        print(l, file=sys.stderr)
    sys.exit(code)


def main():
    argv = sys.argv[1:]
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__.strip())
        return 0

    top = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                         capture_output=True, text=True)
    if top.returncode:
        die(3, "not inside a git tree, so the vault cannot be identified")
    here = Path(top.stdout.strip()).resolve()

    def obsidian(*cmd):
        try:
            p = subprocess.run(["obsidian", *cmd], capture_output=True, text=True, timeout=30)
        except FileNotFoundError:
            die(3, "the `obsidian` binary is not on PATH.",
                   "  Install the Obsidian CLI, or use grep over your own tree.")
        except subprocess.TimeoutExpired:
            die(3, "`obsidian` timed out after 30s — treat it as unavailable.")
        blob = f"{p.stdout}\n{p.stderr}"
        if "not enabled" in blob:
            die(3, "the Obsidian CLI is DISABLED, which is its default.",
                   "  Enable it: Obsidian > Settings > General > Advanced > command line interface.",
                   "  App-level, set once, and Obsidian must be running.",
                   "  Until then use grep over your own tree — and say so in your report.")
        if p.returncode:
            die(3, f"`obsidian {' '.join(cmd)}` failed: {(p.stderr or p.stdout).strip()[:200]}")
        return p.stdout

    indexed = None
    for line in obsidian("vault").splitlines():
        parts = line.split("\t")
        if len(parts) == 2 and parts[0].strip() == "path":
            indexed = Path(parts[1].strip()).expanduser().resolve()
    if indexed is None:
        die(3, "`obsidian vault` returned no path field; treat the CLI as unavailable.")

    if indexed != here:
        die(4, "REFUSING: the Obsidian CLI indexes a different tree than the one you are in.",
               f"  it indexes : {indexed}",
               f"  you are in : {here}",
               "  It has no concept of git worktrees, so it would answer about that tree's",
               "  committed state — a doc you just wrote is invisible to it, and a backlink it",
               "  reports may already be deleted here. Use grep over your own tree instead,",
               "  remembering to drop the file itself from a `grep -rln '[[name]]'` result.")

    sys.stdout.write(obsidian(*argv))
    return 0


if __name__ == "__main__":
    sys.exit(main())
