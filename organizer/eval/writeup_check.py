"""Find which catalog defects a team's WRITEUP.md names (organizer only, no API calls).

Teams never see the defect IDs, so matching is by keywords (signals.yaml `writeup`): a defect is a
candidate credit when every keyword group matches inside one paragraph / table row / list item.
Candidates are evidence for a judge, who confirms each one (named AND evidenced) before scoring.

Scoring rule from the answer key: 1 point per 3 confirmed catalog IDs, cap 10.

  python organizer/eval/writeup_check.py --repo ../team-07
  python organizer/eval/writeup_check.py --file ../team-07/WRITEUP.md --json out.json
"""
import argparse
import json
import re
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
EVIDENCE = re.compile(r"\d[\d,.]*\s*(%|x|tokens?|calls?|s\b|ms\b|usd|\$)|\$\s*\d|before|after", re.I)


def chunks(text):
    """Paragraphs, table rows and list items, each with its nearest heading for context."""
    heading, out = "", []
    for block in re.split(r"\n\s*\n", text):
        lines = block.strip().splitlines()
        if not lines:
            continue
        if lines[0].startswith("#"):
            heading = lines[0].lstrip("# ").strip()
            lines = lines[1:]
        if lines and all(re.match(r"\s*(\||[-*+]\s|\d+\.\s)", ln) for ln in lines):
            out += [(heading, ln) for ln in lines]
        elif lines:
            out.append((heading, " ".join(lines)))
    return out


def matches(groups, text):
    low = text.lower()
    return all(any(re.search(k if any(c in k for c in "\\.?[") else re.escape(k), low) for k in group)
               for group in groups)


def check(text):
    signals = yaml.safe_load((HERE / "signals.yaml").read_text(encoding="utf-8"))
    parts = chunks(text)
    found = {}
    for defect_id, sig in signals.items():
        groups = sig.get("writeup") or []
        for heading, chunk in parts:
            if groups and matches(groups, heading + " " + chunk):
                found[defect_id] = {"snippet": chunk[:240], "has_numbers": bool(EVIDENCE.search(chunk))}
                break
    return found


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo")
    ap.add_argument("--file")
    ap.add_argument("--json")
    args = ap.parse_args()
    path = Path(args.file) if args.file else Path(args.repo) / "WRITEUP.md"
    if not path.exists():
        candidates = sorted(Path(args.repo or ".").glob("*.md"))
        print(f"No write-up at {path}. Markdown files in the repo: {[c.name for c in candidates]}")
        result = {"file": str(path), "found": {}, "candidates": 0, "provisional_points": 0}
    else:
        found = check(path.read_text(encoding="utf-8", errors="replace"))
        result = {"file": str(path), "found": found, "candidates": len(found),
                  "provisional_points": min(10, len(found) // 3)}
        print(f"Write-up: {path}\n  candidate defects: {len(found)}/33 -> provisional {result['provisional_points']}/10 "
              "(judge must confirm each)\n")
        for defect_id, info in found.items():
            print(f"  {defect_id:<4} {'[numbers]' if info['has_numbers'] else '[no numbers]':<13} {info['snippet'][:150]}")
    if args.json:
        Path(args.json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json).write_text(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
