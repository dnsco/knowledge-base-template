#!/usr/bin/env python3
"""
Closure check — which tasks look closeable, and does a rollover lose what was still live.

WHY IT EXISTS
  Measured 2026-08-20: three live tasks in one workstream, every workstream in the vault
  `status: active`, four ledger files in `done/` and ZERO closed task folders. Nothing had ever
  closed. The cause was not compliance -- no role was chartered to close a task, because closing
  one needs a SUCCESSOR to hold what is still live, and "never infer completion" (correct about
  items) had been read as covering task closure too. Those are different judgements: whether a
  thing landed, versus whether the remaining work still describes this task.

  So closure became a librarian capability, and this is its gate. The two guarantees it buys are
  the only two things closure can destroy:

    LOSSLESSNESS       -- every fact survives the move. `recall-check` owns that half.
    COHESION OF NEXT   -- every item that was still live is still live somewhere a reader will
                          look. This tool owns that half, and nothing else checked it.

  A rule written into a definition has failed to fire in this system repeatedly, which is why
  this is an exit code and not a paragraph.

TWO MODES

  --scan <workstream>            which tasks look closeable, with the evidence
      A heuristic and it says so. Authority to ASK whether a task is closed, never to close it --
      the same standing a merged PR has in the scout's `closure` brief. It prints the landed
      fraction, the residue that would have to carry across, and the live typed-register entries,
      so the answer to "is this closeable" arrives with the rollover manifest already written.

  <task-dir> --into <successor>   refuse a rollover that drops live work
      Residue is every list item in the closing frontier that does NOT carry a done-marker, plus
      every live typed-register entry ([GATE] / [LANDMINE] / [OPEN Q] / [DEAD END] not marked
      resolved). Each must appear in the successor -- matched on identifying material (PR ref,
      sha, backticked name, filename) where the item has any, on content-word overlap where it
      does not. The successor must also cite the closing task, or the chain back to the archived
      detail is broken.

WHY MATCHING IS FUZZY, DELIBERATELY
  A carried item is meant to be REWORDED -- carry-across is selection, not transcription, and the
  conventions say rewording is free so long as the fact survives. A checker demanding string
  equality would forbid the thing it is checking. So: identifiers are hard evidence, prose is
  scored, and a weak score is reported (exit 1) rather than failed. Exit 2 is reserved for
  residue with NO trace in the successor at all, which is the only unambiguous loss.

USAGE
  python3 closure_check.py --scan workstreams/<ws> [--landed-fraction 0.6] [--min-landed 3]
  python3 closure_check.py workstreams/<ws>/<task>/ --into workstreams/<ws>/<successor>/
  python3 closure_check.py --scan workstreams/<ws> --json

EXIT CODES
  scan mode   0  no task looks closeable
              1  at least one candidate -- read the evidence, then decide
  gate mode   0  every residue item is accounted for in the successor
              1  carried, but one or more matched only weakly -- read those and judge
              2  a defect: residue with no trace in the successor, or no citation of the closing
                 task. The rollover would take live work dark
  both        5  bad invocation
"""

import argparse
import json
import os
import re
import sys

import markers

DATED_DOC = re.compile(r"^\d{4}-\d{2}-\d{2}-.*\.md$")
TASK_DIR = re.compile(r"^\d{4}-\d{2}-\d{2}-")
RESOLVED = re.compile(r"\b(resolved|mitigated|discharged|closed|fixed|dead)\b", re.I)
# Heading names vary across real frontiers -- measured: "What's next", "Open questions this task
# owns", "Dead ends this task ruled out". Open questions are residue too, so they are listed here.
NEXT_SECTIONS = ("what's next", "whats next", "next", "in flight", "in-flight", "open question")



