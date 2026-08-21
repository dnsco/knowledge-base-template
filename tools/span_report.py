#!/usr/bin/env python3
"""span-report — how long each operation actually takes, against the two-minute north star.

WHY THIS EXISTS
  Goal 4 -- any operation somebody waits on finishes inside two minutes -- had no measurement.
  `pass_log.py` computes `span_s` per pass and `agent_transcript.py` computes tokens; nothing joined
  them, so every claim about efficiency was whichever run someone remembered. Quoting one is how
  `context-dump` kept its pre-redesign 264/368/420 s reputation while actually running 117, 39, 97 s.

  ** It always exits 0, including when everything misses. ** Twice this target hardened into a limit
  and did damage: scoped as the frontier-clerk's ceiling, which a fan-out pass at
  `max(child) + overhead` can never meet, and as "every required step is wall clock spent against the
  budget", withdrawn for discouraging the tools that make rules fire. A check that fails is how it
  happens a third time. An operation over the star is a fact to look at, not a build to break.

WHAT IT CANNOT SEE, and prints
  A read-only operation opens no pass. `pickup` -- likeliest to be inside the star -- is therefore
  invisible here, and its figures come from a transcript profile instead. An unannounced gap reads
  as a clean result.

CONTRACT
  exit 0  always, on a valid invocation -- including when every operation misses the star
  exit 5  bad invocation
"""

import argparse
import datetime
import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vault_config     # noqa: E402

NORTH_STAR_S = 120

# Operations a person is blocked on are judged against the star. Everything else is exempt --
# an eval or a profiling run is development work, settled 2026-08-20.
EXEMPT_KINDS = {"eval", "profile", "probe"}
EXEMPT_ROLES = {"scout"}          # recon in a discarded context; nobody waits on it in-session


def load(path):
    out = []
    try:
        with open(path) as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        out.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    except FileNotFoundError:
        return None
    return out


def pair_passes(records):
    """Join start/stop by pass id. Returns (completed, dangling).

    A `start` with no `stop` is an agent that died, not a fast pass -- it must never be read as a
    zero. It goes in `dangling` and gets printed.
    """
    starts, stops = {}, {}
    for r in records:
        pid = r.get("id")
        if not pid:
            continue
        if r.get("event") == "start":
            starts[pid] = r
        elif r.get("event") == "stop":
            stops[pid] = r
    completed, dangling = [], []
    for pid, s in starts.items():
        if pid in stops and stops[pid].get("span_s") is not None:
            completed.append((s, stops[pid]))
        else:
            dangling.append(s)
    completed.sort(key=lambda p: p[0].get("ts", ""))
    dangling.sort(key=lambda r: r.get("ts", ""))
    return completed, dangling


def exempt(start):
    return start.get("kind") in EXEMPT_KINDS or start.get("role") in EXEMPT_ROLES


def bar(span, width=28):
    """Where this span sits against the star. Visual, so a miss is obvious without arithmetic."""
    filled = min(width, max(1, round(span / NORTH_STAR_S * width)))
    if span <= NORTH_STAR_S:
        return "▇" * filled + "·" * (width - filled)
    return "▇" * width + "»"


def since_cutoff(days):
    if not days:
        return None
    return (datetime.datetime.now(datetime.timezone.utc)
            - datetime.timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")


def main(argv):
    ap = argparse.ArgumentParser(add_help=True, description=__doc__.splitlines()[0])
    ap.add_argument("--scope", help="only passes overlapping this scope")
    ap.add_argument("--role", help="only this role")
    ap.add_argument("--days", type=int, help="only the last N days")
    ap.add_argument("--each", action="store_true", help="every pass, not just the per-role summary")
    ap.add_argument("--vault", help="override the resolved vault")
    args = ap.parse_args(argv)

    vault = vault_config.resolve_or_exit(args.vault, "span_report")
    log_path = os.path.join(str(vault.path), "pass-log.jsonl")
    records = load(log_path)

    if records is None:
        print(f"no pass log at {log_path}")
        print("NOTHING WAS MEASURED -- no operation has recorded a pass in this vault.")
        return 0

    cutoff = since_cutoff(args.days)
    kept = []
    for r in records:
        if args.scope and args.scope not in (r.get("scope") or ""):
            continue
        if args.role and r.get("role") != args.role:
            continue
        if cutoff and (r.get("ts") or "") < cutoff:
            continue
        kept.append(r)

    completed, dangling = pair_passes(kept)

    print(f"north star {NORTH_STAR_S}s · aspirational, for operations a person waits on · "
          f"{len(completed)} completed pass(es)")
    print(f"log: {log_path}\n")

    if not completed:
        print("NOTHING WAS MEASURED for this filter.")
    else:
        by_role = defaultdict(list)
        for s, st in completed:
            by_role[(s.get("role", "?"), exempt(s))].append((s, st))

        if args.each:
            for s, st in completed:
                tag = "exempt" if exempt(s) else ("ok" if st["span_s"] <= NORTH_STAR_S else "OVER")
                print(f"  {s.get('ts','?')}  {s.get('role','?'):14} {s.get('kind','?'):6} "
                      f"{st['span_s']:>5}s  {bar(st['span_s'])}  {tag}")
            print()

        print(f"  {'operation':<16} {'n':>3} {'median':>7} {'worst':>7} {'inside':>8}   series")
        for (role, is_exempt), passes in sorted(by_role.items()):
            spans = sorted(st["span_s"] for _, st in passes)
            med = spans[len(spans) // 2]
            inside = sum(1 for v in spans if v <= NORTH_STAR_S)
            label = f"{role} (exempt)" if is_exempt else role
            verdict = "—" if is_exempt else f"{inside}/{len(spans)}"
            series = ", ".join(str(v) for v in
                               [st["span_s"] for _, st in passes][-8:])
            print(f"  {label:<16} {len(spans):>3} {med:>6}s {spans[-1]:>6}s {verdict:>8}   {series}")

    # --- what was NOT measured. An unannounced gap reads as a clean result. ---
    print("\nnot measured here:")
    print("  · `pickup` — read-only, so it opens no pass and has no span in this log.")
    print("    It is the operation most likely to be inside the star and this tool cannot see it;")
    print("    its figures come from a transcript profile instead.")
    print("  · tokens — `lipika agent-transcript <id> --tokens`, per run. The pass log has no")
    print("    token field, deliberately: emitting metrics from an operating agent was ruled out")
    print("    2026-08-19 as spending the very budget it would be reporting.")
    if dangling:
        print(f"  · {len(dangling)} pass(es) started and never stopped — an agent that died, "
              f"NOT a fast pass:")
        for r in dangling[-5:]:
            print(f"      {r.get('ts','?')}  {r.get('role','?')}  {r.get('scope') or '(vault)'}")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except SystemExit:
        raise
    except BrokenPipeError:
        sys.exit(0)
