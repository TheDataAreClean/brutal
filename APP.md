# APP — brutal

Technical reference for the portfolio build system. See [README.md](README.md) for quickstart.

## Architecture

`build.py` is the only build step. It reads all content, calls render functions, then calls `render_page()` per page. There is no markdown library — each render function parses its own format.

```
content/
  meta.md             ← <title>, description, OG tags, favicon path
  hero.md             ← home page heading + tagline
  footer.md           ← location, credits, license (kv-list)
  labels.md           ← all UI copy (keys fixed, values editable)
  work/
    intro.md          ← work page opening tagline
    about.md          ← "What is a …" two-column section
    toolkit.md        ← skills tag cloud
    projects.md       ← section heading for the projects grid
    project-order.md  ← display order (one slug per line)
    articles.md       ← published writings
    projects/         ← one .md per project case study
      *.md
  play/
    intro.md              ← play page opening tagline
    lately.md             ← current month's activity (kv-list)
    lately-archive.md     ← past months, YYYY-MM-DD sections, RSS-only
    playground.md         ← external project cards
    ideas.md              ← rolodex links
    interests.md          ← curiosity tags
template.html    ← shared HTML shell with {{placeholders}}
style.css        ← all styling, design tokens at top
script.js        ← theme, seasons, live data (Open-Meteo)
build.py         ← assembles dist/
requirements.txt ← Python deps (Pillow)
assets/
  fonts/
    SchibstedGrotesk.ttf          ← used by Pillow for OG image generation
    MaterialSymbolsSharp.woff2    ← icon font, downloaded + subsetted by build.py
  monthly/
    og-01.png … og-12.png        ← pre-generated seasonal OG images
  playground/
    *.webp                        ← playground card previews
  projects/
    *.webp / *.gif                ← case study images
  og-image.png                    ← copied from monthly/ at build time
  favicon.png                     ← generated fresh on every build
dist/            ← generated output, git-tracked, committed with source
```

### Render functions

