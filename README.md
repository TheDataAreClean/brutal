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
    playground.md     ← external project cards (name, url, image, desc, year)
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
  monthly/
    og-01.png … og-12.png        ← pre-generated seasonal OG images (one per month)
  playground/
    *.png                         ← screenshot previews for playground cards (manual)
  og-image.png                    ← copied from monthly/ at build time
  favicon.png                     ← generated fresh on every build (static design)
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
  assets/
  CNAME
```

CSS and JS are inlined into every HTML file. Asset paths are rewritten per page depth.

## Pages

- **/** — full-viewport hero with name + tagline
- **/work** — about, toolkit tags, project cards (3-col grid, internal links), published writings (3-col grid, show-more in batches of 6)
- **/play** — lately, playground cards (2-col grid, external links with screenshot previews), rolodex (5 random links per visit with shuffle), curiosity tags
- **/work/\<slug\>/** — project case study: problem as h1, org/year meta, tags + visit button, overview, what i did, highlights, back to work

## Design system

### Type scale

| Token | Mobile | Desktop | Use |
|---|---|---|---|
| `--text-display` | 32px | 128px | hero h1 |
| `--text-heading` | 24px | 36px | page intros, section titles, about h2, case study h1 |
| `--text-subhead` | 18px | 24px | hero tagline |
| `--text-body` | 15px | 17px | about text, tags, project/article names, case study meta |
| `--text-small` | 13px | 13px | article meta, footer, rolodex, lately |
| `--text-ui` | 11px | 11px | nav links, toast, season picker, article/project tags |

### Weight

| Weight | Use |
|---|---|
| 400 | default — body, tags, descriptions |
| 500 | headings — section titles, about h2 |
| 700 | emphasis — project/article name, nav, toast, lately value |

### Line-height

| Value | Use |
|---|---|
| 1 | hero h1 |
| 1.05 | section titles |
| 1.3 | case study problem heading |
| 1.4 | `--text-small` and `--text-ui` |
| 1.5 | `--text-body` and above |

### Letter-spacing

| Token | Value | Use |
|---|---|---|
| `--ls-ui` | 1px | nav, toast, tags, buttons (`--text-ui` contexts) |
| `--ls-label` | 0.5px | meta labels, footer, small text (`--text-small` contexts) |

### Spacing

| Token | Value | Use |
|---|---|---|
| `--space-xl` | clamp(64px, 10vh, 120px) | page intro top, hero bottom |
| `--space-lg` | clamp(48px, 7vh, 80px) | between sections, footer |
| `--space-md` | clamp(24px, 3vw, 40px) | title-to-content, inner gaps |
| `--space-sm` | 12px | box gap (alias `--box-gap`) |
| `--box-gap` | — | alias for `--space-sm` |
| `--box-pad` | `12px 16px` | inner padding for bordered boxes |
| `--tag-pad` | `2px 8px` | padding inside pill tags (cards) |
| `--tag-gap` | `6px` | gap between tags in a group |
| `--bar-h` | 40px | height of all bars and buttons |
| `--bar-pad` | 20px | top/bottom padding inside top-bar and nav |
| `--btn-pad-x` | 16px | horizontal padding in text bar-boxes |
| `--inner-gap` | 8px | tight gap within component items (cards, list rows) |
| `--padding` | clamp(24px, 5vw, 64px) | horizontal page margin |

### Icon sizes

| Token | Value | Use |
|---|---|---|
| `--icon-sz` | 16px | inline/small icons |
| `--icon-sz-lg` | 18px | bar-box and primary icons |
| `--nav-logo-sz` | 14px | season picker dot |

Note: Material Symbols `opsz` in `font-variation-settings` must match the rendered `font-size` value numerically.

### Colour

- `--black` / `--white` — swap in dark mode (`#1a1a1a`/`#ffffff` → `#ffffff`/`#000000`)
- `--accent` — seasonal, set by JS per month (12 Bengaluru bloom colours); separate `--accent-light` and `--accent-dark` variants
- `--on-accent` — `#ffffff` in light mode, `#000000` in dark mode; always use this for text/icons on accent-coloured fills
- Theme and season persist within a session via `sessionStorage`; weather/AQI cached 1h in `localStorage`