def frontier_of(task_dir):
    """The task's own frontier: the one undated .md at its top level."""
    if not os.path.isdir(task_dir):
        return None
    cands = [f for f in sorted(os.listdir(task_dir))
             if f.endswith(".md") and not DATED_DOC.match(f)]
    if not cands:
        return None
    named = TASK_DIR.sub("", os.path.basename(task_dir.rstrip("/"))) + ".md"
    return os.path.join(task_dir, named if named in cands else cands[0])


def live_tasks(ws_dir):
    out = []
    for entry in sorted(os.listdir(ws_dir)):
        sub = os.path.join(ws_dir, entry)
        if os.path.isdir(sub) and TASK_DIR.match(entry):
            f = frontier_of(sub)
            if f:
                out.append((sub, f))
    return out


def residue(text):
    """(next_items, live_risks) — what a rollover would have to carry forward.

    next_items: list items under a what's-next heading carrying no done-marker.
    live_risks: typed-register entries not marked resolved.
    """
    nxt = [t for _, _, t in markers.list_items(text, NEXT_SECTIONS)
           if markers.state(t) != markers.DONE_STATE]
    risks = []
    # Typed entries are swept from the WHOLE document, not from a named section: measured, three
    # real frontiers spelled that section three different ways, and a typed entry identifies
    # itself. A section list would have found 0 of 11 in two of them.
    for _, _, t in markers.list_items(text):
        kind = markers.typed_kind(t)
        if not kind:
            continue
        # A DEAD END is permanently live: its whole purpose is to keep firing so nobody
        # re-treads it. Resolution does not apply to it, so `RESOLVED` must not silence it.
        if kind != "DEAD END" and RESOLVED.search(t):
            continue
        risks.append(t)
    # An item can be reached twice -- a typed entry sitting under an "Open questions" heading is
    # both residue and a typed entry. Dedupe on the text, keeping first sight, so the counts are
    # the number of distinct things that must carry across.
    seen, nxt_u, risks_u = set(), [], []
    for src, dst in ((nxt, nxt_u), (risks, risks_u)):
        for t in src:
            key = re.sub(r"\s+", " ", t).strip()
            if key in seen:
                continue
            seen.add(key)
            dst.append(t)
    return nxt_u, risks_u


def landed(text, task_dir):
    """Evidence that a sizeable corpus finished — counted from the task's DUMPS, not only its
    frontier.

    This is the correction that made the heuristic work at all. A frontier is DRAINED as work
    lands: a clerk strikes the item and files it in `done/`, so the finished work has already
    left the document you would measure. Measured on three real tasks, frontier-only counting
    reported 12-40% landed for tasks carrying 29, 86 and 105 done-markers in their dumps.
    """
    out = [t for _, _, t in markers.list_items(text, NEXT_SECTIONS)
           if markers.state(t) == markers.DONE_STATE]
    for name in sorted(os.listdir(task_dir)):
        if not DATED_DOC.match(name):
            continue
        body = open(os.path.join(task_dir, name), encoding="utf-8").read()
        out += [t for _, _, t in markers.list_items(body)
                if markers.state(t) == markers.DONE_STATE and markers.LEADING_DONE.match("- " + t)]
    return out


def match_one(item, hay_sig, hay_hard):
    """('ident'|'strong'|'weak'|'missing', detail) for one residue item against a successor.

    A shared hard identifier is evidence only ALONGSIDE overlapping language. Measured: two
    unrelated frontiers in one workstream both name `CLAUDE.md` and `librarian.md`, and an
    identifier-alone rule passed 12 of 12 residue items that were nowhere in the successor. So
    the identifier localizes and the prose corroborates; neither decides alone.
    """
    hit = markers.idents(item, hard=True) & hay_hard
    sig = markers.significant(item)
    score = markers.overlap(sig, hay_sig)
    detail = f"{score:.0%} of content words"
    if hit:
        detail = f"{', '.join(sorted(hit)[:3])} + {detail}"
    if hit and score >= 0.25:
        return "ident", detail
    if score >= 0.6:
        return "strong", detail
    if hit or score >= 0.35:
        return "weak", detail
    return "missing", detail


