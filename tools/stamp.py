#!/usr/bin/env python3
"""stamp — the UTC filename stamp for a new orientation or dump, checked against what is already there.

WHY THIS EXISTS
  `pickup` opens the LAST orientation by name, so a handoff that does not sort last is never read --
  and the failure is silent at every step: the file writes, the commit succeeds, the handoff reports
  done, and the next session reads a stale document.

  A name is therefore a SEQUENCE KEY, not a timestamp, and this checks SORTING: string comparison
  against the existing names, no date parsing.

  Measured 2026-08-21, of four orientations on one thread, only the first is a UTC timestamp --
  1930 was written at 18:10Z, 2015 at 18:13Z, 2100 at 19:32Z. The names run ahead of the clock and
  the drift compounds; the newest was 88 minutes out. The skill said "stamp from `date`", which is
  local time besides, and would have produced a name sorting before all three.

  --after exists for that drift and is not the default: emitting a monotonic name silently would
  entrench it invisibly, where refusing puts it in front of the writer once per handoff, the only
  moment anyone can decide to reset. A document's real time is its `date:` frontmatter and its
  commit.

CONTRACT
  exit 0  the stamp is printed on stdout, and (with --for) it sorts last in that directory
  exit 1  the stamp would NOT sort last -- the directory holds a name at or after it
  exit 5  bad invocation

USAGE
  lipika stamp                                   # 2026-08-21-2245
  lipika stamp --date                            # 2026-08-21
  lipika stamp --for workstreams/<ws>/orientation      # stamp, checked against what is there
  lipika stamp --for <dir> --after               # ...and if the clock is behind, step past the last
"""

import argparse
import datetime
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vault_config     # noqa: E402

# A leading YYYY-MM-DD-HHMM or YYYY-MM-DD. Anything else in the directory is not a stamped
# document and cannot be sorted against -- README.md in an orientation folder is not a rival.
STAMPED = re.compile(r"^(\d{4}-\d{2}-\d{2}(?:-\d{4})?)")


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc)


def stamp(now, date_only=False):
    return now.strftime("%Y-%m-%d" if date_only else "%Y-%m-%d-%H%M")


def existing_stamps(dirpath):
    """Every leading stamp already in the directory, as strings. Missing directory is not an
    error -- a thread's first orientation has nothing to sort against, which is the normal case."""
    try:
        names = os.listdir(dirpath)
    except FileNotFoundError:
        return []
    out = []
    for n in sorted(names):
        if n.startswith("."):
            continue
        m = STAMPED.match(n)
        if m:
            out.append((m.group(1), n))
    return out


def main(argv):
    ap = argparse.ArgumentParser(add_help=True, description=__doc__.splitlines()[0])
    ap.add_argument("--date", action="store_true",
                    help="YYYY-MM-DD only, for a document dated to the day")
    ap.add_argument("--for", dest="target", metavar="DIR",
                    help="check the stamp sorts last in this directory (vault-relative or absolute)")
    ap.add_argument("--after", action="store_true",
                    help="if the clock does not sort last, step one minute past the newest name "
                         "instead of refusing -- and say so on stderr")
    ap.add_argument("--vault", help="override the resolved vault")
    args = ap.parse_args(argv)

    if args.after and not args.target:
        ap.error("--after needs --for: there is nothing to step past without a directory")
    if args.after and args.date:
        ap.error("--after needs minute resolution; it cannot step a --date stamp")

    now = utc_now()
    s = stamp(now, args.date)

    if not args.target:
        print(s)
        return 0

    target = args.target
    if not os.path.isabs(target):
        vault = vault_config.resolve_or_exit(args.vault, "stamp")
        target = os.path.join(str(vault.path), target)

    found = existing_stamps(target)
    # Compare on the leading stamp, string-wise, because that is how pickup picks the newest.
    # A same-minute collision counts as NOT sorting last: two handoffs in one minute need the
    # author to look, not a silent overwrite or an arbitrary tiebreak.
    blocking = [(st, n) for st, n in found if st >= s]

    if blocking and args.after:
        newest = max(st for st, _ in blocking)
        try:
            stepped = (datetime.datetime.strptime(newest, "%Y-%m-%d-%H%M")
                       + datetime.timedelta(minutes=1)).strftime("%Y-%m-%d-%H%M")
        except ValueError:
            # A day-only name (YYYY-MM-DD) in an orientation folder: any HHMM sorts after it.
            stepped = newest + "-0001"
        drift = stepped[:16]
        print(stepped)
        print(f"\nthe clock does not sort last here, so this stepped past {newest}", file=sys.stderr)
        print(f"  UTC now is {s}; the newest name is {newest}", file=sys.stderr)
        print(f"  emitted {drift} -- a SEQUENCE KEY, ahead of real time. The document's true time is"
              f"\n  its `date:` frontmatter and its commit, not this name.", file=sys.stderr)
        print("  Drift compounds. If it has grown large, the fix is a reset agreed with the owner,"
              "\n  not another step.", file=sys.stderr)
        return 0

    if blocking:
        print(s)
        print(f"\nthis stamp does NOT sort last in {args.target}", file=sys.stderr)
        for st, n in blocking:
            rel = "same minute" if st == s else "sorts after"
            print(f"  {n}   ({rel})", file=sys.stderr)
        print("\n  A new orientation must sort last by name or `pickup` will not read it.",
              file=sys.stderr)
        print("  Measured 2026-08-21: these names are sequence keys, not timestamps, and they run"
              "\n  ahead of the clock. Re-run with --after to step past the newest one.",
              file=sys.stderr)
        print("  Do not hand-pick a stamp -- the step is the tool's job, and it reports the drift.",
              file=sys.stderr)
        return 1

    print(s)
    if found:
        print(f"sorts after {found[-1][1]}  ({len(found)} stamped here)", file=sys.stderr)
    else:
        print(f"nothing stamped in {args.target} yet -- this would be the first", file=sys.stderr)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except SystemExit:
        raise
    except BrokenPipeError:
        sys.exit(0)
