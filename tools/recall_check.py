#!/usr/bin/env python3
"""
Recall check — did a rewrite silently drop content?

WHAT IT DOES
  Compares a file's committed version against its current one and reports any sentence
  whose content words largely vanished. Built for the case where prose was reflowed,
  re-labelled or trimmed and a plain diff is too noisy to audit: every line changed, so
  "nothing important was lost" cannot be read off it.

  Two passes, coarse then sharp:
    all       every sentence in the old version
    imperative  only clauses containing never/must/don't/always/only/halt/stop

  The second is the one that matters for an instruction document. The failure mode
  there is not losing prose, it is losing a *rule*.

WHY NOT A GREP CHECKLIST
  Because you write the checklist from the same memory that did the cutting, so it can
  only confirm. This reads the old file and lets it dictate the questions. Used on a
  librarian rewrite it found one dropped guardrail — "uncommitted files must not be
  edited" — that a thirteen-string checklist had passed clean.

USAGE
  python3 tools/recall_check.py <git-ref> <path>
  python3 tools/recall_check.py HEAD~3 agents/librarian.md
  python3 tools/recall_check.py main CLAUDE.md --mode all --threshold 0.25

  A rewrite keeps the path, so <path> is both sides. A *consolidation* does not: the old
  doc is gone and its content is meant to be somewhere else. Name where it went:

  python3 tools/recall_check.py "$LAST" workstreams/x/2026-01-02-journal.md \
      --into workstreams/x/x.md --into workstreams/x/done/2026-01-02-shipped.md

  --into PATH            where the content should now live; repeatable, and a sentence
                         counts as surviving if it survives in ANY of them. Defaults to
                         <path>.
  --mode all|imperative  (default imperative)
  --threshold FLOAT      fraction of content words allowed to be absent (default 0.15)
  --no-merge-base        read the old side at <git-ref> exactly (see below)

WHICH VERSION IS "OLD", AND WHY IT IS NOT ALWAYS <git-ref>
  Resolved in two steps, and the printed header always names the version actually read.

  First merge-base(<git-ref>, HEAD), which covers an agent working on its own branch and is
  a no-op when the ref is already an ancestor of HEAD.

  Then, if the path does not exist there, the commit that ADDED it in <git-ref>..HEAD. This
  is the case a delta pass mostly does and the one the single-ref signature could not
  express: a pass anchors on a tag and consolidates journals that arrived after that tag, so
  `git show <anchor>:<path>` dies on its normal workload. The doc's added state is its
  pre-pass state, because the pass is what changed it next.

  Note for anyone re-deriving this: merge-base alone does NOT fix it. Where the anchor is an
  ancestor of HEAD it resolves to the anchor itself, so it changes nothing — the add-commit
  fallback is what reaches the failing case. --no-merge-base disables both steps.

THE OLD SIDE COMES FROM GIT; THE NEW SIDE COMES FROM DISK
  --into targets are read from the WORKING TREE, not from a ref. That is deliberate — you run
  this to check an edit you have not committed — but it means two runs are only comparable if
  you changed nothing between them.

  This was once recorded as a non-monotonic --threshold: the same five-way split reportedly
  gave 0 flags at 0.15, 1 at 0.45 and 0 at 0.60, which would be a real defect, since raising
  tolerance must never ADD a flag. It is not the threshold. The test is len(missing)/len(words)
  > threshold, which is monotonic by construction, and a sweep over a case with many flags is
  strictly non-increasing: 19, 13, 8, 5, 1, 1 at 0.05 through 0.80. What moved was the input —
  a pass mid-consolidation is still editing the survivors this reads from disk. Re-run after an
  edit and you are checking against different content, and nothing in the output says so.

  So: never compare two runs across an edit, and treat a flag count as a reading of one moment.

OUTPUT
  One block per flagged sentence: the sentence, and the content words with no home
  anywhere in the new file. Exit 1 if anything was flagged.

GOTCHA THIS ENCODES
  Matching is by word, so a faithful reword still flags — "must not be edited" rewritten
  as "leave every file untouched" looks like a loss. Read every flag and judge it; do
  NOT reword the new file to satisfy this script, which is gaming your own test. Absence
  of flags is weak evidence, presence of a flag is a question.
"""

import argparse
import re
import os
import pathlib
import subprocess

GIT_CWD = None   # set from the resolved vault in main(); git must run in the vault
import sys

KEEP = re.compile(r"\b(never|must|don't|do not|always|only|halt|stop)\b", re.I)


def flatten(s):
    return " ".join(re.sub(r"[*`_\[\]]", "", s).split())


def content(s):
    return {w.lower() for w in re.findall(r"[A-Za-z][A-Za-z'-]{4,}", s)}


def rev(*args):
    p = subprocess.run(["git", *args], capture_output=True, text=True, cwd=GIT_CWD)
    return None if p.returncode else (p.stdout.strip() or None)


