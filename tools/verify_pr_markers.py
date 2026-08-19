#!/usr/bin/env python3
"""
Batch PR-state verifier — librarian tooling for checking done-markers against reality.

WHAT IT DOES
  Takes a list of PR references, possibly spanning several repos, and resolves all of
  them in ONE GitHub GraphQL request: state, mergedAt, and the squash/merge commit.
  Built for the librarian's "Archive first" step (verify every marker before acting on
  it) and for any agent reconciling a vault frontier against what actually merged.

WHY NOT `gh pr view`
  One round-trip instead of N. Measured on 13 PRs across 3 repos:
    one GraphQL query   0.66s
    13 × gh pr view     5.43s
  So there is no reason to fan this out across parallel subagents — spawn overhead alone
  exceeds the whole query. Just call this once.

USAGE
  python3 verify_pr_markers.py acme/server#12398 acme/client#121
  python3 verify_pr_markers.py --json <refs...>          # machine-readable
  echo "owner/repo#123 owner/repo#124" | python3 verify_pr_markers.py -

  A bare "#123" or "123" needs --repo, which keeps a same-repo list short:
  python3 verify_pr_markers.py --repo acme/server 12091 12096 12193

WHY A BARE NUMBER DOES NOT INHERIT POSITIONALLY
  It used to: a bare "#123" reused the previous ref's repo. That shipped a false "settled"
  fact. Two bare refs trailing one qualified ref inherited the qualified repo, resolved to
  real PRs there that had MERGED years earlier, and those wrong rows went into two agent
  prompts labelled "already resolved, do not re-run" — while the PRs actually meant were
  OPEN in a different repo. Nothing was ambiguous *within* the argument list, so no
  ambiguity check would have caught it: the binding was simply wrong, and plausible.
  It was caught only by a downstream agent whose own notes contradicted the table.

  So the inheritance is gone rather than validated. With --repo the binding is stated; a
  bare number without --repo is refused. A verifier that can emit a confidently wrong row
  is worse than one that refuses, because its output is what everything downstream trusts.

OUTPUT
  repo     ref     state   mergedAt              mergeCommit
  server   #12398  MERGED  2026-08-04T14:44:06Z  54c372b4775
  client   #121    OPEN    -                     -
  tracker  #168    CLOSED  -                     -   <- ISSUE, not a PR (completed)
  server   #99999  MISSING -                     -   <- check the number

  Exit 0 if every ref resolved, 2 if any came back MISSING. A MISSING ref means the doc
  citing it has a wrong number — that is a finding, not a tool failure.

THE ISSUE-VS-PR TRAP (the most common real finding)
  Docs cite a tracking *issue* as though it were a PR, and it then reads as unlanded work.
  So this resolves `issueOrPullRequest`, not `pullRequest`: an issue comes back as an ISSUE
  with its state and stateReason instead of a misleading MISSING. One vault pass hit three
  of these in a single run — every one a closed-or-open issue that a doc had recorded as a
  pending PR. An ISSUE row does not set the exit code (citing an issue is often
  legitimate), so read the note: if the doc calls it a PR, fix the doc.

GOTCHA THIS ENCODES
  GraphQL returns PARTIAL data when one PR does not exist: the good aliases resolve, the
  bad one is null, and `errors[]` names its path. But `gh` still exits 1, so a `set -e`
  shell pipeline would abort and throw away the good results. This parses `.data` and
  ignores the exit code, reporting the nulls as MISSING.
"""

import json
import re
import subprocess
import sys
from collections import OrderedDict

REF = re.compile(r"^(?:(?P<owner>[\w.-]+)/(?P<repo>[\w.-]+))?#?(?P<num>\d+)$")


def parse_refs(argv, default_repo=None):
    """-> OrderedDict[(owner, repo)] = [numbers].

    A bare number binds ONLY to an explicit default_repo (--repo). It never inherits from a
    preceding qualified ref: that inheritance once bound two bare refs to the wrong repo,
    where they resolved to real long-merged PRs and shipped a false "settled" row into two
    agent prompts. The wrong binding was unambiguous within the argument list, so there is
    nothing to validate — only a form to refuse.

    A bad ref does NOT abort the batch. It is collected and returned as a problem, and every
    good ref still resolves. This is the same partial-results stance the GOTCHA section takes on
    GraphQL's partial NOT_FOUND: one wrong row must not throw away 23 right ones. Measured -- a
    pass carrying 24 refs included 7 malformed ones, and a fail-hard parse would have lost the
    whole batch, which is how a verifier stops being run at all.
    """
    out = OrderedDict()
    problems = []
    owner = repo = None
    if default_repo:
        # An invocation error, unlike a bad ref: nothing can be resolved, so this does exit.
        m = re.match(r"^(?P<owner>[\w.-]+)/(?P<repo>[\w.-]+)$", default_repo.strip())
        if not m:
            sys.exit(f"--repo {default_repo!r} is not owner/name")
        owner, repo = m.group("owner"), m.group("repo")
    for raw in argv:
        m = REF.match(raw.strip())
        if not m:
            problems.append((raw, "UNPARSEABLE", "want owner/repo#123, #123, or 123"))
            continue
        if m.group("owner"):
            out.setdefault((m.group("owner"), m.group("repo")), []).append(int(m.group("num")))
            continue
        if not repo:
            problems.append((
                raw, "NO-REPO",
                f"bare ref needs --repo owner/name, or qualify it as owner/name#{m.group('num')}"
                " — a bare number does NOT inherit the previous ref's repo",
            ))
            continue
        out.setdefault((owner, repo), []).append(int(m.group("num")))
    return out, problems


