#!/usr/bin/env python3
"""
Marker-licence check — did a frontier edit claim more than its source entry licenses?

WHY IT EXISTS
  The frontier-clerk may act only on evidence-bearing markers in the dated entry it is
  reconciling. A semantic-correctness audit of one real clerk run found 3 OVERREACH in a
  43-insertion diff -- no fabrications, no lossy strikes, every sha checking out, and yet
  three claims stronger than the entry supported. Every one was the same failure and the
  same direction: UPGRADE.

  The mechanical profiles could not see it. They asked whether the role ran the right tools
  and stayed inside its contract, and answered clean. Nobody re-read the flips against the
  entry. This is that check, with an exit code.

  It does NOT replace the judgement pass. It catches the two mechanical shapes, which are
  the ones that recur, and reports the rest for a reader.

THE THREE RULES
  1. SELF-CONTRADICTION (hard fail, exit 2)
     A line that carries a done-marker AND a weaker marker at the same time. The measured
     instance read "✅ done ... ▢ not started" in a single breath: a parent item flipped to
     done while carrying its own live child inline. Purely syntactic, no judgement needed.

  2. ROLLUP (hard fail, exit 2)
     A list item flipped to done while a more-indented child beneath it is still ▢ or ⏳.
     "Most of it is done" is not done. This is rule 1's structural cousin -- same failure,
     one nesting level out.

  3. UNLICENSED UPGRADE (report, exit 1)
     A line whose marker got stronger, where no marker in the source entry shares enough
     identifying material with it. Fuzzy by nature: reported for a human or a reviewing
     agent to judge, never hard-failed, because the honest cases (a restraint claim, a
     rewording) are common and a check that fails on correct content gets dismissed --
     which then takes the real findings down with it.

  A STATUS WORD THE ENTRY NEVER USES is reported under rule 3 too.

WHAT THIS CATCHES, MEASURED
  Run against the one clerk diff that has been audited by hand (3 OVERREACH found), it
  catches the rollup as a hard DEFECT and reports the "discharged" upgrade. It does NOT
  catch the third -- a landmine flipped to "Mitigated" where the entry used that word only
  about other items. Catching it needs per-item locality, which is not decidable from two
  files, and the rule that tried scored 1 true positive against 3 false ones.

  So: this tool is the floor, not the ceiling. The semantic question -- "is each change
  licensed by a marker in the source?" -- still wants the auditing sub-agent that found all
  three. Run both; they fail differently, which is the point.

USAGE
  python3 marker_licence_check.py <entry.md> <frontier.md> [--base REF] [--vault PATH]

    --base REF   diff the frontier against REF (default: HEAD, i.e. uncommitted edits)
    --json       machine-readable

    exit 0   nothing to answer for
    exit 1   at least one unlicensed-upgrade report -- read them, then judge
    exit 2   a self-contradiction or rollup -- these are defects, not judgement calls
    exit 5   bad invocation

WHAT IT DELIBERATELY DOES NOT DO
  It does not check strikes or removals. A removal's correctness is whether the evidence
  survives somewhere, which is not decidable from two files -- the clerk's own
  losslessness precondition covers it, and the audit found that half clean.
"""
import argparse
import re
import subprocess
import sys

import markers

# Both spellings are live in the corpus: bracketed in some notes, bold-prefix in others.
# Enforcing one everywhere was considered and declined -- the convention emerged rather than
# being designed. So anything counting markers reads both. This is that requirement.
TYPED, DONE, WEAK = markers.TYPED, markers.DONE, markers.WEAK
STRONG_WORD, IDENT = markers.STRONG_WORD, markers.IDENT

RANK_DONE, RANK_WEAK, RANK_NONE = 2, 1, 0


def rank(line):
    """The state a line ASSERTS. A line that talks about markers asserts nothing.

    THE DEFECT THIS FIXES: the tool could not tell a done-marker from a MENTION of one, so
    every line explaining the convention -- "a ✅ done marker is the only authority", a
    heading reading "Settled as direction", a `✅ settled … execution deferred` line about a
    decision rather than about work -- was read as a completion claim and flagged. A check
    that stays red on correct content gets dismissed, and takes the real findings with it.
    """
    if not markers.carries_marker(line):
        return RANK_NONE
    if DONE.search(line):
        return RANK_DONE
    if WEAK.search(line):
        return RANK_WEAK
    return RANK_NONE


def git(vault, *args):
    p = subprocess.run(["git", *args], cwd=vault, capture_output=True, text=True)
    return p.returncode, p.stdout


def added_lines(vault, base, path):
    """The frontier's added/changed lines, with the line they replaced where there is one.

    `base` may be a single ref (diffed against the working tree, the live clerk case) or an
    `A..B` range, which is how you audit a clerk run that already landed.
    """
    if ".." in base:
        a, b = base.split("..", 1)
        code, out = git(vault, "diff", "-U0", a, b, "--", path)
    else:
        code, out = git(vault, "diff", "-U0", base, "--", path)
    added, removed = [], []
    for ln in out.splitlines():
        if ln.startswith("+++") or ln.startswith("---"):
            continue
        if ln.startswith("+"):
            added.append(ln[1:])
        elif ln.startswith("-"):
            removed.append(ln[1:])
    return added, removed


