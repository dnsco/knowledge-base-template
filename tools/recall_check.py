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
                         <path>. The old side always comes from <git-ref>:<path>.
  --mode all|imperative  (default imperative)
  --threshold FLOAT      fraction of content words allowed to be absent (default 0.15)

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
import subprocess
import sys

KEEP = re.compile(r"\b(never|must|don't|do not|always|only|halt|stop)\b", re.I)


def flatten(s):
    return " ".join(re.sub(r"[*`_\[\]]", "", s).split())


def content(s):
    return {w.lower() for w in re.findall(r"[A-Za-z][A-Za-z'-]{4,}", s)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ref")
    ap.add_argument("path")
    ap.add_argument("--into", action="append", metavar="PATH",
                    help="where the content should now live; repeatable (default: <path>)")
    ap.add_argument("--mode", choices=["all", "imperative"], default="imperative")
    ap.add_argument("--threshold", type=float, default=0.15)
    a = ap.parse_args()

    old = subprocess.run(["git", "show", f"{a.ref}:{a.path}"],
                         capture_output=True, text=True)
    if old.returncode:
        sys.exit(old.stderr.strip())
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

    print(f"{len(sents)} {a.mode} sentences in {a.ref}:{a.path}"
          f" -> {', '.join(targets)}\n")
    for s, missing in flagged:
        print(f"  {s[:170]}")
        print(f"     absent: {missing}\n")
    print(f"{len(flagged)} flagged at threshold {a.threshold}")
    sys.exit(1 if flagged else 0)


if __name__ == "__main__":
    main()
