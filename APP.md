# APP — brutal

Technical reference for the portfolio build system. See [README.md](README.md) for quickstart.

## Architecture

`build.py` is the only build step. It reads all content, calls render functions, then calls `render_page()` per page. There is no markdown library — each render function parses its own format.

```
content/
  meta.md             ← site-wide url/site-name/favicon + per-page title/description/heading/tagline (see OG images)
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
    SchibstedGrotesk.ttf          ← variable font (Regular…Black), used by Pillow for OG images
    MaterialSymbolsSharp.woff2    ← icon font, downloaded + subsetted by build.py
  monthly/
    og-01.png … og-12.png        ← pre-generated seasonal OG images (home only)
  og/
    work.png                      ← work page OG image, generated fresh every build
    play.png                      ← play page OG image, generated fresh every build
    work/<slug>.png                ← one per project, generated fresh every build
  playground/
    *.webp                        ← playground card previews
  projects/
    *.webp / *.gif                ← case study images
  og-image.png                    ← copied from monthly/ at build time (home only)
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
| `render_feed(articles_md, project_mds, lately_archive_md, playground_md, site_url, site_title, site_desc)` | articles + projects + lately-archive + playground | RSS 2.0 XML |
| `render_meta(title, description, url, image_url, favicon)` | per-page values resolved in `build()` | `<title>` + OG/Twitter `<meta>` tags |
| `render_page(template, css, js, meta_html, ...)` | all above | complete HTML file |
| `generate_og_image(accent_hex, heading_raw, tagline_raw, domain_text, site_name, output_path)` | per-page heading/tagline | 2400x1260 OG PNG — see OG images |

`render_page()` rewrites asset paths based on `depth`: 0 = home, 1 = work/play (`../`), 2 = project detail (`../../`). Unlike other render functions, `render_meta()` is called once per page (not once globally) — `build()` resolves each page's own title/description/image before calling it.

### Key helpers

`parse_kv_list`, `parse_meta(md)` (splits meta.md into site-wide dict + per-page dict), `parse_heading_tagline(md)` (hero.md's `# heading` + tagline format), `parse_labels`, `slugify`, `_BOLD_RE`, `_apply_span()`, `apply_highlight`, `apply_name`, `parse_inline`, `escape`, `render_inline` (bold + italic + links → HTML), `_domain_text(url)` (strips the protocol for the OG image domain label), `_abs_url(src, site_url)`, `_project_fields(md)` (slug/org/problem/year — replaces the old `_project_slug`), `_project_order`.

### Template placeholders

| Placeholder | Source |
|---|---|
| `{{meta}}` | per-page `render_meta()` output — see OG images |
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

## OG images

Every page gets its own Open Graph image and its own `<title>`/description — not one shared site-wide image/title, which is how the site's early versions worked. Spec size is 1200x630; images are saved at 2400x1260 (same aspect ratio) so they stay crisp on retina/high-DPI unfurl previews.

### Content: `content/meta.md`

```markdown
- url: https://thedataareclean.com
- site-name: thedataareclean
- favicon: assets/favicon.png

## home
- title: arpit | curious about everything | thedataareclean
- description: hello, i am arpit — i am curious about everything.

## work
- title: selected work | thedataareclean
- description: i help people understand their data — through products, research and stories.
- heading: selected works
- tagline: i help people understand their data — through products, research and stories.

## play
- title: whatever i want | thedataareclean
- description: reading, design, coffee, and everything in between.
- heading: my playground
- tagline: reading, creating, coffee, and everything in between.
```

Top-level keys (before the first `## page` header) are site-wide. Each `## pagename` section holds per-page `title`/`description` (→ `<title>`, `og:description`, `twitter:description`) and, for work/play, `heading`/`tagline` (→ the text actually drawn on the image). `parse_meta()` splits the file into `(site, pages)`.

- **home** — image heading/tagline come from `hero.md` instead, not duplicated in `meta.md`, so the hero copy has one source of truth.
- **work / play** — `heading`/`tagline` live in `meta.md` directly.
- **project pages** — no entry in `meta.md` at all. Image heading = the project's `problem` field (the question), tagline = `org · year`; `title`/`description` meta tags use `org`/`problem`. All already in `content/work/projects/<slug>.md` — nothing extra to maintain.