def indent(line):
    return len(line) - len(line.lstrip())


def check(entry_text, frontier_text, added, removed):
    findings = []

    # -- rule 1: self-contradiction, purely syntactic
    for ln in added:
        if not ln.strip():
            continue
        if markers.carries_marker(ln) and DONE.search(ln) and WEAK.search(ln):
            findings.append({
                "rule": "self-contradiction", "severity": "defect", "line": ln.strip()[:200],
                "why": "carries a done-marker and a weaker marker on the same line",
            })

    # -- rule 2: rollup. A done bullet whose deeper-indented following bullet is still weak.
    flines = frontier_text.split("\n")
    added_set = {l.strip() for l in added if l.strip()}
    for i, ln in enumerate(flines):
        if not re.match(r"^\s*[-*\d]", ln) or ln.strip() not in added_set:
            continue
        if rank(ln) != RANK_DONE:
            continue
        base_ind = indent(ln)
        for nxt in flines[i + 1:]:
            if not nxt.strip():
                continue
            if indent(nxt) <= base_ind and re.match(r"^\s*[-*\d]", nxt):
                break
            if indent(nxt) > base_ind and rank(nxt) == RANK_WEAK:
                findings.append({
                    "rule": "rollup", "severity": "defect", "line": ln.strip()[:200],
                    "why": f"flipped to done over a live child: {nxt.strip()[:120]}",
                })
                break

    # -- rule 3: unlicensed upgrade, reported not failed
    entry_done = [l for l in entry_text.split("\n") if rank(l) == RANK_DONE]
    entry_idents = set()
    for l in entry_done:
        entry_idents |= set(IDENT.findall(l))
    entry_words = set(w.lower() for w in STRONG_WORD.findall(entry_text))

    removed_ranks = {r.strip(): rank(r) for r in removed}
    for ln in added:
        if rank(ln) != RANK_DONE or not ln.strip():
            continue
        idents = set(IDENT.findall(ln))
        if idents and not (idents & entry_idents):
            findings.append({
                "rule": "unlicensed-upgrade", "severity": "report", "line": ln.strip()[:200],
                "why": "done-marker whose identifiers appear in no done-marker in the entry: "
                       + ", ".join(sorted(idents)[:4]),
            })
            continue
        used = set(w.lower() for w in STRONG_WORD.findall(ln))
        novel = used - entry_words
        if novel:
            findings.append({
                "rule": "unlicensed-upgrade", "severity": "report", "line": ln.strip()[:200],
                "why": "status word(s) the entry never uses: " + ", ".join(sorted(novel)),
            })

    # A fourth rule was tried and removed: "an upgrade carrying no identifier at all".
    # Measured against the one audited clerk run it fired 4 times for 1 true positive -- it
    # flagged three upgrades the audit judged LICENSED. Kept out on purpose: a check that
    # stays red on correct content gets dismissed, and takes the real findings with it.
    # The finding it would have caught (a landmine flipped to "Mitigated" where the entry
    # used that word only about other items) needs per-item locality, which is not decidable
    # from two files. That one is the auditing sub-agent's, not this tool's.
    _ = removed_ranks
    return findings


def main():
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("entry")
    ap.add_argument("frontier")
    ap.add_argument("--base", default="HEAD")
    ap.add_argument("--vault", default=None,
                    help="vault path or a name from ~/.config/lipika/config.json; "
                         "default: $LIPIKA_VAULT, the config, then this checkout")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("-h", "--help", action="store_true")
    try:
        a = ap.parse_args()
    except SystemExit:
        print(__doc__.strip())
        return 5
    if a.help:
        print(__doc__.strip())
        return 0

    import vault_config
    a.vault = str(vault_config.resolve_or_exit(a.vault, "marker_licence_check"))
    a.entry = vault_config.anchor(a.entry) or a.entry
    a.frontier = vault_config.anchor(a.frontier) or a.frontier

    try:
        entry_text = open(a.entry).read()
        frontier_text = open(a.frontier).read()
    except OSError as e:
        sys.exit(f"{e}")

    added, removed = added_lines(a.vault, a.base, a.frontier)
    if not added:
        print(f"considering: {a.base if '..' in a.base else a.base + '..working tree'} for {a.frontier}\n  no added lines in the diff — nothing to license")
        return 0

    findings = check(entry_text, frontier_text, added, removed)

    if a.json:
        import json
        print(json.dumps({"added": len(added), "findings": findings}, indent=2))
    else:
        # Always state what was considered. A checker that cannot distinguish
        # checked-nothing-wrong from checked-nothing gets trusted when it should not be.
        print(f"considering: {a.base if '..' in a.base else a.base + '..working tree'}, {len(added)} added line(s) in {a.frontier}")
        print(f"             against done-markers in {a.entry}")
        if not findings:
            print("  no unlicensed upgrades, no self-contradictions, no rollups")
        for f in findings:
            tag = "DEFECT" if f["severity"] == "defect" else "report"
            print(f"  [{tag}] {f['rule']}: {f['why']}")
            print(f"           {f['line']}")

    if any(f["severity"] == "defect" for f in findings):
        return 2
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
