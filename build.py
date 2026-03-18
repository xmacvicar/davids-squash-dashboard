#!/usr/bin/env python3
"""
build.py
--------
Rebuilds index.html from:
  - template.html   (static shell with placeholders)
  - matches.csv     (match history — source of truth)
  - ratings.json    (ClubLocker rankings data)

Usage:
    python3 build.py           <- just build index.html
    python3 build.py --push    <- build, commit, and push to GitHub
"""

import csv
import json
import re
import subprocess
import sys
from datetime import date

TEMPLATE = "template.html"
MATCHES  = "matches.csv"
RATINGS  = "ratings.json"
OUTPUT   = "index.html"


def load_template():
    try:
        with open(TEMPLATE, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"\nx  Could not find '{TEMPLATE}'.\n")
        sys.exit(1)


def build_matches_and_scores_js():
    """Build the MD array and SCORES dict from matches.csv."""
    try:
        md_rows = []
        scores_dict = {}
        date_counters = {}

        with open(MATCHES, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                d = row["Date"]
                entry = (
                    f'  {{date:"{d}",opp:"{row["Opponent"]}",'
                    f'event:"{row["Event"]}",wl:"{row["Win/Loss"]}",'
                    f'result:"{row["Score"]}",type:"{row["Type"]}"'
                )
                if row.get("Game Scores", "").strip():
                    entry += f',games:"{row["Game Scores"]}"'
                entry += "},"
                md_rows.append(entry)

                # Rebuild SCORES dict with a/b/c suffixes for same-day matches
                if row.get("Game Scores", "").strip():
                    count = date_counters.get(d, 0)
                    key = d if count == 0 else f"{d}{chr(97 + count)}"
                    if count == 1 and d in scores_dict:
                        scores_dict[d + "a"] = scores_dict.pop(d)
                    scores_dict[key] = row["Game Scores"]
                    date_counters[d] = count + 1
                else:
                    date_counters[d] = date_counters.get(d, 0) + 1

        matches_js = "const MD=[\n" + "\n".join(md_rows) + "\n];"
        scores_js = "const SCORES=" + json.dumps(scores_dict, indent=2) + ";"
        return matches_js, scores_js

    except FileNotFoundError:
        print(f"\nx  Could not find '{MATCHES}'.\n")
        sys.exit(1)


def build_ratings_js():
    try:
        with open(RATINGS, "r", encoding="utf-8") as f:
            data = json.load(f)
        return f"const RANK_DATA={json.dumps(data, separators=(',', ':'))};"
    except FileNotFoundError:
        print(f"\nx  Could not find '{RATINGS}'.\n")
        sys.exit(1)


def build():
    template = load_template()
    matches_js, scores_js = build_matches_and_scores_js()
    ratings_js = build_ratings_js()

    output = template.replace("const MD=/*MATCHES_DATA*/[];", matches_js)
    output = output.replace("const RANK_DATA=/*RATINGS_DATA*/{};", ratings_js)
    output = output.replace("const SCORES=/*SCORES_DATA*/{};", scores_js)

    for placeholder in ["/*MATCHES_DATA*/", "/*RATINGS_DATA*/", "/*SCORES_DATA*/"]:
        if placeholder in output:
            print(f"\nx  Build failed -- {placeholder} not replaced. Was template.html modified?\n")
            sys.exit(1)

    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(output)

    match_count = len(re.findall(r'\{date:"', output))
    scores_count = len(scores_js.split('": "')) - 1
    print(f"  v {OUTPUT} rebuilt ({match_count} matches, {scores_count} game score entries)")


def git_commit_and_push(message):
    steps = [
        (["git", "add", OUTPUT], "Staging"),
        (["git", "commit", "-m", message], "Committing"),
        (["git", "push"], "Pushing to GitHub"),
    ]
    for cmd, label in steps:
        print(f"  -> {label}...", end=" ", flush=True)
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print("FAILED")
            print(f"\nx  Git error:\n{result.stderr.strip()}\n")
            sys.exit(1)
        print("done")


if __name__ == "__main__":
    push = len(sys.argv) > 1 and sys.argv[1] == "--push"

    print("\n+-------------------------------------+")
    print("|   Building index.html              |")
    print("+-------------------------------------+\n")

    build()

    if push:
        today = date.today().isoformat()
        git_commit_and_push(f"Update ratings ({today})")
        print("\n  v Live on GitHub Pages shortly\n")
    else:
        print("\n  Run with --push to deploy to GitHub.\n")
