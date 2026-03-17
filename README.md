# brutal

Personal portfolio site for [Arpit](https://thedataareclean.com) — a brutalist, multi-page design built with a markdown-driven Python build system.

## Structure

```
content/
  meta.md             ← <title>, description, OG tags, favicon path
  hero.md             ← home page heading + tagline
  footer.md           ← location, credits, license (kv-list)
  labels.md           ← all UI copy (keys fixed, values editable)
  work/
    intro.md          ← work page opening tagline
    about.md          ← "What is a …" section
    toolkit.md        ← skills tag cloud
    projects.md       ← section heading for the projects grid
    articles.md       ← published writings
    projects/         ← one .md per project (auto-discovered, sorted alphabetically)
      *.md
  play/
    intro.md          ← play page opening tagline
    lately.md         ← recent activity (kv-list)
    clicks.md         ← gallery section heading
    ideas.md          ← rolodex links
    interests.md      ← curiosity tags
template.html         ← shared HTML shell with {{placeholders}}
style.css             ← all styling with design tokens
script.js             ← theme, seasons, live data (Open-Meteo)
build.py              ← assembles dist/ (Python 3)
requirements.txt      ← Python dependencies (Pillow)
assets/
  fonts/
    SchibstedGrotesk.ttf          ← used by Pillow for OG image generation
    MaterialSymbolsSharp.woff2    ← self-hosted icon font (downloaded by build.py)
  og-image.png
  favicon.png
CNAME                 ← custom domain
CLAUDE.md             ← instructions for Claude Code
```

### Output

```
dist/
  index.html                ← home
  work/index.html           ← work page
  play/index.html           ← play page
  work/<slug>/index.html    ← project case study pages (one per projects/*.md)
  play/photos/index.html    ← full photo gallery with lightbox
  assets/
  CNAME
```

CSS and JS are inlined into every HTML file. Asset paths are rewritten per page depth.

## Pages

- **/** — full-viewport hero with name + tagline
- **/work** — about, toolkit tags, project cards (3-col grid), published writings (3-col grid, show-more in batches of 6)
- **/play** — lately, Glass.photo masonry gallery (9 shown, view-all link), rolodex (5 random links per visit with shuffle), curiosity tags
- **/play/photos/** — full masonry gallery (all photos) with lightbox viewer, EXIF info overlays, and keyboard navigation
- **/work/\<slug\>/** — project case study: overview, what i did, highlights, back to work

## Design system

### Type scale

| Token | Mobile | Desktop | Use |
|---|---|---|---|
| `--text-display` | 32px | 128px | hero h1 |
| `--text-heading` | 24px | 36px | page intros, section titles, about h2 |
| `--text-subhead` | 18px | 24px | hero tagline |
| `--text-body` | 15px | 17px | about text, tags, project/article names |
| `--text-small` | 13px | 13px | project role/desc, article meta, footer, gallery info |
| `--text-ui` | 11px | 11px | nav links, toast, season picker, article tags |

### Weight

| Weight | Use |
|---|---|
| 400 | default — body, tags, descriptions |
| 500 | headings — section titles, about h2 |
| 700 | emphasis — project/article name, nav, toast, lately value, gallery info title |

### Line-height

| Value | Use |
|---|---|
| 1 | hero h1 |
| 1.05 | section titles |
| 1.4 | `--text-small` and `--text-ui` |
| 1.5 | `--text-body` and above |

### Letter-spacing

| Value | Use |
|---|---|
| 1px | `--text-ui` (nav, toast, tags, show-more) |
| 0.5px | `--text-small` labels (project role, article meta, footer) |

### Spacing

| Token | Value | Use |
|---|---|---|
| `--space-xl` | clamp(64px, 10vh, 120px) | page intro top, hero bottom |
| `--space-lg` | clamp(48px, 7vh, 80px) | between sections, footer |
| `--space-md` | clamp(24px, 3vw, 40px) | title-to-content, inner gaps |
| `--space-sm` | 12px | box gap (alias `--box-gap`) |
| `--box-gap` | — | alias for `--space-sm` |
| `--box-pad` | `12px 16px` | inner padding for bordered boxes |
| `--bar-h` | 40px | height of all bars and buttons |
| `--bar-pad` | 20px | top/bottom padding inside top-bar and nav |
| `--btn-pad-x` | 16px | horizontal padding in text bar-boxes |
| `--inner-gap` | 8px | tight gap within component items (cards, list rows) |
| `--padding` | clamp(24px, 5vw, 64px) | horizontal page margin |

### Icon sizes

| Token | Value | Use |
|---|---|---|
| `--icon-sz` | 16px | inline/small icons (svg social icons, inline symbols) |
| `--icon-sz-lg` | 18px | bar-box and primary icons |
| `--nav-logo-season-sz` | 14px | season picker dot |

Note: Material Symbols `opsz` in `font-variation-settings` must match the rendered `font-size` value numerically.

### Colour

- `--black` / `--white` — swap in dark mode (`#1a1a1a`/`#ffffff` → `#ffffff`/`#000000`)
- `--accent` — seasonal, set by JS per month (12 Bengaluru bloom colours); separate `--accent-light` and `--accent-dark` variants
- `--on-accent` — always `#ffffff`; text/icons on accent-coloured fills
- `--gallery-overlay-bg`, `--gallery-btn-*` — fixed semi-transparent values for photo card overlays (do not swap in dark mode)
- `--lightbox-bg` — `rgba(0,0,0,0.95)` — lightbox backdrop (always dark, not swapped)
- `--lightbox-frame-border`, `--lightbox-text`, `--lightbox-btn-*` — semi-transparent white values for lightbox UI
- `--gallery-info-btn-sz`, `--gallery-info-btn-offset` — gallery info button sizing tokens
- Theme and season persist within a session via `sessionStorage`; weather/AQI cached 1h in `localStorage`

## Build

```bash
python3 build.py
```

With image generation (OG image + favicon):

```bash
# First time
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# Build
.venv/bin/python3 build.py
```

Each build:
1. Downloads a subsetted `MaterialSymbolsSharp.woff2` (~25KB) from the Google Fonts API
2. Fetches all photos from Glass.photo with EXIF metadata (cursor-paginated)
3. Renders all pages from markdown content
4. Inlines minified CSS + JS into each HTML file
5. Generates seasonal OG image + favicon using Pillow (skipped if Pillow not installed)
6. Writes output to `dist/`, copies assets

## Edit content

Edit any file in `content/`, then run `python3 build.py`. Inline syntax available in all content files:

- `**bold**` → accent-coloured highlight
- `[text](url)` → link (opens in new tab)
- `- key: value` → structured kv data

### Projects

Each project lives in its own file at `content/work/projects/<filename>.md`. Files are sorted alphabetically — prefix with a number to control order. The card on the work page links to an auto-generated case study page at `/work/<slug>/`.

```markdown
# Project Name
- role: your role
- url: https://example.com/
- desc: One-line card description.

## overview
Case study overview paragraph.

## what i did
- Bullet one
- Bullet two

## highlights
- [Link text](https://url.com/)
```

The section headings (`## overview`, `## what i did`, `## highlights`) are displayed as-is — edit them per project if needed.

### Articles

Each article is a `## Title` block in `content/work/articles.md`. First 6 are visible; the rest are behind a show-more button (batches of 6). Displayed in file order (add newest at top):

```markdown
## Article Title
- publisher: Publication Name
- date: Mon YYYY
- tags: tag1, tag2
- url: https://url.com/
```

### Gallery

Photos are fetched automatically from Glass.photo at build time — no manual config needed. The play page shows the 9 most recent with a "view all photos" link to `/play/photos/`. The full gallery page shows all photos in a responsive masonry grid (3-col desktop, 2-col tablet, 1-col mobile) with:

- **Lightbox** — click any photo to open a full-screen viewer with EXIF info and prev/next navigation (keyboard arrows supported)
- **Info overlay** — tap the info button on any card to see description, date, camera, and EXIF
- **Responsive layout** — JS redistributes photos into the correct column count on load and orientation change, preserving left-to-right reading order

The gallery heading lives in `content/play/clicks.md`.

### Lately

In `content/play/lately.md`, use `[title](url)` for a linked entry or leave blank to hide:

```markdown
- read: [Book Title](https://example.com)
- listened: [Podcast](https://example.com)
- watched:
```

Available keys: `read`, `listened`, `watched`, `cooked`, `explored`, `played`, `built`, `learned`, `ran`, `cycled`, `photographed`, `drank`, `visited`, `wrote`.

### Rolodex

In `content/play/ideas.md`, add `[name](url)` bullet entries. 5 random items are shown per visit with a shuffle button.

### Labels

All UI copy lives in `content/labels.md`. Keys are fixed; only values change:

| Key | Default | Used for |
|---|---|---|
| `case-study` | case study | project card button |
| `visit-site` | visit site | project card button |
| `back-to-work` | ← back to work | case study page back link |
| `show-more` | show more | articles + gallery expand button |
| `view-all` | view all photos | gallery "view all" link on play page |
| `back-to-play` | ← back to play | photos page back link |
| `email-copied` | email copied | clipboard toast message |
| `season-info` | colours from bengaluru's seasonal blooms | season picker footnote |

### Adding a new icon

Add the Material Symbols Sharp icon name to `ICON_NAMES` in `build.py`. The next build downloads an updated subset font automatically.

## Live data

The footer shows live data for Bengaluru via [Open-Meteo](https://open-meteo.com/) (free, no API key):

- **Local time** — `Asia/Kolkata` timezone, updates every 60s, pauses when tab is hidden
- **Temperature** — Open-Meteo forecast API, cached 1h in localStorage
- **AQI** — Open-Meteo air quality API (US AQI), cached 1h in localStorage

## Deploy

Three GitHub Actions workflows:

| Workflow | Trigger | What it does |
|---|---|---|
| `pages.yml` | push to `main` | Runs `build.py`, deploys `dist/` to GitHub Pages |
| `monthly-build.yml` | 1st of every month | Runs `build.py` with Pillow, commits updated `dist/` + seasonal OG image + favicon |
| `lately-reminder.yml` | every Sunday 9am IST | Opens a GitHub issue to update `content/play/lately.md` (skips if one is already open) |

### Release tagging

Tag significant releases for easy rollback:

```bash
git tag -a v1.x.x -m "short description"
git push origin v1.x.x
```

Then mark a GitHub release at `github.com/<user>/<repo>/releases/new` — select the tag, write a short changelog, publish.

**Versioning:** major = redesign, minor = new feature/section/page, patch = content update or bug fix.

## Live

https://thedataareclean.com
