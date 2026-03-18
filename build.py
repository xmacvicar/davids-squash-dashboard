#!/usr/bin/env python3
"""
build.py
--------
Rebuilds index.html from:
  - template.html   (the static shell with placeholders)
  - matches.csv     (your match history)
  - ratings.json    (your ClubLocker rankings data)

Usage:
    python3 build.py           ← just build index.html
    python3 build.py --push    ← build, commit, and push to GitHub
"""

import csv
import json
import subprocess
import sys
from datetime import date

TEMPLATE  = "template.html"
MATCHES   = "matches.csv"
RATINGS   = "ratings.json"
OUTPUT    = "index.html"


# ─────────────────────────────────────────────
# Build
# ─────────────────────────────────────────────

def load_template():
    try:
        with open(TEMPLATE, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"\n✗  Could not find '{TEMPLATE}'.\n")
        sys.exit(1)


def build_matches_js():
    try:
        rows = []
        with open(MATCHES, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                entry = (
                    f'  {{date:"{row["Date"]}",opp:"{row["Opponent"]}",'
                    f'event:"{row["Event"]}",wl:"{row["Win/Loss"]}",'
                    f'result:"{row["Score"]}",type:"{row["Type"]}"'
                )
                if row.get("Game Scores", "").strip():
                    entry += f',games:"{row["Game Scores"]}"'
                entry += "},"
                rows.append(entry)
        return "const MD=[\n" + "\n".join(rows) + "\n];"
    except FileNotFoundError:
        print(f"\n✗  Could not find '{MATCHES}'.\n")
        sys.exit(1)


def build_ratings_js():
    try:
        with open(RATINGS, "r", encoding="utf-8") as f:
            data = json.load(f)
        compact = json.dumps(data, separators=(",", ":"))
        return f"const RANK_DATA={compact};"
    except FileNotFoundError:
        print(f"\n✗  Could not find '{RATINGS}'.\n")
        sys.exit(1)


def build():
    template = load_template()
    matches_js = build_matches_js()
    ratings_js = build_ratings_js()

    output = template.replace("const MD=/*MATCHES_DATA*/[];", matches_js)
    output = output.replace("const RANK_DATA=/*RATINGS_DATA*/{};", ratings_js)

    if "/*MATCHES_DATA*/" in output or "/*RATINGS_DATA*/" in output:
        print("\n✗  Placeholder replacement failed. Was template.html modified?\n")
        sys.exit(1)

    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(output)

    import re
    count = len(re.findall(r'\{date:"', output))
    print(f"  ✓ {OUTPUT} rebuilt ({count} matches)")


# ─────────────────────────────────────────────
# Git
# ─────────────────────────────────────────────

def git_commit_and_push(message):
    steps = [
        (["git", "add", OUTPUT], "Staging"),
        (["git", "commit", "-m", message], "Committing"),
        (["git", "push"], "Pushing to GitHub"),
    ]
    for cmd, label in steps:
        print(f"  → {label}...", end=" ", flush=True)
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print("FAILED")
            print(f"\n✗  Git error:\n{result.stderr.strip()}\n")
            sys.exit(1)
        print("done")


# ─────────────────────────────────────────────
# Entry
# ─────────────────────────────────────────────

if __name__ == "__main__":
    push = len(sys.argv) > 1 and sys.argv[1] == "--push"

    print("\n┌─────────────────────────────────────┐")
    print("│   🔨  Building index.html           │")
    print("└─────────────────────────────────────┘\n")

    build()

    if push:
        today = date.today().isoformat()
        git_commit_and_push(f"Update ratings ({today})")
        print("\n  ✓ Live on GitHub Pages shortly\n")
    else:
        print("\n  Run with --push to deploy to GitHub.\n")