**Hover pattern (all bordered interactive box elements):** `background: var(--accent)`, `color: var(--on-accent)`, `border-color: var(--accent)`. Accent-coloured children (arrows, labels, publisher) must also override to `var(--on-accent)`. Always inside `@media (hover: hover)`. Applies to: `.bar-box`, `.project`, `.article`, `.lately-item`, `.rolodex-item`, `.playground-card`, `.nav-link-box`, `.season-option`.

### Responsive breakpoints

| Breakpoint | Behaviour |
|---|---|
| > 1024px | 3-col grids (projects, articles) |
| ≤ 1024px | 2-col grids (projects, articles); playground stays 2-col |
| ≤ 768px | 1-col everything; lately items wrap; about goes single column |

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
2. Copies the current month's pre-generated OG image from `assets/monthly/`
3. Generates the favicon (static design, requires Pillow)
4. Renders all pages from markdown content
5. Inlines minified CSS + JS into each HTML file
6. Writes output to `dist/`, copies assets

To pre-generate all 12 monthly OG images (requires Pillow):

```bash
python3 build.py --gen-monthly
```

## Edit content

Edit any file in `content/`, then run `python3 build.py`. Inline syntax available in all content files:

- `**bold**` → accent-coloured highlight
- `[text](url)` → link (opens in new tab)
- `- key: value` → structured kv data

### Projects

Each project lives in its own file at `content/work/projects/<filename>.md`. Files are sorted alphabetically — prefix with a number to control order. The slug is derived from `- org:` automatically, or set explicitly with `- slug:`.

The card on the work page is an internal link to the case study at `/work/<slug>/`. External visit links appear only on the case study page.

```markdown
<!-- CARD -->
- problem: The problem this project addresses, as a question or statement.
- org: Organisation Name
- year: 2024
- tags: tag1, tag2

<!-- IDENTITY -->
- url: https://example.com/
- slug: custom-slug       ← optional; auto-derived from org if omitted

<!-- CASE STUDY -->

## overview
Case study overview paragraph(s). Each non-empty line becomes a <p>.

## what i did
- Bullet one
- Bullet two

## highlights
- [Link text](https://url.com/) or plain text result
```

Section headings (`## overview`, `## what i did`, `## highlights`) are displayed as written — customise per project. Sections with no content are silently skipped.

**Case study page layout:**
- Problem statement as `<h1>` (full viewport height intro, anchored bottom)
- `org · year` meta line with visit site icon button `[↗]`
- Tags row at bar height, with visit button aligned right
- Content sections below

### Articles

Each article is a `## Title` block in `content/work/articles.md`. First 6 are visible; the rest are behind a show-more button (batches of 6). Displayed in file order (add newest at top):

```markdown
## Article Title
- publisher: Publication Name
- date: Mon YYYY
- tags: tag1, tag2
- url: https://url.com/
```

### Playground

In `content/play/playground.md`, each line is one project card. Format:

```
[Name](https://url) | image.png | one-line description | year
```

- `image.png` — filename only; file must exist in `assets/playground/`
- `year` — optional; displayed in accent colour below the name

Example:
```markdown
# playground

[memories](https://photos.thedataareclean.com) | photos.png | experiments behind the viewfinder. | 2026
[musings](https://musings.thedataareclean.com) | musings.png | a place for my thoughts and ideas. | 2026
```

Cards render as a 2-col grid. Each card links externally with an `arrow_outward` indicator.

### Lately

In `content/play/lately.md`, use `[title](url)` for a linked entry or leave blank to hide:

```markdown
- read: [Book Title](https://example.com)
- listened: [Podcast](https://example.com)
- watched:
```

Available keys: `read`, `listened`, `watched`, `cooked`, `explored`, `played`, `built`, `learned`, `ran`, `cycled`, `photographed`, `brewed`, `visited`, `wrote`.

### Rolodex

In `content/play/ideas.md`, add `[name](url)` bullet entries. 5 random items are shown per visit with a shuffle button.

### Labels

All UI copy lives in `content/labels.md`. Keys are fixed; only values change:

| Key | Default | Used for |
|---|---|---|
| `case-study` | case study | project card link text (cards link internally, no arrow) |
| `visit-site` | visit site | `aria-label` on the icon-only visit button on case study pages |
| `back-to-work` | ← back to work | case study page back link |
| `show-more` | show more | articles expand button |
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
