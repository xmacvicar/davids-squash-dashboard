# Squash Dashboard — Workflow Guide

## Adding a Match

Run this in Terminal:

```
squash
```

Follow the prompts. When you confirm, it will:
- Append the match to `matches.csv`
- Rebuild `index.html`
- Commit and push to GitHub automatically

To undo the last match:

```
squash --undo
```

---

## Updating Rankings

1. Log into [ClubLocker](https://www.clublocker.com) in your browser
2. Run the `fetch_squash_ratings.py` script to download a fresh `squash_ratings.json`
3. Replace `ratings.json` in your project folder with the new file
4. Run in Terminal:

```
python3 build.py --push
```

This rebuilds `index.html` with the updated rankings and deploys it.

---

## File Overview

| File | Purpose |
|---|---|
| `matches.csv` | Your match history — the source of truth |
| `ratings.json` | Your rankings data — replace periodically from ClubLocker |
| `template.html` | The dashboard shell — never edit directly |
| `index.html` | Generated automatically — never edit directly |
| `build.py` | Rebuilds `index.html` from the source files |
| `squash_add_match.py` | The CLI behind the `squash` command |

---

## Rules

- **Never edit `index.html` directly** — your changes will be overwritten on the next build
- **Never edit `template.html`** unless you're making a structural change to the dashboard itself
- `matches.csv` is safe to open and edit in Excel or Numbers if you need to fix a past entry — just run `python3 build.py --push` afterwards