#!/usr/bin/env python3
"""
Agent transcript reader — find another agent's transcript and profile it, without reading it.

WHY THIS EXISTS
  Profiling an agent means answering four questions: what did it call, in what order, how much did
  each call return into its context, and what did that cost. Every one is mechanical, and every
  time it has been done here by hand it cost thousands of tokens of `jq` incantations plus at
  least one wrong number. The traps are known and each has produced a wrong figure:

    - A RESUME IS NOT A UNIT OF WORK. Resuming re-pays the whole prior transcript as input, so
      summing a resumed agent's token figures overstates it -- measured, one role's three runs
      summed to 213,957 against 65,545 for a single well-specified call. This tool reports the
      PEAK cache_read, never a sum, and says how many separate runs it saw.
    - CACHE-CREATION IS NOT CONTEXT PAID FOR. Summing it against a peak read counts churn inside
      one run as cost. Reported separately, and never added.
    - COLLAPSING NEWLINES IN A COMMAND PREVIEW FABRICATES PIPELINES. A multi-line heredoc rendered
      with `|` reads as a broken pipe; five were misread that way in one profile before the raw
      input was checked. This tool renders newlines as ` <NL> `.
    - A LIVE TRANSCRIPT GROWS WHILE YOU READ IT. If the file was modified in the last two minutes
      the summary says so, because a figure taken from a running agent is a floor.
    - A BACKGROUNDED CHILD'S REPORT IS NOT IN ITS PARENT'S TRANSCRIPT. It arrives out of band, so
      a parent's own file understates delegate cost. `--list` shows the children so they can be
      profiled directly.
    - A WORKTREE SESSION HAS ITS OWN PROJECT SLUG. `~/.claude/projects/<slug>` is derived from the
      cwd, so a session rooted in `<repo>/.claude/worktrees/<name>` is NOT under the repo's slug.
      This resolves the slug from a path rather than assuming one.

USAGE
  python3 tools/agent_transcript.py --list                          # sessions and subagents, newest first
  python3 tools/agent_transcript.py --list --cwd ~/some/worktree    # resolve a different slug
  python3 tools/agent_transcript.py <agent-id-or-path>              # the full profile
  python3 tools/agent_transcript.py <id> --calls                    # one row per tool call
  python3 tools/agent_transcript.py <id> --calls --min-bytes 2000   # only the expensive reads
  python3 tools/agent_transcript.py <id> --tokens                   # cost, with the traps applied
  python3 tools/agent_transcript.py <id> --grep PATTERN             # calls whose input matches

EXIT CODES
  0  printed
  1  nothing matched (no such agent id, or --grep found nothing)
  5  bad invocation, or no transcript directory for that slug
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

PROJECTS = Path.home() / ".claude" / "projects"
LIVE_WINDOW_S = 120


def slug_for(cwd):
    """~/.claude/projects/<slug> is the cwd with separators flattened to dashes."""
    p = os.path.abspath(os.path.expanduser(cwd))
    return "-" + re.sub(r"[/_.]", "-", p.lstrip("/"))


def sessions(slug_dir):
    return sorted((p for p in slug_dir.iterdir() if p.is_dir()),
                  key=lambda p: p.stat().st_mtime, reverse=True)


def find_transcript(target, slug_dir):
    """An id, a bare filename, or a path. Newest match wins."""
    p = Path(target).expanduser()
    if p.is_file():
        return p
    hits = list(slug_dir.glob(f"*/subagents/*{target}*.jsonl"))
    hits += list(slug_dir.glob(f"*{target}*.jsonl"))
    hits = [h for h in hits if not h.name.endswith(".meta.json")]
    if not hits:
        return None
    return sorted(hits, key=lambda h: h.stat().st_mtime, reverse=True)[0]


def records(path):
    out = []
    with open(path, errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return out


def preview(inp, width=150):
    """A one-line rendering that does NOT fabricate a pipeline out of a heredoc."""
    if not isinstance(inp, dict):
        return str(inp)[:width]
    for k in ("command", "file_path", "pattern", "path", "prompt", "query", "description"):
        if k in inp and isinstance(inp[k], str):
            s = inp[k]
            break
    else:
        s = json.dumps(inp, ensure_ascii=False)
    s = s.replace("\n", " <NL> ")
    return s[:width] + ("…" if len(s) > width else "")


def result_text(rec):
    """Bytes this tool_result put into the agent's context."""
    msg = rec.get("message") or {}
    content = msg.get("content")
    chunks = []
    if isinstance(content, list):
        for c in content:
            if not isinstance(c, dict):
                continue
            if c.get("type") == "tool_result":
                r = c.get("content")
                if isinstance(r, str):
                    chunks.append(r)
                elif isinstance(r, list):
                    for rr in r:
                        if isinstance(rr, dict) and isinstance(rr.get("text"), str):
                            chunks.append(rr["text"])
    return "".join(chunks)


