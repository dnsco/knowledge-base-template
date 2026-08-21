#!/usr/bin/env python3
"""orientation-audit — did the newest orientation account for everything the last one held?

WHY THIS EXISTS
  An orientation is a VIEW: rewritten wholesale at every handoff rather than edited. That is what
  makes it cheap, and it is also its one failure mode -- a live item can simply not be written down
  again, and nothing in the document says so. A register that is edited leaves a diff; a document
  that is regenerated leaves nothing.

  So the guarantee is not losslessness (the dumps behind it are immutable and intact) but
  DISPOSITION: every item that was live must appear in the successor as carried, or be recorded as
  resolved, dropped or escalated. A drop is fine -- an unstated drop is not.

  It runs at PICKUP, not at handoff. The handing-off agent is nearly out of budget and auditing its
  own work; the fresh one has a full window and no stake in the answer.

CONTRACT
  exit 0  every prior item accounted for  (also: no predecessor to audit against)
  exit 1  matched on prose alone, or an item carries no `as-of` -- judge these, one line each
  exit 2  an item vanished with no trace in the successor -- a silent drop
  exit 5  bad invocation

  Matching is deliberately fuzzy, the same way `closure-check --into` is: a carried item is MEANT to
  be reworded, so a hard identifier localizes and prose corroborates, and only total absence fails.
"""

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import markers                                    # noqa: E402
from closure_check import one_line                # noqa: E402
import vault_config                               # noqa: E402

ORIENT_DOC = re.compile(r"^\d{4}-\d{2}-\d{2}(-\d{4})?.*\.md$")

LIVE_SECTIONS = ("live items", "needs the owner")
# The successor accounts for an item by carrying it OR by recording where it went.
ACCOUNTED_SECTIONS = LIVE_SECTIONS + ("settled since", "settled", "resolved", "dropped")

AS_OF = re.compile(r"as[- ]of\s+(\d{4}-\d{2}-\d{2})", re.I)
DIES_WHEN = re.compile(r"\bdies when\b", re.I)
# Scaffolding every item carries. Left in, it is shared vocabulary that inflates the overlap
# between two items that have nothing to do with each other -- measured on the first fixture, a
# deleted LANDMINE scored 43% against a successor that did not mention it.
SCAFFOLD = re.compile(r"\*\*\[?(?:LANDMINE|GATE|DEAD END|OPEN Q|ESCALATED)\]?\*\*|"
                      r"\[(?:LANDMINE|GATE|DEAD END|OPEN Q|ESCALATED)\]|"
                      r"as[- ]of\s+\d{4}-\d{2}-\d{2}|\bdies when\b|[·—]", re.I)


def substance(item):
    """The item with its typed scaffolding removed, for comparison only."""
    return SCAFFOLD.sub(" ", item)


def orientations(ws_dir):
    """Every orientation under the workstream, oldest first. Names sort chronologically."""
    d = os.path.join(ws_dir, "orientation")
    if not os.path.isdir(d):
        return []
    return [os.path.join(d, n) for n in sorted(os.listdir(d)) if ORIENT_DOC.match(n)]


def live_items(text):
    """Typed and untyped items the document presents as live."""
    out, seen = [], set()
    for _, _, t in markers.list_items(text, LIVE_SECTIONS):
        key = re.sub(r"\s+", " ", t).strip()
        if key and key not in seen:
            seen.add(key)
            out.append(t)
    return out


def accounted_items(text):
    """Every successor item that can discharge a prior one, as (raw, significant, hard, soft).

    Compared ITEM BY ITEM, never against the concatenation. An item is carried by *an* item, and
    pooling the successor's whole vocabulary lets shared scaffolding vouch for something nobody
    wrote down.
    """
    out = []
    for _, _, t in markers.list_items(text, ACCOUNTED_SECTIONS):
        sub = substance(t)
        out.append((t, markers.significant(sub),
                    markers.idents(sub, hard=True), markers.idents(sub)))
    return out


def verdict(sub, sig, hard, soft):
    """('ident'|'strong'|'weak'|'missing', detail) for one item against ONE successor item.

    Deliberately not `closure_check.match_one`. That one compares an item against a whole
    successor DOCUMENT, so it needs a hard identifier -- a sha, a PR number, a filename -- before
    it will trust prose, because a big haystack shares vocabulary with everything. Here the
    haystack is a single short item, so a shared BACKTICKED token is already specific enough to
    localize: measured on the fixtures, requiring a hard identifier reported a correctly-recorded
    resolution as needing judgement, and a check that stays red on correct content gets dismissed.
    """
    mine_hard, mine_soft = markers.idents(sub, hard=True), markers.idents(sub)
    hit_hard, hit_soft = mine_hard & hard, mine_soft & soft
    score = markers.overlap(markers.significant(sub), sig)
    detail = f"{score:.0%} of content words"
    if hit_hard or hit_soft:
        shared = sorted(hit_hard or hit_soft)[:3]
        detail = f"{', '.join(shared)} + {detail}"
    if hit_hard and score >= 0.25:
        return "ident", detail
    if hit_soft and score >= 0.35:
        return "ident", detail
    if score >= 0.6:
        return "strong", detail
    if (hit_hard or hit_soft) or score >= 0.35:
        return "weak", detail
    return "missing", detail


