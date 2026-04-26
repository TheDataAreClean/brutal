# Commands

Quick reference for common tasks. Current version: see `git tag`.

---

## Setup (fresh clone)

```bash
# Python environment
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# Enable the pre-commit hook (auto-archives lately.md changes)
git config core.hooksPath .githooks
```

---

## Build

```bash
# Build the site (always required before committing)
python3 build.py

# Preview locally
cd dist && python3 -m http.server 8787
# open http://localhost:8787

# Regenerate all 12 monthly OG images (run after changing hero.md or accent colours)
python3 build.py --gen-monthly

# Convert all PNG/JPG in assets/ to WebP and delete originals
python3 build.py --optimize-images
```

---

## Git — day-to-day

```bash
# Check what's changed
git status
git diff

# Stage and commit (always include dist/)
git add -p                          # stage interactively (recommended)
git add content/ dist/ style.css    # or stage specific files
git commit -m "description"

# Push
git push origin main
```

---

## Releases

```bash
# Patch (content update, bug fix)
git tag -a v4.0.1 -m "short description"
git push origin v4.0.1

# Minor (new feature or section)
git tag -a v4.1.0 -m "short description"
git push origin v4.1.0

# Major (redesign)
git tag -a v5.0.0 -m "short description"
git push origin v5.0.0

# List all tags
git tag | sort -V

# See what changed since last tag
git log $(git describe --tags --abbrev=0)..HEAD --oneline
```

Versioning: **major** = redesign · **minor** = new feature/section/page · **patch** = content or bug fix.

GitHub releases: only for minor and major. Patches don't need one.

---

## Content — common edits

| What | File |
|---|---|
| Hero name / tagline | `content/hero.md` |
| About section | `content/work/about.md` |
| Articles | `content/work/articles.md` |
| Lately | `content/play/lately.md` |
| Playground | `content/play/playground.md` |
| New project | `content/work/projects/<slug>.md` |
| Project display order | `content/work/project-order.md` |
| Lately (current month) | `content/play/lately.md` |
| Lately archive (past months) | `content/play/lately-archive.md` |
| UI labels (buttons, etc.) | `content/labels.md` |

---

## Images

```bash
# After adding any PNG or JPG to assets/ (converts to WebP, deletes original)
python3 build.py --optimize-images

# Exceptions — do NOT run optimize-images on:
# assets/favicon.png
# assets/og-image.png
# assets/monthly/
```

---

## Useful git

```bash
# Undo last commit (keep changes staged)
git reset --soft HEAD~1

# See recent commits
git log --oneline -10

# See what a tag points to
git show v4.0.0 --stat
```
