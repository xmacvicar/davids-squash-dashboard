#!/usr/bin/env python3
"""
update_ratings.py
-----------------
Downloads ranking/rating history from the US Squash (ClubLocker) API and
writes ratings.json in the shape the dashboard expects:

    {"Squash Quebec|All Men": [{"d": "2026-03-04", "r": 37, "rt": 4.96}, ...], ...}

The endpoint is public, so no login or token is needed.

Usage:
    python3 update_ratings.py          <- update ratings.json
    python3 update_ratings.py --push   <- update, rebuild index.html, commit and push

Runs weekly on GitHub via .github/workflows/update-ratings.yml.
"""

import json
import subprocess
import sys
import urllib.request

PLAYER_ID = 99447
URL = f"https://api.ussquash.com/resources/res/user/{PLAYER_ID}/rankings?history=yes"
RATINGS = "ratings.json"

# The series the dashboard charts ("RatingGroupDescr|DivisionName")
SERIES = [
    "Squash Quebec|All Men",
    "Squash Quebec|M40+",
    "Squash Canada|All Men",
    "Squash Canada|M40+",
    "Universal Squash Rating|All Men",
    "Universal Squash Rating|M40+",
]


def fetch():
    req = urllib.request.Request(URL, headers={
        "Accept": "application/json",
        "User-Agent": "davids-squash-dashboard (ratings sync)",
    })
    with urllib.request.urlopen(req, timeout=60) as res:
        return json.load(res)


def transform(rows):
    out = {key: {} for key in SERIES}
    for row in rows:
        key = f'{row["RatingGroupDescr"]}|{row["DivisionName"]}'
        if key in out and row.get("Ranking") is not None and row.get("Rating") is not None:
            d = row["RankingPeriod"][:10]
            out[key][d] = {"d": d, "r": row["Ranking"], "rt": row["Rating"]}
    return {key: [pts[d] for d in sorted(pts)] for key, pts in out.items()}


def main():
    try:
        rows = fetch()
    except Exception as e:
        sys.exit(f"x  Could not fetch rankings: {e}")
    if not isinstance(rows, list) or not rows:
        sys.exit("x  Rankings API returned no data -- leaving ratings.json unchanged.")

    new = transform(rows)

    try:
        with open(RATINGS, encoding="utf-8") as f:
            old = json.load(f)
    except FileNotFoundError:
        old = {}

    # Refuse to replace history with something smaller (API hiccup, format change)
    for key in SERIES:
        if len(new[key]) < len(old.get(key, [])):
            sys.exit(f"x  {key}: API returned {len(new[key])} points, file has {len(old[key])} -- not overwriting.")

    if new == old:
        print("  v ratings.json already up to date")
        return False

    with open(RATINGS, "w", encoding="utf-8") as f:
        json.dump(new, f, indent=2)
        f.write("\n")

    for key in SERIES:
        added = len(new[key]) - len(old.get(key, []))
        latest = new[key][-1] if new[key] else None
        if latest:
            print(f"  v {key:<34} #{latest['r']:<5} {latest['rt']:.2f}  ({latest['d']}, +{added} new)")
    return True


if __name__ == "__main__":
    changed = main()
    if changed and len(sys.argv) > 1 and sys.argv[1] == "--push":
        from build import build, git_commit_and_push
        from datetime import date
        build()
        git_commit_and_push(f"Update ratings ({date.today().isoformat()})")
