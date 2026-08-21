#!/usr/bin/env python3
"""architecture-candidates — which reference traces are load-bearing across threads and have no portrait.

WHY THIS EXISTS
  `architecture/` holds the owner's portrait of a system: present tense, stable names, no dates. It
  is the only tier an agent may not write, because an agent-authored portrait becomes the
  most-linked document in the vault with no dated evidence positioned to contradict it.

  So the question an agent CAN answer is when one is missing, and "useful across more than one
  thread" is the observable form of that. It is mechanical, and it fires without anyone
  remembering to ask -- which is the difference between this and a line in a skill telling an agent
  to notice.

  It is a heuristic and authority to RECOMMEND, never to write. A pickup's own experience of
  reading cold is the other half of the signal and this tool cannot see it.

CONTRACT
  exit 0  nothing to recommend
  exit 1  candidates, listed with who cites them
  exit 5  bad invocation
"""

import argparse
import os
import re
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import markers          # noqa: E402
import vault_config     # noqa: E402


def md_files(root):
    for dirpath, dirnames, names in os.walk(root):
        dirnames[:] = [d for d in dirnames
                       if not d.startswith(".") and d not in ("obsidian-skills", "node_modules")]
        for n in names:
            if n.endswith(".md"):
                yield os.path.join(dirpath, n)


def stem(path):
    return os.path.splitext(os.path.basename(path))[0]


def thread_of(rel):
    """The workstream a vault-relative path belongs to, or None.

    ONLY a workstream counts. The vault index links every trace by construction, so counting it
    clears the bar for everything and the check answers yes to every question -- measured on the
    first run, 8 of 11 traces reported as candidates on the strength of a README line. A routing
    surface citing something is not a thread depending on it.
    """
    parts = rel.split(os.sep)
    return parts[1] if len(parts) > 2 and parts[0] == "workstreams" else None


def main(argv):
    ap = argparse.ArgumentParser(prog="lipika architecture-candidates", add_help=True)
    ap.add_argument("--vault", default=None)
    ap.add_argument("--min-threads", type=int, default=2,
                    help="how many distinct workstreams must cite a trace before it is a candidate")
    args = ap.parse_args(argv)

    try:
        # resolve() returns a Vault, whose existence is the proof it is one; .path is the str.
        vault = args.vault or str(vault_config.resolve().path)
    except Exception as e:                                # noqa: BLE001
        print(f"cannot resolve the vault: {e}", file=sys.stderr)
        return 5

    arch_dir = os.path.join(vault, "architecture")
    portrayed = set()      # everything the portrait already links to
    nodes = []
    if os.path.isdir(arch_dir):
        for p in md_files(arch_dir):
            nodes.append(stem(p))
            body = open(p, encoding="utf-8", errors="replace").read()
            portrayed |= {t.strip() for t in markers.WIKILINK.findall(body)}

    # Traces: dated documents in any reference/ directory, at the root or under a workstream.
    traces = {}
    for p in md_files(vault):
        rel = os.path.relpath(p, vault)
        if os.sep + "reference" + os.sep in os.sep + rel or rel.startswith("reference" + os.sep):
            traces[stem(p)] = rel

    if not traces:
        print("no reference/ traces in the vault — nothing to recommend a portrait for.")
        return 0

    # Who cites each trace, by thread.
    cited = defaultdict(set)
    for p in md_files(vault):
        rel = os.path.relpath(p, vault)
        if rel.startswith("architecture" + os.sep):
            continue
        body = open(p, encoding="utf-8", errors="replace").read()
        here = thread_of(rel)
        if not here:
            continue                       # routing surfaces and raw inputs do not vote
        for target in markers.WIKILINK.findall(body):
            t = target.strip()
            if t in traces and stem(p) != t:
                cited[t].add(here)

    cands = sorted(((t, srcs) for t, srcs in cited.items()
                    if len(srcs) >= args.min_threads and t not in portrayed),
                   key=lambda kv: (-len(kv[1]), kv[0]))

    print(f"{len(traces)} trace(s) · {len(nodes)} architecture node(s) · "
          f"threshold {args.min_threads} thread(s)")

    if not cands:
        print("\nnothing to recommend: every cross-thread trace is already reachable from a portrait.")
        return 0

    print("\nCANDIDATES — cited across threads, with no architecture node linking them:")
    for t, srcs in cands:
        print(f"  · {t}")
        print(f"      {traces[t]}")
        print(f"      cited from {len(srcs)} threads: {', '.join(sorted(srcs))}")
    print("\nRecommend these to the owner with pointers, and do not write one yourself.")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