| Function | Input | Output |
|---|---|---|
| `render_hero(md)` | hero.md | hero header |
| `render_about(md)` | about.md | two-column section |
| `render_toolkit(md)` | toolkit.md | tag cloud |
| `render_projects(heading_md, mds, labels)` | projects.md + projects/*.md | 3-col grid of cards |
| `render_articles(md, labels)` | articles.md | 3-col grid + show-more |
| `render_lately(md)` | lately.md | activity list |
| `render_playground(md)` | playground.md | 2-col linked image card grid |
| `render_rolodex(md)` | ideas.md | randomised link list |
| `render_interests(md)` | interests.md | tag cloud |
| `render_project_page(md, labels)` | projects/*.md | case study page |
| `render_feed(...)` | articles + projects + lately-archive + playground | RSS 2.0 XML |
| `render_page(template, css, js, ...)` | all above | complete HTML file |

`render_page()` rewrites asset paths based on `depth`: 0 = home, 1 = work/play (`../`), 2 = project detail (`../../`).

### Key helpers

`parse_kv_list`, `parse_labels`, `slugify`, `_BOLD_RE`, `_apply_span()`, `apply_highlight`, `apply_name`, `parse_inline`, `escape`, `render_inline` (bold + italic + links → HTML), `_project_slug(md)`, `_project_order`.

### Template placeholders

| Placeholder | Source |
|---|---|
| `{{meta}}` | meta.md |
| `{{body}}` | render function output |
| `{{footer}}` | footer.md |
| `{{nav_root}}` | depth-based prefix |
| `{{nav_work_active}}` / `{{nav_play_active}}` | active page |
| `{{toast_email_copied}}` | labels.md `email-copied` |
| `{{season_info}}` | labels.md `season-info` |

## Pages

| Path | Description |
|---|---|
| `/` | Full-viewport hero |
| `/work` | About, toolkit, project cards (3-col), articles (3-col, show-more) |
| `/play` | Lately, playground (2-col), rolodex (5 random), interests |
| `/work/<slug>/` | Case study: problem as h1, meta, tags, sections, back link |
| `/feed.xml` | RSS 2.0 — articles, projects, lately archive, playground |

## Content formats

### Projects

Files live at `content/work/projects/<filename>.md`. Display order is controlled by `content/work/project-order.md` (one slug per line). Projects not listed fall to the end alphabetically.

```markdown
<!-- CARD -->
- problem: Problem statement as a question.
- org: Organisation Name
- year: 2024
- tags: tag1, tag2

<!-- IDENTITY -->
- url: https://example.com/
- slug: custom-slug       ← optional; auto-derived from org if omitted
- added: Mon YYYY         ← used in RSS feed

<!-- CASE STUDY -->

## overview
## problem
## what i did
## highlights
## impact
## team

### Sub-team
- Person, Role
```

Section headings are displayed as written. Sections with no content are silently skipped. Supported inline: `**bold**`, `*italic*`, `[text](url)`, `![caption](src)`. Two consecutive image lines render side-by-side. Numbered lists (`1. item`) and `### sub-headings` are supported within sections.

### Articles

In `content/work/articles.md`. Add newest at top. Each entry:

```markdown
## Article Title
- publisher: Name
- date: Mon YYYY
- tags: tag1, tag2
- url: https://url.com/
```

### Playground

In `content/play/playground.md`. One card per line:

```
[Name](https://url) | image.webp | one-line description | year
```

### Lately

In `content/play/lately.md`. Use `[title](url)` for a linked entry or leave blank to hide:

```markdown
- read: [Book Title](https://example.com)
- watched:
```

Available keys: `read`, `listened`, `watched`, `cooked`, `explored`, `played`, `built`, `learned`, `ran`, `cycled`, `photographed`, `brewed`, `visited`, `wrote`.

**Archive:** Past months go in `content/play/lately-archive.md` using `## YYYY-MM-DD` section headers. The pre-commit hook (`scripts/archive_lately.py`) logs changed items automatically on every commit.

### Rolodex

In `content/play/ideas.md`, add `[name](url)` bullet entries. 5 random items are shown per visit with a shuffle button.

### Interests

In `content/play/interests.md`, add plain-text tags as a flat list. Rendered as a tag cloud.

### Labels

All UI copy lives in `content/labels.md`. Keys are fixed; edit values only.

| Key | Used for |
|---|---|
| `case-study` | Project card link text |
| `visit-site` | aria-label on case study visit button |
| `back-to-work` | Case study back link |
| `show-more` | Articles expand button |
| `email-copied` | Clipboard toast |
| `season-info` | Season picker footnote |
| `feed-title` | RSS feed title |

## Design system

### Colour

- `--black` / `--white` — swap in dark mode
- `--accent` — seasonal, set by JS per month (12 Bengaluru bloom colours)
- `--accent-light` / `--accent-dark` — light and dark variants
- `--on-accent` — `#ffffff` light / `#000000` dark; always use for text on accent fills

### Type scale

| Token | Mobile | Desktop | Use |
|---|---|---|---|
| `--text-display` | 32px | 128px | hero h1 |
| `--text-heading` | 24px | 36px | page intros, section titles, case study h1 |
| `--text-subhead` | 18px | 24px | hero tagline |
| `--text-body` | 15px | 17px | body text, tags, names |
| `--text-small` | 13px | 13px | article meta, footer, rolodex, lately |
| `--text-ui` | 11px | 11px | nav, toast, season picker, tags |

### Spacing

| Token | Value | Use |
|---|---|---|
| `--space-xl` | clamp(64px, 10vh, 120px) | page intro top, hero bottom |
| `--space-lg` | clamp(48px, 7vh, 80px) | between sections, footer |
| `--space-md` | clamp(24px, 3vw, 40px) | title-to-content, inner gaps |
| `--space-sm` | 12px | box gap (alias `--box-gap`) |
| `--box-pad` | `12px 16px` | inner padding for bordered boxes |
| `--tag-pad` | `2px 8px` | pill tag padding |
| `--tag-gap` | `6px` | gap between tags |
| `--bar-h` | 40px | height of all bars and buttons |
| `--bar-pad` | 20px | top/bottom padding inside top-bar and nav |
| `--btn-pad-x` | 16px | horizontal padding in text bar-boxes |
| `--inner-gap` | 8px | tight gap within component items |
| `--padding` | clamp(24px, 5vw, 64px) | horizontal page margin |

### Icons

| Token | Value | Use |
|---|---|---|
| `--icon-sz` | 16px | inline/small icons |
| `--icon-sz-lg` | 18px | bar-box and primary icons |
| `--nav-logo-sz` | 14px | season picker dot |

Material Symbols `opsz` in `font-variation-settings` must match the rendered `font-size` numerically. New icons must be added to `ICON_NAMES` in `build.py` — the font is subsetted at build time.

### Responsive breakpoints

| Breakpoint | Behaviour |
|---|---|
| > 1024px | 3-col grids (projects, articles) |
| ≤ 1024px | 2-col grids |
| ≤ 768px | 1-col everything |

### Hover pattern

All bordered interactive elements (`.bar-box`, `.project`, `.article`, `.lately-item`, `.rolodex-item`, `.playground-card`, `.nav-link-box`, `.season-option`) use: `background: var(--accent)`, `color: var(--on-accent)`, `border-color: var(--accent)`. Always inside `@media (hover: hover)`.

## Build pipeline

Each `python3 build.py` run:

1. Downloads a subsetted `MaterialSymbolsSharp.woff2` (~25KB) from Google Fonts
2. Copies the current month's OG image from `assets/monthly/`
3. Generates `favicon.png` (requires Pillow)
4. Renders all pages from markdown content
5. Inlines minified CSS + JS into each HTML file
6. Writes output to `dist/`, copies assets
7. Generates `dist/feed.xml`

Flags: `--gen-monthly` regenerates all 12 OG images; `--optimize-images` converts PNG/JPG in `assets/` to WebP in-place.

## Live data

The footer shows live Bengaluru data via [Open-Meteo](https://open-meteo.com/) (free, no API key):

- **Local time** — `Asia/Kolkata` timezone, updates every 60s
- **Temperature** — Open-Meteo forecast API, cached 1h in localStorage
- **AQI** — Open-Meteo air quality API (US AQI), cached 1h in localStorage

## Deploy

Three GitHub Actions workflows:

| Workflow | Trigger | What it does |
|---|---|---|
| `pages.yml` | push to `main` | Runs `build.py`, deploys `dist/` to GitHub Pages |
| `monthly-build.yml` | 1st of every month | Runs build with Pillow, commits updated `dist/` + OG image + favicon |
| `lately-reminder.yml` | every Sunday 9am IST | Opens a GitHub issue to update `lately.md` (skips if one is already open) |

Custom domain via `CNAME`. `dist/` is git-tracked and committed alongside source.