def exists_at(ref, path):
    p = subprocess.run(["git", "cat-file", "-e", f"{ref}:{path}"], capture_output=True,
                       cwd=GIT_CWD)
    return p.returncode == 0


def resolve_base(ref, path, exact=False):
    """Find the commit holding the PRE-PASS version of path, starting from ref.

    Two steps, and the second is the one that matters.

    merge-base(ref, HEAD) covers an agent on its own branch, and is a no-op when ref is
    already an ancestor of HEAD.

    Then, if path does not exist there at all, fall back to the commit that ADDED it in
    ref..HEAD. This is the case a delta pass mostly does: a pass anchors on a tag and
    consolidates journals that arrived AFTER that tag, so `git show <anchor>:<path>` dies
    on its normal workload. The doc's added state IS its pre-pass state, since the pass is
    what changed it next. Returns (commit, why) so the caller can print which it read —
    reading a different version than you think you are reading is how this check gets
    believed when it proved nothing.
    """
    if exact:
        return ref, "exact"
    base = rev("merge-base", ref, "HEAD") or ref
    why = "exact" if base == rev("rev-parse", ref) else "merge-base with HEAD"
    if exists_at(base, path):
        return base, why
    added = rev("log", "--diff-filter=A", "--format=%H", "-1", f"{base}..HEAD", "--", path)
    if added:
        return added, "the commit that added it after <ref>"
    return base, why


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ref")
    ap.add_argument("path")
    ap.add_argument("--into", action="append", metavar="PATH",
                    help="where the content should now live; repeatable (default: <path>)")
    ap.add_argument("--mode", choices=["all", "imperative"], default="imperative")
    ap.add_argument("--threshold", type=float, default=0.15)
    ap.add_argument("--no-merge-base", action="store_true",
                    help="read the old side at <ref> exactly, not at merge-base(<ref>, HEAD)")
    a = ap.parse_args()
    import vault_config
    global GIT_CWD
    # Follow the file's own repository when it has one -- this question is about a rewrite, not
    # about a vault, and the definitions it most needs to check now live outside the vault.
    _repo = vault_config.repo_for(a.path)
    if _repo:
        GIT_CWD = _repo
        a.path = str(pathlib.PurePath(os.path.relpath(os.path.abspath(a.path), _repo)))
        if a.into:
            a.into = [os.path.relpath(os.path.abspath(i), _repo) for i in a.into]
        os.chdir(GIT_CWD)
    else:
        # No repo at that path — it may have been given relative to the vault root.
        # This tool reads the working tree AND asks git for older versions of the same path, so it
        # needs one path that satisfies both. Working from the vault root is what it always did when
        # it lived there; doing it explicitly is what lets it be invoked from anywhere.
        _v = vault_config.resolve_or_exit(None, "recall_check")
        GIT_CWD = str(_v.path)
        a.path = vault_config.vault_relative(a.path, _v)
        if a.into:
            a.into = [vault_config.vault_relative(i, _v) for i in a.into]
        os.chdir(GIT_CWD)

    base, why = resolve_base(a.ref, a.path, a.no_merge_base)
    old = subprocess.run(["git", "show", f"{base}:{a.path}"], cwd=GIT_CWD,
                         capture_output=True, text=True)
    if old.returncode:
        sys.exit(f"{old.stderr.strip()}\n"
                 f"  resolved <ref> {a.ref} to {base} ({why}); the path is not there, and no\n"
                 f"  commit in <ref>..HEAD added it either. Nothing to recall-check.")
    targets = a.into or [a.path]
    new = ""
    for path in targets:
        try:
            new += "\n" + open(path).read()
        except OSError as e:
            sys.exit(str(e))

    present = {w.lower() for w in re.findall(r"[A-Za-z][A-Za-z'-]{3,}", flatten(new))}
    sents = [flatten(s) for s in re.split(r"(?<=[.;:])\s+|\n\n", flatten(old.stdout))
             if len(s.strip()) > 25]
    if a.mode == "imperative":
        sents = [s for s in sents if KEEP.search(s)]

    flagged = []
    for s in sents:
        words = content(s)
        if not words:
            continue
        missing = sorted(words - present)
        if len(missing) / len(words) > a.threshold:
            flagged.append((s, missing))

    shown = a.ref if why == "exact" else f"{a.ref} -> {base[:9]} ({why})"
    print(f"{len(sents)} {a.mode} sentences in {shown}:{a.path}"
          f" -> {', '.join(targets)}\n")
    for s, missing in flagged:
        print(f"  {s[:170]}")
        print(f"     absent: {missing}\n")
    print(f"{len(flagged)} flagged at threshold {a.threshold}")
    sys.exit(1 if flagged else 0)


if __name__ == "__main__":
    main()
