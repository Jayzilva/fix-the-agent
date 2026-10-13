"""Static defect scan of a team repo against the planted-defect catalog (organizer only, no API calls).

Bug signatures are the defects.yaml anchors, or the `broken` / `missing` rules in signals.yaml
where an anchor only locates code. For each catalog defect it reports:
  PRESENT       every bug signature still matches -> defect untouched
  PARTIAL       some bug signatures still match
  FIXED         no anchor matches and a fix signal was found
  LIKELY_FIXED  no anchor matches, no specific fix signal (code removed or rewritten)
  UNKNOWN       anchors gone but the defect needs a positive signal that was not found

It is evidence for the judges, not a verdict: anchors are exact regexes against the starter code,
so a rename can hide a defect that is still there. Always skim the flagged code.

  python organizer/eval/static_scan.py --repo ../team-07
  python organizer/eval/static_scan.py --repo ../team-07 --json organizer/runs/team-07/static_scan.json
  python organizer/eval/static_scan.py --calibrate     # starter (main) must be all PRESENT,
                                                       # reference (solution) must have none PRESENT
"""
import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ORGANIZER = HERE.parent
ROOT = ORGANIZER.parent
SKIP_DIRS = {"data", "organizer", "tests", ".git", ".venv", "venv", "out", "__pycache__", "node_modules"}
CODE_SUFFIXES = {".py", ".md", ".yaml", ".yml", ".toml"}


def load_catalog():
    defects = yaml.safe_load((ORGANIZER / "defects.yaml").read_text(encoding="utf-8"))["defects"]
    signals = yaml.safe_load((HERE / "signals.yaml").read_text(encoding="utf-8"))
    return defects, signals


def code_files(repo):
    for path in repo.rglob("*"):
        if path.is_file() and path.suffix in CODE_SUFFIXES and not (set(path.relative_to(repo).parts) & SKIP_DIRS):
            if path.name in ("WRITEUP.md", "README.md", "CHALLENGE.md"):
                continue
            yield path


def anchor_hits(repo, anchors):
    hits = []
    for file, pattern in anchors:
        path = repo / file
        if not path.exists():
            continue
        rx = re.compile(pattern)
        for n, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if rx.search(line):
                hits.append(f"{file}:{n}")
                break
    return hits


def missing_hits(texts, rules):
    """`when` found somewhere but `absent` found nowhere -> a broken hit at the `when` location."""
    hits = []
    for rule in rules:
        when = signal_hits(texts, [rule["when"]])
        if when and not signal_hits(texts, [rule["absent"]]):
            hits.append(f"{when[0]} (no /{rule['absent']}/ anywhere)")
    return hits


def signal_hits(texts, patterns):
    hits = []
    for pattern in patterns:
        rx = re.compile(pattern, re.I)
        for rel, text in texts.items():
            for n, line in enumerate(text.splitlines(), 1):
                if rx.search(line):
                    hits.append(f"{rel}:{n}")
                    break
            if len(hits) >= 3:
                return hits
    return hits


def scan(repo):
    repo = Path(repo).resolve()
    defects, signals = load_catalog()
    texts = {str(p.relative_to(repo)).replace("\\", "/"): p.read_text(encoding="utf-8", errors="replace")
             for p in code_files(repo)}
    rows = []
    for d in defects:
        sig = signals.get(d["id"], {})
        checks = sig["broken"] if "broken" in sig else d["anchors"]
        present = anchor_hits(repo, checks) + missing_hits(texts, sig.get("missing", []))
        total = len(checks) + len(sig.get("missing", []))
        fixed = signal_hits(texts, sig.get("fixed", []))
        if present and len(present) == total:
            status = "PRESENT"
        elif present:
            status = "PARTIAL"
        elif fixed:
            status = "FIXED"
        elif sig.get("gone_ok"):
            status = "LIKELY_FIXED"
        else:
            status = "UNKNOWN"
        rows.append({"id": d["id"], "title": d["title"], "status": status,
                     "anchors_still_matching": present, "fix_signals": fixed})
    counts = {s: sum(r["status"] == s for r in rows) for s in
              ("PRESENT", "PARTIAL", "FIXED", "LIKELY_FIXED", "UNKNOWN")}
    return {"repo": str(repo), "counts": counts, "defects": rows}


def render(result):
    out = [f"Static scan: {result['repo']}", "  " + ", ".join(f"{k} {v}" for k, v in result["counts"].items()), ""]
    for r in result["defects"]:
        detail = ", ".join(r["anchors_still_matching"] or r["fix_signals"])[:90]
        out.append(f"  {r['id']:<4} {r['status']:<13} {r['title'][:58]:<58} {detail}")
    return "\n".join(out)


def export_branch(branch):
    """Export a branch of this repo to a temp dir (git archive), for calibration."""
    tmp = Path(tempfile.mkdtemp(prefix=f"scan-{branch}-"))
    archive = subprocess.run(["git", "-C", str(ROOT), "archive", branch], capture_output=True, check=True).stdout
    subprocess.run(["tar", "-x", "-C", str(tmp)], input=archive, check=True)
    return tmp


def calibrate(starter, reference):
    ok = True
    for name, branch, check in (
        ("starter", starter, lambda c: c["PRESENT"] == sum(c.values())),
        ("reference", reference, lambda c: c["PRESENT"] == 0 and c["PARTIAL"] == 0 and c["UNKNOWN"] == 0),
    ):
        result = scan(export_branch(branch))
        print(render(result) + "\n")
        if not check(result["counts"]):
            ok = False
            print(f"CALIBRATION FAILED for {name} ({branch}): {result['counts']}\n")
    print("Calibration OK" if ok else "Calibration FAILED - fix signals.yaml or defects.yaml")
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", help="team repo to scan")
    ap.add_argument("--json", help="write the result as JSON")
    ap.add_argument("--calibrate", action="store_true", help="scan the starter and reference branches")
    ap.add_argument("--starter", default="main")
    ap.add_argument("--reference", default="solution")
    args = ap.parse_args()
    if args.calibrate:
        sys.exit(0 if calibrate(args.starter, args.reference) else 1)
    if not args.repo:
        ap.error("--repo is required (or --calibrate)")
    result = scan(args.repo)
    print(render(result))
    if args.json:
        Path(args.json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json).write_text(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