def build_query(refs):
    """One request, repos and PRs as aliases. Alias names must be valid GraphQL names."""
    lines = ["query {"]
    for i, ((owner, repo), nums) in enumerate(refs.items()):
        lines.append(f'  r{i}: repository(owner:"{owner}", name:"{repo}") {{')
        for n in nums:
            # issueOrPullRequest, not pullRequest: a doc citing a tracking issue as a PR
            # would otherwise come back MISSING and read as a wrong number.
            lines.append(
                f"    p{n}: issueOrPullRequest(number:{n}) {{ __typename "
                "... on PullRequest { number state mergedAt mergeCommit { oid } } "
                "... on Issue { number state stateReason } }"
            )
        lines.append("  }")
    lines.append("}")
    return "\n".join(lines)


def run(query):
    # Deliberately NOT check=True: gh exits 1 on a partial NOT_FOUND while still
    # returning every PR that did resolve.
    p = subprocess.run(
        ["gh", "api", "graphql", "-f", f"query={query}"],
        capture_output=True,
        text=True,
    )
    try:
        return json.loads(p.stdout)
    except json.JSONDecodeError:
        sys.exit(f"gh returned no JSON (exit {p.returncode}):\n{p.stderr.strip()}")


def main():
    argv = sys.argv[1:]
    if not argv or {"-h", "--help"} & set(argv):
        print(__doc__.strip())
        return 0
    as_json = "--json" in argv
    argv = [a for a in argv if a != "--json"]
    default_repo = None
    if "--repo" in argv:
        i = argv.index("--repo")
        if i + 1 >= len(argv):
            sys.exit("--repo needs an owner/name argument")
        default_repo = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    if argv == ["-"]:
        argv = sys.stdin.read().split()
    if not argv:
        sys.exit(__doc__.strip().split("USAGE")[1].strip())

    refs, problems = parse_refs(argv, default_repo)
    if not refs:
        for raw, kind, why in problems:
            print(f"{kind:<12} {raw!r}: {why}", file=sys.stderr)
        sys.exit("no resolvable refs")
    payload = run(build_query(refs))
    data = payload.get("data") or {}

    rows, missing = [], False
    for i, ((_owner, repo), nums) in enumerate(refs.items()):
        node = data.get(f"r{i}") or {}
        for n in nums:
            pr = node.get(f"p{n}")
            if pr is None:
                missing = True
                rows.append({"repo": repo, "number": n, "state": "MISSING",
                             "mergedAt": None, "mergeCommit": None})
            elif pr.get("__typename") == "Issue":
                rows.append({
                    "repo": repo,
                    "number": pr["number"],
                    "state": pr["state"],
                    "kind": "issue",
                    "stateReason": pr.get("stateReason"),
                    "mergedAt": None,
                    "mergeCommit": None,
                })
            else:
                rows.append({
                    "repo": repo,
                    "number": pr["number"],
                    "state": pr["state"],
                    "kind": "pr",
                    "mergedAt": pr["mergedAt"],
                    "mergeCommit": (pr.get("mergeCommit") or {}).get("oid"),
                })

    if as_json:
        print(json.dumps({"rows": rows, "problems": [
            {"ref": r, "kind": k, "why": w} for r, k, w in problems]} if problems
            else rows, indent=2))
    else:
        w = max(len(r["repo"]) for r in rows)
        print(f"{'repo':<{w}}  {'ref':<8} {'state':<8} {'mergedAt':<21} mergeCommit")
        for r in rows:
            if r["state"] == "MISSING":
                note = "   <- check the number"
            elif r.get("kind") == "issue":
                reason = (r.get("stateReason") or "").lower()
                note = f"   <- ISSUE, not a PR{f' ({reason})' if reason else ''}"
            else:
                note = ""
            print(
                f"{r['repo']:<{w}}  {'#' + str(r['number']):<8} {r['state']:<8} "
                f"{r['mergedAt'] or '-':<21} {(r['mergeCommit'] or '-')[:11]}{note}"
            )
        # Bad refs are rows too, not an abort. Printed after the resolved ones so the good
        # results are never buried by the noise, and counted so the caller cannot miss them.
        for raw, kind, why in problems:
            print(f"{'-':<{w}}  {raw[:8]:<8} {kind:<8} {'-':<21} -   <- {why}")
        if problems:
            print(f"\n{len(problems)} ref(s) not resolvable, {len(rows)} resolved. "
                  "The batch was NOT aborted.", file=sys.stderr)
        for e in payload.get("errors") or []:
            if e.get("type") != "NOT_FOUND":
                print(f"\nnon-NOT_FOUND error: {e.get('type')}: {e.get('message')}",
                      file=sys.stderr)

    # A malformed ref is as much a finding as a MISSING one -- the doc citing it is wrong either
    # way -- so both set exit 2, and neither loses the rows that did resolve.
    sys.exit(2 if (missing or problems) else 0)


if __name__ == "__main__":
    main()
