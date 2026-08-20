#!/usr/bin/env python3
"""
Scope-manifest validator — check a sub-agent's structured return against the branch it wrote.

WHY
  A sub-agent returns a manifest of what it did. The orchestrator must not act on it unvalidated:
  a manifest can name a link that does not exist, and unvalidated that turns one agent's mistake
  into the orchestrator's commit. Measured 2026-08-18, the orchestrator did validate -- by hand,
  in six tool calls and ~95s, differently for each scope. Same checks, one call, identical across
  scopes. Biggest single collapse available in a pass.

  It does the MECHANICAL half only. Two things in that run needed judgement and still do:
  reading the cited lines to rule a claimed contradiction a false positive, and deciding whether
  an uncorroborated claim matters. This tool marks a claim UNVERIFIED rather than guessing, and
  an UNVERIFIED claim is a question for the orchestrator, not a pass.

MANIFEST FORMAT — JSON (not YAML: no stdlib parser, and a manifest must never be ambiguous)
  {
    "scope": "workstreams/x/",
    "base":  "<ref the agent was given>",
    "renames": [{"from": "old/path.md", "to": "new/path.md"}],
    "deletes": [{"path": "old/path.md", "into": ["survivor.md"]}],
    "inbound_links_out_of_scope": [
       {"file": "other/doc.md", "line": 42, "old_target": "x", "new_target": "y"}],
    "stale_claims_out_of_scope": [{"file": "other/doc.md", "line": 12, "claim": "..."}],
    "stale_claims_in_own_scope": [{"file": "in/scope.md", "line": 3, "claim": "..."}],
    "surfaces_delta": [...], "structural_proposals": [...], "markers": [...],
    "self_check": {...}
  }
  Unknown keys are preserved and reported, never rejected -- a schema that refuses an extra
  field teaches agents to drop findings that have nowhere to go.

WHAT IT ASSERTS
  renames          both halves present in the branch's diff, as a rename or as add+delete
  deletes          the file is gone, AND each named survivor exists and is non-trivially
                   larger than nothing -- content survival is sampled, see LIMITS
  inbound_links    every cited file:line exists, and the line really contains old_target;
                   scanned across the WHOLE branch and (with --memory-dir) the memory dir,
                   because the load-bearing claim is that NONE were missed
  claims           every cited file:line resolves; the claim text itself is never adjudicated
  scope discipline every path the agent wrote is inside its declared scope

LIMITS, STATED BECAUSE A SILENT ONE READS AS A CLEAN RESULT
  Content survival is checked by sampling distinctive lines from the deleted file and looking
  for them in the survivors. It cannot prove a paraphrase preserved meaning. Use
  `recall_check.py <base> <deleted> --into <survivor>` for that; this reports SAMPLED.

USAGE
  python3 tools/scope_manifest_validate.py <manifest.json> --vault PATH --branch REF
                                           [--memory-dir PATH] [--sample N]

    exit 0   every mechanical assertion holds (UNVERIFIED items reported, not hidden)
    exit 1   at least one assertion failed
    exit 5   bad invocation, or the manifest will not parse
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path


class Report:
    def __init__(self):
        self.rows = []      # (status, section, message)
        self.failed = 0
        self.unverified = 0

    def add(self, status, section, message):
        self.rows.append((status, section, message))
        if status == "FAIL":
            self.failed += 1
        elif status == "UNVER":
            self.unverified += 1

    def ok(self, section, msg):
        self.add("ok", section, msg)

    def fail(self, section, msg):
        self.add("FAIL", section, msg)

    def unver(self, section, msg):
        self.add("UNVER", section, msg)


def git(vault, *args):
    r = subprocess.run(["git", *args], cwd=vault, capture_output=True, text=True)
    return r.returncode, r.stdout


def file_at(vault, ref, path):
    code, out = git(vault, "show", f"{ref}:{path}")
    return out if code == 0 else None


def check_renames(rep, vault, base, branch, manifest):
    renames = manifest.get("renames") or []
    if not renames:
        rep.ok("renames", "none claimed")
        return
    code, out = git(vault, "diff", "--name-status", "-M", f"{base}..{branch}")
    if code != 0:
        rep.unver("renames", f"cannot diff {base}..{branch}")
        return
    added, deleted, renamed = set(), set(), set()
    for line in out.splitlines():
        parts = line.split("\t")
        if not parts or not parts[0]:
            continue
        tag = parts[0]
        if tag.startswith("R") and len(parts) >= 3:
            renamed.add((parts[1], parts[2]))
            deleted.add(parts[1])
            added.add(parts[2])
        elif tag == "A" and len(parts) >= 2:
            added.add(parts[1])
        elif tag == "D" and len(parts) >= 2:
            deleted.add(parts[1])
    for r in renames:
        frm, to = r.get("from"), r.get("to")
        if (frm, to) in renamed:
            rep.ok("renames", f"{frm} -> {to} (detected as a rename)")
        elif to in added and frm in deleted:
            rep.ok("renames", f"{frm} -> {to} (add + delete; git did not pair them)")
        else:
            missing = []
            if frm not in deleted:
                missing.append(f"old half {frm} not deleted")
            if to not in added:
                missing.append(f"new half {to} not added")
            rep.fail("renames", f"{frm} -> {to}: " + "; ".join(missing or ["not in the diff"]))


def check_deletes(rep, vault, base, branch, manifest, sample_n):
    deletes = manifest.get("deletes") or []
    if not deletes:
        rep.ok("deletes", "none claimed")
        return
    for d in deletes:
        path = d.get("path")
        intos = d.get("into") or []
        if file_at(vault, branch, path) is not None:
            rep.fail("deletes", f"{path}: still present on {branch}")
            continue
        old = file_at(vault, base, path)
        if old is None:
            rep.unver("deletes", f"{path}: not readable at {base}, cannot check survival")
            continue
        if not intos:
            rep.unver("deletes", f"{path}: deleted, but no survivor named -- content survival unchecked")
            continue
        # Sample distinctive lines: long, prose-ish, not headings or list bullets.
        cand = [l.strip() for l in old.splitlines()
                if len(l.strip()) > 60 and not l.strip().startswith(("#", "|", "```", "-", "*"))]
        step = max(1, len(cand) // sample_n) if cand else 1
        sample = cand[::step][:sample_n]
        if not sample:
            rep.unver("deletes", f"{path}: no sampleable lines (short or all structure)")
            continue
        blobs = []
        for s in intos:
            t = file_at(vault, branch, s)
            if t is None:
                rep.fail("deletes", f"{path}: named survivor {s} does not exist on {branch}")
                blobs = None
                break
            blobs.append(t)
        if blobs is None:
            continue
        joined = "\n".join(blobs)
        missing = [s for s in sample if s not in joined]
        if not missing:
            rep.ok("deletes", f"{path}: SAMPLED {len(sample)}/{len(sample)} lines present in {', '.join(intos)}")
        else:
            rep.fail("deletes",
                     f"{path}: {len(missing)}/{len(sample)} sampled lines absent from {', '.join(intos)} "
                     f"-- first: {missing[0][:70]!r}")


def check_citations(rep, vault, branch, manifest, section, target_key=None):
    items = manifest.get(section) or []
    if not items:
        rep.ok(section, "none claimed")
        return
    for it in items:
        path, line_no = it.get("file"), it.get("line")
        text = file_at(vault, branch, path)
        if text is None:
            rep.fail(section, f"{path}: does not exist on {branch}")
            continue
        lines = text.splitlines()
        if not isinstance(line_no, int) or not (1 <= line_no <= len(lines)):
            rep.fail(section, f"{path}:{line_no}: out of range (file has {len(lines)} lines)")
            continue
        if target_key:
            needle = it.get(target_key)
            if needle and needle not in lines[line_no - 1]:
                rep.fail(section,
                         f"{path}:{line_no}: does not contain {needle!r} -- "
                         f"line reads {lines[line_no - 1].strip()[:70]!r}")
                continue
        # The claim's TRUTH is never adjudicated here; that is a read of prose against a claim
        # and it is the judgement the orchestrator exists to make.
        rep.ok(section, f"{path}:{line_no} resolves")


def check_no_missed_inbound(rep, vault, branch, manifest, memory_dir):
    """The load-bearing claim is that no inbound link was MISSED, which a per-item check
    cannot establish. Verified the way it was verified by hand: grep the whole branch,
    excluding the scope itself, and the memory dir separately."""
    scope = manifest.get("scope")
    if not scope:
        rep.unver("inbound sweep", "manifest names no scope; cannot exclude it from the sweep")
        return
    claimed = {(i.get("file"), i.get("line")) for i in (manifest.get("inbound_links_out_of_scope") or [])}
    renamed_or_deleted = [r.get("from") for r in (manifest.get("renames") or [])]
    renamed_or_deleted += [d.get("path") for d in (manifest.get("deletes") or [])]
    stems = {Path(p).stem for p in renamed_or_deleted if p}
    if not stems:
        rep.ok("inbound sweep", "no renames or deletes, so nothing could break an inbound link")
        return
    found = []
    for stem in stems:
        code, out = git(vault, "grep", "-n", "-F", f"[[{stem}", branch)
        if code not in (0, 1):
            rep.unver("inbound sweep", f"git grep failed for {stem}")
            continue
        for line in out.splitlines():
            # branch:path:line:text
            rest = line.split(":", 1)[1] if ":" in line else line
            path, _, rest2 = rest.partition(":")
            num, _, _ = rest2.partition(":")
            if path.startswith(scope):
                continue
            try:
                num_i = int(num)
            except ValueError:
                continue
            if (path, num_i) not in claimed:
                found.append(f"{path}:{num_i} -> [[{stem}]]")
    if memory_dir and Path(memory_dir).is_dir():
        for stem in stems:
            for f in Path(memory_dir).glob("*.md"):
                for i, l in enumerate(f.read_text(errors="replace").splitlines(), 1):
                    if f"[[{stem}" in l and (str(f), i) not in claimed:
                        found.append(f"{f}:{i} -> [[{stem}]]  (memory dir)")
    elif memory_dir:
        rep.unver("inbound sweep", f"memory dir not found: {memory_dir}")

    if found:
        rep.fail("inbound sweep",
                 f"{len(found)} inbound link(s) the manifest did not report: " + "; ".join(found[:5]))
    else:
        rep.ok("inbound sweep", f"no unreported inbound links to {len(stems)} moved/deleted doc(s)")


def check_scope_discipline(rep, vault, base, branch, manifest):
    scope = manifest.get("scope")
    if not scope:
        rep.unver("scope", "manifest names no scope")
        return
    code, out = git(vault, "diff", "--name-only", f"{base}..{branch}")
    if code != 0:
        rep.unver("scope", f"cannot diff {base}..{branch}")
        return
    outside = [p for p in out.splitlines() if p.strip() and not p.startswith(scope)]
    if outside:
        rep.fail("scope", f"{len(outside)} file(s) written outside {scope}: " + ", ".join(outside[:5]))
    else:
        rep.ok("scope", f"every write inside {scope}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest")
    ap.add_argument("--vault", default=None,
                    help="vault path or a name from ~/.config/lipika/config.json; "
                         "default: $LIPIKA_VAULT, the config, then this checkout")
    ap.add_argument("--branch", required=True, help="the sub-agent's branch")
    ap.add_argument("--base", default=None, help="override the manifest's own base")
    ap.add_argument("--memory-dir", default=None)
    ap.add_argument("--sample", type=int, default=6)
    args = ap.parse_args()
    import vault_config
    args.vault = str(vault_config.resolve_or_exit(args.vault, "scope_manifest_validate"))

    vault = Path(args.vault).expanduser().resolve()
    try:
        manifest = json.loads(Path(args.manifest).read_text())
    except Exception as e:
        print(f"manifest will not parse as JSON: {e}", file=sys.stderr)
        return 5
    base = args.base or manifest.get("base")
    if not base:
        print("no base ref: pass --base or put \"base\" in the manifest", file=sys.stderr)
        return 5

    rep = Report()
    check_scope_discipline(rep, vault, base, args.branch, manifest)
    check_renames(rep, vault, base, args.branch, manifest)
    check_deletes(rep, vault, base, args.branch, manifest, args.sample)
    check_citations(rep, vault, args.branch, manifest,
                    "inbound_links_out_of_scope", target_key="old_target")
    check_no_missed_inbound(rep, vault, args.branch, manifest, args.memory_dir)
    check_citations(rep, vault, args.branch, manifest, "stale_claims_out_of_scope")
    check_citations(rep, vault, args.branch, manifest, "stale_claims_in_own_scope")

    print(f"manifest {args.manifest}\nscope {manifest.get('scope')}  base {base}  branch {args.branch}\n")
    width = max(len(s) for _, s, _ in rep.rows)
    for status, section, msg in rep.rows:
        print(f"  {status:5}  {section:{width}}  {msg}")

    known = {"scope", "base", "renames", "deletes", "inbound_links_out_of_scope",
             "stale_claims_out_of_scope", "stale_claims_in_own_scope", "surfaces_delta",
             "structural_proposals", "markers", "self_check"}
    extra = sorted(set(manifest) - known)
    print()
    if extra:
        print(f"unvalidated manifest keys (preserved, read them yourself): {', '.join(extra)}")
    for key in ("surfaces_delta", "structural_proposals", "markers", "self_check"):
        if manifest.get(key):
            n = len(manifest[key]) if isinstance(manifest[key], list) else 1
            print(f"not mechanically checkable — read it: {key} ({n})")
    if rep.unverified:
        print(f"UNVERIFIED: {rep.unverified} — these are questions, not passes.")
    if rep.failed:
        print(f"FAILED: {rep.failed}")
        return 1
    print("every mechanical assertion holds" + (" (see UNVERIFIED above)" if rep.unverified else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