def one_line(text, width=96):
    t = re.sub(r"\s+", " ", text).strip()
    return t if len(t) <= width else t[:width - 1] + "…"


def scan(ws_dir, frac, min_landed, as_json):
    tasks = live_tasks(ws_dir)
    if not tasks:
        print(f"skip  no dated task folder in {ws_dir} — nothing to scan "
              f"(an unconverted workstream has no tasks yet)")
        return 0, []
    rows, worst = [], 0
    for task_dir, frontier in tasks:
        text = open(frontier, encoding="utf-8").read()
        nxt, risks = residue(text)
        done = landed(text, task_dir)
        dumps = len([n for n in os.listdir(task_dir) if DATED_DOC.match(n)])
        total = len(done) + len(nxt)
        f = (len(done) / total) if total else 0.0
        cand = total and len(done) >= min_landed and f >= frac
        rows.append({
            "task": os.path.relpath(task_dir, os.path.dirname(ws_dir.rstrip("/"))),
            "frontier_bytes": len(text.encode()),
            "dumps": dumps,
            "landed": len(done), "residue": len(nxt), "landed_fraction": round(f, 2),
            "live_risks": len(risks), "candidate": bool(cand),
            "carry_forward": [one_line(t) for t in nxt] + [one_line(t) for t in risks],
        })
        if cand:
            worst = 1
    if as_json:
        print(json.dumps(rows, indent=2))
        return worst, rows
    for r in rows:
        label = "CANDIDATE" if r["candidate"] else "live"
        print(f"{label:10} {r['task']}  ({r['frontier_bytes']} B)")
        print(f"           {r['landed']} landed / {r['residue']} open "
              f"= {r['landed_fraction']:.0%} landed · {r['live_risks']} live typed entries "
              f"· {r['dumps']} dumps")
        if r["candidate"]:
            print("           would have to carry across:")
            for line in r["carry_forward"]:
                print(f"             · {line}")
    if worst:
        print("\nA landed fraction is a HEURISTIC — authority to ask whether the task is closed, "
              "never\nto close it. Closing is a librarian's, and its gate is "
              "`closure-check <task> --into <successor>`.")
    return worst, rows


