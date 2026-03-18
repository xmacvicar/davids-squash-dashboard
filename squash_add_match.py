#!/usr/bin/env python3
"""
squash_add_match.py
-------------------
CLI tool to add a new match to matches.csv, rebuild index.html,
then commit and push to GitHub Pages.

Usage:
    python3 squash_add_match.py           <- add a match
    python3 squash_add_match.py --undo    <- undo the last commit

Requirements:
    - Run from the root of your squash project repo
    - matches.csv, template.html, ratings.json must exist
    - Git must be configured with push access
"""

import csv
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

MATCHES    = "matches.csv"
TEMPLATE   = "template.html"
RATINGS    = "ratings.json"
OUTPUT     = "index.html"

FIELDNAMES = ["Date", "Opponent", "Event", "Win/Loss", "Score", "Game Scores", "Type"]


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def prompt(label, default=None, choices=None):
    while True:
        hint = ""
        if default is not None:
            hint += f" [{default}]"
        if choices:
            hint += f" ({'/'.join(choices)})"
        raw = input(f"  {label}{hint}: ").strip()

        if not raw and default is not None:
            return default
        if choices and raw not in choices:
            print(f"    x  Please enter one of: {', '.join(choices)}")
            continue
        if not raw:
            print(f"    x  This field is required.")
            continue
        return raw


def validate_date(s):
    try:
        date.fromisoformat(s)
        return True
    except ValueError:
        return False


def validate_score(s):
    return bool(re.match(r'^\d-\d$', s))


def check_files():
    missing = [f for f in [MATCHES, TEMPLATE, RATINGS] if not Path(f).exists()]
    if missing:
        print(f"\nx  Missing files: {', '.join(missing)}")
        print("   Make sure you're running this from your project root.\n")
        sys.exit(1)


# ─────────────────────────────────────────────
# CSV
# ─────────────────────────────────────────────

def append_to_csv(row):
    with open(MATCHES, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writerow(row)


# ─────────────────────────────────────────────
# Build
# ─────────────────────────────────────────────

def build():
    with open(TEMPLATE, "r", encoding="utf-8") as f:
        template = f.read()

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
    matches_js = "const MD=[\n" + "\n".join(rows) + "\n];"

    with open(RATINGS, "r", encoding="utf-8") as f:
        data = json.load(f)
    ratings_js = f"const RANK_DATA={json.dumps(data, separators=(',', ':'))};"

    output = template.replace("const MD=/*MATCHES_DATA*/[];", matches_js)
    output = output.replace("const RANK_DATA=/*RATINGS_DATA*/{};", ratings_js)

    if "/*MATCHES_DATA*/" in output or "/*RATINGS_DATA*/" in output:
        print("\nx  Build failed -- placeholder not found in template.html.\n")
        sys.exit(1)

    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(output)

    count = len(re.findall(r'\{date:"', output))
    print(f"  v {OUTPUT} rebuilt ({count} matches)")


# ─────────────────────────────────────────────
# Git
# ─────────────────────────────────────────────

def git_commit_and_push(message):
    steps = [
        (["git", "add", MATCHES, OUTPUT], "Staging files"),
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


# ─────────────────────────────────────────────
# Add match
# ─────────────────────────────────────────────

def main():
    check_files()
    today = date.today().isoformat()

    print("\n+-------------------------------------+")
    print("|   Add Squash Match Result           |")
    print("+-------------------------------------+\n")

    while True:
        raw_date = prompt("Date (YYYY-MM-DD)", default=today)
        if validate_date(raw_date):
            break
        print("    x  Invalid date format. Use YYYY-MM-DD (e.g. 2026-03-18)")

    opponent   = prompt("Opponent name (e.g. John Smith)")
    event      = prompt("Event (e.g. Montreal League Div 2)")
    match_type = prompt("Type", choices=["league", "tournament"])
    wl         = prompt("Result", choices=["Win", "Loss"])

    while True:
        score = prompt("Score (e.g. 3-1 or 1-3)")
        if validate_score(score):
            break
        print("    x  Use format like 3-1 or 2-3")

    print("\n  Game scores are optional but power deeper stats (e.g. 11-7, 9-11, 11-5)")
    game_scores = prompt("Game scores", default="")

    row = {
        "Date":        raw_date,
        "Opponent":    opponent,
        "Event":       event,
        "Win/Loss":    wl,
        "Score":       score,
        "Game Scores": game_scores,
        "Type":        match_type,
    }

    print("\n+-------------------------------------+")
    print("|   Preview                           |")
    print("+-------------------------------------+\n")
    for k, v in row.items():
        if v:
            print(f"  {k:<12} {v}")

    print()
    confirm = prompt("Add this match and push to GitHub?", choices=["y", "n"])
    if confirm != "y":
        print("\n  Cancelled. Nothing was changed.\n")
        sys.exit(0)

    print("\n+-------------------------------------+")
    print("|   Updating & Deploying              |")
    print("+-------------------------------------+\n")

    append_to_csv(row)
    print(f"  v {MATCHES} updated")

    build()

    commit_msg = f"Add match vs {opponent} ({raw_date})"
    git_commit_and_push(commit_msg)

    print(f"\n  v Live on GitHub Pages shortly")
    print(f"  {wl} vs {opponent} | {score} | {event}\n")


# ─────────────────────────────────────────────
# Undo
# ─────────────────────────────────────────────

def undo():
    print("\n+-------------------------------------+")
    print("|   Undo Last Match                   |")
    print("+-------------------------------------+\n")

    result = subprocess.run(
        ["git", "log", "-1", "--pretty=format:%s  (%cr)"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print("x  Could not read git log. Are you in the right folder?\n")
        sys.exit(1)

    print(f"  Last commit:  {result.stdout.strip()}\n")

    confirm = prompt("Undo this and push to GitHub?", choices=["y", "n"])
    if confirm != "y":
        print("\n  Cancelled. Nothing was changed.\n")
        sys.exit(0)

    print("\n+-------------------------------------+")
    print("|   Reverting & Deploying             |")
    print("+-------------------------------------+\n")

    steps = [
        (["git", "revert", "HEAD", "--no-edit"], "Reverting last commit"),
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

    print("\n  v Undone and live on GitHub Pages shortly\n")


# ─────────────────────────────────────────────
# Entry
# ─────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--undo":
        undo()
    else:
        main()