def walk(recs):
    """(calls, usages, timestamps). One call row per tool_use, paired with its result bytes."""
    calls, usages, stamps = [], [], []
    pending = {}
    for rec in recs:
        ts = rec.get("timestamp")
        if ts:
            stamps.append(ts)
        msg = rec.get("message") or {}
        if rec.get("type") == "assistant":
            u = msg.get("usage")
            if u:
                usages.append(u)
            for c in msg.get("content") or []:
                if isinstance(c, dict) and c.get("type") == "tool_use":
                    row = {"n": len(calls) + 1, "tool": c.get("name"), "id": c.get("id"),
                           "input": c.get("input") or {}, "ts": ts, "bytes": 0}
                    calls.append(row)
                    pending[c.get("id")] = row
        elif rec.get("type") == "user":
            text = result_text(rec)
            if not text:
                continue
            content = (msg.get("content") or [])
            ids = [c.get("tool_use_id") for c in content
                   if isinstance(c, dict) and c.get("type") == "tool_result"]
            for tid in ids:
                row = pending.get(tid)
                if row is not None:
                    row["bytes"] += len(text.encode())
                    break
            else:
                if calls:
                    calls[-1]["bytes"] += len(text.encode())
    return calls, usages, stamps


def cmd_list(slug_dir):
    print(f"{slug_dir}\n")
    for sess in sessions(slug_dir):
        subs = sorted(sess.glob("subagents/*.jsonl"), key=lambda p: p.stat().st_mtime)
        print(f"session {sess.name}   {len(subs)} subagent transcript(s)")
        for s in subs:
            meta = s.with_suffix("").with_suffix(".meta.json")
            kind = ""
            if meta.is_file():
                try:
                    m = json.loads(meta.read_text())
                    kind = m.get("subagent_type") or m.get("agentType") or ""
                except (json.JSONDecodeError, OSError):
                    pass
            age = time.time() - s.stat().st_mtime
            live = "  LIVE (still being appended)" if age < LIVE_WINDOW_S else ""
            print(f"  {s.stem.replace('agent-', ''):20} {s.stat().st_size:>9,}B  "
                  f"{kind:16}{live}")
    return 0


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("target", nargs="?", help="agent id, filename fragment, or a path")
    ap.add_argument("--list", action="store_true", help="sessions and their subagent transcripts")
    ap.add_argument("--cwd", default=os.getcwd(),
                    help="resolve the project slug from this path (a worktree has its own)")
    ap.add_argument("--calls", action="store_true", help="one row per tool call")
    ap.add_argument("--tokens", action="store_true", help="cost, with the traps applied")
    ap.add_argument("--grep", metavar="PATTERN", help="only calls whose input matches (regex, -i)")
    ap.add_argument("--min-bytes", type=int, default=0, help="with --calls, hide smaller results")
    args = ap.parse_args(argv)

    slug_dir = PROJECTS / slug_for(args.cwd)
    if not slug_dir.is_dir():
        print(f"no transcript directory for {args.cwd}\n  looked in {slug_dir}\n"
              f"  a worktree session has its own slug -- pass --cwd for the right tree",
              file=sys.stderr)
        return 5
    if args.list or not args.target:
        return cmd_list(slug_dir)

    path = find_transcript(args.target, slug_dir)
    if not path:
        print(f"no transcript matching {args.target!r} under {slug_dir}", file=sys.stderr)
        return 1
    recs = records(path)
    calls, usages, stamps = walk(recs)
    age = time.time() - path.stat().st_mtime
    live = age < LIVE_WINDOW_S

    show_all = not (args.calls or args.tokens or args.grep)
    print(f"{path}")
    print(f"  {len(recs)} record(s), {len(calls)} tool call(s), {path.stat().st_size:,}B on disk")
    if stamps:
        print(f"  {stamps[0]} → {stamps[-1]}")
    if live:
        print("  LIVE: modified in the last two minutes, so every figure below is a FLOOR")

    if show_all or args.tokens:
        peak_read = max((u.get("cache_read_input_tokens", 0) for u in usages), default=0)
        peak_create = max((u.get("cache_creation_input_tokens", 0) for u in usages), default=0)
        out_tokens = sum(u.get("output_tokens", 0) for u in usages)
        runs = len({r.get("requestId") for r in recs if r.get("requestId")})
        print("\n## cost")
        print(f"  peak cache_read      {peak_read:>9,}   <- what a turn actually loaded")
        print(f"  peak cache_creation  {peak_create:>9,}   <- churn, NOT context paid for; never add it")
        print(f"  output tokens        {out_tokens:>9,}")
        print(f"  assistant requests   {runs:>9,}")
        print("  Never sum a resumed agent's figures: a resume re-pays the whole prior transcript.")

    if show_all or args.calls or args.grep:
        pat = re.compile(args.grep, re.I) if args.grep else None
        rows = [c for c in calls
                if (not pat or pat.search(json.dumps(c["input"], ensure_ascii=False)))
                and c["bytes"] >= args.min_bytes]
        if not rows:
            print("\nno call matched")
            return 1
        print(f"\n## calls ({len(rows)} shown of {len(calls)})")
        for c in rows:
            print(f"{c['n']:4} {c['tool']:14} {c['bytes']:>8,}B  {preview(c['input'])}")
        by_tool = {}
        for c in calls:
            t = by_tool.setdefault(c["tool"], [0, 0])
            t[0] += 1
            t[1] += c["bytes"]
        print("\n## per tool")
        for tool, (n, b) in sorted(by_tool.items(), key=lambda kv: -kv[1][1]):
            print(f"  {tool:16} {n:4} call(s)  {b:>10,}B returned")
        total = sum(c["bytes"] for c in calls)
        print(f"  {'TOTAL':16} {len(calls):4} call(s)  {total:>10,}B returned into context")
        print("\nBytes returned is the denominator for a relevant-fraction measurement. Classifying "
              "each\nrow as load-bearing / duplicated / never-used is the judgement, and it is yours.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