def gate(task_dir, successor, as_json):
    closing = frontier_of(task_dir)
    if not closing:
        print(f"no task frontier in {task_dir}", file=sys.stderr)
        return 5
    succ_frontier = frontier_of(successor)
    if not succ_frontier:
        print(f"no successor frontier in {successor} — a task closes by opening its successor, "
              f"so the successor has to exist first", file=sys.stderr)
        return 5

    closing_text = open(closing, encoding="utf-8").read()
    succ_text = open(succ_frontier, encoding="utf-8").read()
    succ_sig = markers.significant(succ_text)
    succ_hard = markers.idents(succ_text, hard=True)
    nxt, risks = residue(closing_text)

    findings, worst = [], 0
    for kind, items in (("open item", nxt), ("live risk", risks)):
        for item in items:
            how, detail = match_one(item, succ_sig, succ_hard)
            if how == "missing":
                worst = max(worst, 2)
            elif how == "weak":
                worst = max(worst, 1)
            findings.append({"kind": kind, "match": how, "detail": detail,
                             "item": one_line(item)})

    # The chain back: the successor must cite the closing task, or the archived detail is
    # unreachable from anything a reader opens. A live document points at what was archived
    # out of it -- this is that invariant, at the one moment it can be checked.
    closing_name = os.path.basename(os.path.dirname(closing + "/x")) or ""
    stem = os.path.splitext(os.path.basename(closing))[0]
    cites = (stem in succ_text) or (os.path.basename(task_dir.rstrip("/")) in succ_text)
    if not cites:
        worst = max(worst, 2)

    if as_json:
        print(json.dumps({"closing": closing, "successor": succ_frontier,
                          "cites_closing_task": cites, "findings": findings,
                          "exit": worst}, indent=2))
        return worst

    print(f"closing    {closing}")
    print(f"successor  {succ_frontier}")
    print(f"residue    {len(nxt)} open item(s), {len(risks)} live typed entr(ies)\n")
    order = {"missing": 0, "weak": 1, "strong": 2, "ident": 3}
    for f in sorted(findings, key=lambda f: order[f["match"]]):
        label = {"missing": "MISSING", "weak": "JUDGE", "strong": "ok", "ident": "ok"}[f["match"]]
        print(f"{label:8} {f['kind']:9} {f['item']}")
        print(f"         matched: {f['match']} ({f['detail']})")
    if not cites:
        print(f"MISSING  citation  the successor names neither {stem!r} nor "
              f"{os.path.basename(task_dir.rstrip('/'))!r}")
        print("         a live document must point at what was archived out of it, or the "
              "detail is unreachable")
    if worst == 2:
        print("\nexit 2 — this rollover would take live work dark. Carry the MISSING items into "
              "the\nsuccessor's `## Carried across`, cited by source, then re-run. Losslessness is "
              "the\nother half and is `recall-check`'s: this tool says nothing about it.")
    elif worst == 1:
        print("\nexit 1 — every item has a trace, but the JUDGE rows matched on prose alone. Read "
              "them\nand say in writing that the fact survived; a rewording is fine, a near-miss "
              "is not.")
    else:
        print("\nexit 0 — every residue item is accounted for, and the successor cites the closing "
              "task.")
    return worst


def main(argv):
    ap = argparse.ArgumentParser(
        description="Which tasks look closeable, and does a rollover drop live work.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""TWO MODES

  --scan <ws>                      candidates + the rollover manifest. exit 1 = candidates
  <task-dir> --into <successor>    the gate. exit 2 = residue with no trace in the successor

Residue is every what's-next item without a done-marker, plus every live typed-register entry.
A DEAD END is always live -- it exists to keep firing. Matching is fuzzy on purpose: a carried
item is meant to be reworded, so identifiers are hard evidence and prose is scored.

Closure is a librarian's call. This tool refuses a lossy one; it never makes the call.""")
    ap.add_argument("target", nargs="?", help="a task directory (gate mode)")
    ap.add_argument("--scan", metavar="WORKSTREAM", help="scan a workstream for candidates")
    ap.add_argument("--into", metavar="SUCCESSOR", help="the successor task directory")
    ap.add_argument("--landed-fraction", type=float, default=0.6,
                    help="scan: fraction of items landed to raise a candidate (default 0.6)")
    ap.add_argument("--min-landed", type=int, default=3,
                    help="scan: minimum landed items to raise a candidate (default 3)")
    ap.add_argument("--json", action="store_true")
    import vault_config
    vault_config.add_argument(ap)
    args = ap.parse_args(argv)
    vault = vault_config.resolve_or_exit(getattr(args, "vault", None), "closure_check")

    if args.scan:
        ws = vault_config.anchor(args.scan, vault) or args.scan
        if not os.path.isdir(ws):
            print(f"no such workstream: {args.scan}", file=sys.stderr)
            return 5
        code, _ = scan(ws, args.landed_fraction, args.min_landed, args.json)
        return code

    if not args.target or not args.into:
        ap.print_usage(sys.stderr)
        print("\ngive --scan <workstream>, or <task-dir> --into <successor-dir>", file=sys.stderr)
        return 5
    task = vault_config.anchor(args.target, vault) or args.target
    succ = vault_config.anchor(args.into, vault) or args.into
    for p, what in ((task, "task"), (succ, "successor")):
        if not os.path.isdir(p):
            print(f"no such {what} directory: {p}", file=sys.stderr)
            return 5
    return gate(task, succ, args.json)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
