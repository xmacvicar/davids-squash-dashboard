# Squash Dashboard — Workflow Guide

## Adding a Match

### From the website (any device)

Click **+ Add match** in the nav bar and fill in the form. It commits the match to
`matches.csv`, and a GitHub Action rebuilds `index.html` — the live site updates in about a minute.

The button is hidden from visitors. To unlock it on a new device, visit the site with
`?admin` on the end of the URL, click **+ Add match**, and paste a GitHub token:

1. Go to GitHub → Settings → Developer settings → [Fine-grained tokens](https://github.com/settings/personal-access-tokens/new)
2. Repository access: **Only select repositories** → `davids-squash-dashboard`
3. Permissions: **Contents → Read and write**
4. Pick an expiry, generate, and paste it into the form

The token is saved only in that browser. If it expires, click **Forget token** and paste a new one.

### From Terminal

```
squash
```

Follow the prompts. It pulls the latest changes first (so matches added from the
website aren't lost), then appends the match, rebuilds, commits, and pushes.

To undo the last match (from either method), `git pull` then:

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

This rebuilds `index.html` with the updated rankings and deploys it. (Simply committing
and pushing `ratings.json` also works — the GitHub Action rebuilds the site.)

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
| `.github/workflows/build.yml` | Rebuilds `index.html` on GitHub whenever data or the template changes |

---

## Rules

- **Never edit `index.html` directly** — your changes will be overwritten on the next build
- **Never edit `template.html`** unless you're making a structural change to the dashboard itself
- **If you manually edit `matches.csv`** (e.g. to fix a past entry, even on github.com), just commit and push it — the GitHub Action rebuilds the site
- **Run `git pull` before working locally** — the website and the Action both make commits