### Editing the image text

| What | Where |
|---|---|
| Home heading/tagline | `content/hero.md` |
| Work/play heading/tagline | `content/meta.md`, `## work` / `## play` sections |
| Project heading/tagline | `content/work/projects/<slug>.md` — `problem` and `org`/`year` fields |
| Domain label (`thedataareclean.com`) | Derived from `meta.md`'s `url` — not separately editable |

Work/play/project images regenerate automatically on every `python3 build.py`. Home's are precomputed per season — run `python3 build.py --gen-monthly` after editing `hero.md` or the accent palette.

### Generation: `generate_og_image()`

Called once per page inside `build()` for work/play/each project (fresh every run), and 12x by `--gen-monthly` for home (one per seasonal accent, checked into `assets/monthly/`, copied to `assets/og-image.png` at build time for the current month).

Drawing order: white 2400x1260 canvas → 1px-per-logical-px black border → accent-colour cube top-left (flush against the border, like a browser tab) → domain label top-right (site-name portion in accent colour, `.com` in black — same convention as `**bold**` words) → heading + tagline bottom-left, word-wrapped to fit rather than shrunk, so a short heading and a full project question render at the same type size everywhere.

Non-obvious implementation details, each fixing a real visual bug hit along the way:

- **Shapes and text are drawn on separate layers.** The border/cube are flat shapes drawn straight at final (2x) resolution — pixel-perfect, no resampling. Text is drawn on a separate transparent layer, supersampled 3x further, then downsampled onto the base with LANCZOS for smooth anti-aliased glyph edges. Supersampling everything together (shapes included) was tried first and blurred the 1px border into a multi-pixel grey smear on downsample.
- **Headline bold uses the font's real Bold instance, not a stroke hack.** `assets/fonts/SchibstedGrotesk.ttf` is a variable font (named instances Regular…Black) — `font_lg.set_variation_by_name('Bold')`. An earlier version faked bold with Pillow's `stroke_width`, which reads as a soft grey halo / chunky outline at large sizes. That's an artifact of the stroke technique itself, not a resolution problem — supersampling did not fix it.
- **2x output resolution.** 1200x630 is the OG spec floor; any retina/high-DPI viewer (browsers, Mac Preview, chat/social unfurl previews) upscales an exact-spec-size image, which reads as blur regardless of source pixel quality.
- **Fixed font metrics, not each string's tight glyph bbox**, drive vertical layout (`font.getmetrics()` → ascent + descent). A tight bbox varies with which letters are present — e.g. "VizChitra" has no descenders, "hello, i am arpit!" does — which shifted the heading/tagline baseline differently per page when layout math used it instead.
- Typographic hyphens (`‐` U+2010, `‑` U+2011) are normalized to ASCII `-` before drawing — the font has no glyph for them and they rendered as tofu boxes.

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
2. Copies the current month's home OG image from `assets/monthly/`
3. Generates `favicon.png` (requires Pillow)
4. Generates work/play/each-project's OG image fresh into `assets/og/` (requires Pillow) — see [OG images](#og-images)
5. Renders all pages from markdown content, each with its own `<title>`/meta tags
6. Inlines minified CSS + JS into each HTML file
7. Writes output to `dist/`, copies assets
8. Generates `dist/feed.xml`
9. `smoke_check()` — verifies every expected `dist/` file (each page, `feed.xml`, favicon, every OG image) exists and is non-empty; exits 1 if anything's missing. Doesn't check output is *correct*, just that nothing was silently skipped or swallowed by an exception — see `check_content()` for content-level validation (missing images, duplicate slugs) instead.

Flags: `--gen-monthly` regenerates all 12 seasonal home OG images (into `assets/monthly/`); `--optimize-images` converts PNG/JPG in `assets/` to WebP in-place (skips `assets/og/`, `assets/monthly/`, fonts).

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