def best_match(item, cands):
    """The strongest verdict this item earns against any single successor item."""
    rank = {"ident": 3, "strong": 2, "weak": 1, "missing": 0}
    best, detail = "missing", "no successor item resembles it"
    sub = substance(item)
    for _, sig, hard, soft in cands:
        v, d = verdict(sub, sig, hard, soft)
        if rank[v] > rank[best]:
            best, detail = v, d
    return best, detail


def age_days(item, today):
    m = AS_OF.search(item)
    if not m:
        return None
    from datetime import date
    try:
        a = date(*(int(x) for x in m.group(1).split("-")))
        b = date(*(int(x) for x in today.split("-")))
    except ValueError:
        return None
    return (b - a).days


def main(argv):
    ap = argparse.ArgumentParser(prog="lipika orientation-audit", add_help=True)
    ap.add_argument("scope", help="workstream directory, vault-relative or absolute")
    ap.add_argument("--vault", default=None)
    ap.add_argument("--today", default=None, help="YYYY-MM-DD, for tests")
    ap.add_argument("--stale-days", type=int, default=14,
                    help="an item whose as-of is older than this is reported for re-checking")
    args = ap.parse_args(argv)

    try:
        vault = args.vault or vault_config.resolve()
    except Exception as e:                                    # noqa: BLE001
        print(f"cannot resolve the vault: {e}", file=sys.stderr)
        return 5

    ws = args.scope if os.path.isabs(args.scope) else os.path.join(vault, args.scope)
    if not os.path.isdir(ws):
        print(f"not a directory: {ws}", file=sys.stderr)
        return 5

    if args.today:
        today = args.today
    else:
        from datetime import date
        today = date.today().isoformat()

    docs = orientations(ws)
    if not docs:
        print(f"no orientation/ under {args.scope} — nothing handed off yet.")
        print("The first handoff out of this session creates one.")
        return 0
    if len(docs) == 1:
        print(f"one orientation, no predecessor to audit: {os.path.relpath(docs[0], vault)}")
        cur = open(docs[0], encoding="utf-8").read()
        report_freshness(live_items(cur), today, args.stale_days)
        return 0

    prev_p, cur_p = docs[-2], docs[-1]
    prev = open(prev_p, encoding="utf-8").read()
    cur = open(cur_p, encoding="utf-8").read()

    print(f"current   {os.path.relpath(cur_p, vault)}")
    print(f"previous  {os.path.relpath(prev_p, vault)}")

    prior = live_items(prev)
    if not prior:
        print("\nthe previous orientation held no live items — nothing to account for.")
        report_freshness(live_items(cur), today, args.stale_days)
        return 0

    cands = accounted_items(cur)

    missing, weak = [], []
    for item in prior:
        verdict, detail = best_match(item, cands)
        if verdict == "missing":
            missing.append((item, detail))
        elif verdict == "weak":
            weak.append((item, detail))

    print(f"\n{len(prior)} item(s) live in the previous orientation; "
          f"{len(prior) - len(missing)} accounted for.")

    if missing:
        print("\nDROPPED WITHOUT A DISPOSITION — no trace in the successor:")
        for item, detail in missing:
            print(f"  · {one_line(item)}")
            print(f"      {detail}")
    if weak:
        print("\nMATCHED ON PROSE ALONE — judge each in writing:")
        for item, detail in weak:
            print(f"  · {one_line(item)}")
            print(f"      {detail}")

    unstated = report_freshness(live_items(cur), today, args.stale_days)

    if missing:
        return 2
    if weak or unstated:
        return 1
    print("\nclean: every prior item is carried or its disposition is recorded.")
    return 0


def report_freshness(items, today, stale_days):
    """Print what the reader should re-check before trusting, and whether any item is undateable.

    An item carried unchanged through several handoffs inherits the newest document's name and
    reads as fresh. Its own `as-of` is the only thing that says otherwise, which is why an item
    without one is reported rather than ignored.
    """
    stale, undated, no_death = [], [], []
    for t in items:
        if markers.typed_kind(t) == "DEAD END":
            continue                      # permanently live; freshness does not apply
        age = age_days(t, today)
        if age is None:
            undated.append(t)
        elif age >= stale_days:
            stale.append((age, t))
        if not DIES_WHEN.search(t) and markers.typed_kind(t) not in (None, "DEAD END"):
            no_death.append(t)
    if stale:
        print(f"\nSTALE — as-of is {stale_days}+ days old; re-check before relying on these:")
        for age, t in sorted(stale, reverse=True):
            print(f"  · {age}d  {one_line(t)}")
    if undated:
        print("\nNO as-of — cannot tell how fresh; treat as unconfirmed:")
        for t in undated:
            print(f"  · {one_line(t)}")
    if no_death:
        print("\nNO death condition — nothing says what would retire these:")
        for t in no_death:
            print(f"  · {one_line(t)}")
    return bool(undated)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
