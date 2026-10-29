# CHANGELOG

Reverse-chronological. Versioning: **major** = redesign · **minor** = new feature/section/page · **patch** = content or bug fix. Content-only commits (lately updates, project edits) do not get version bumps.

---

## UNRELEASED

- Projects with no slug/org or a duplicate slug are skipped with a warning instead of overwriting another page (including `work/index.html`)
- Lately values keep text around a link; RSS lately guids include the date and text, so repeated or unlinked entries no longer collapse into one
- `script.js` survives blocked `sessionStorage`/`localStorage`; season buttons have `type="button"`
- Remaining hardcoded copy (nav, aria-labels, AQI bands, season/month names, lately verbs, `IST`, `AQI`, `Shuffle`) moved to `labels.md`, passed to `script.js` as JSON
- List items, article fields, URLs and label attributes are HTML-escaped; rolodex JSON can't close its `<script>`
- Build no longer redownloads the icon font or regenerates unchanged OG images (`.build-cache.json`); `feed.xml` is reproducible across rebuilds; `build()` no longer crashes on an incomplete `meta.md`
- `--optimize-images` applies EXIF rotation, won't overwrite an existing `.webp`, checks skip folders relative to `assets/`, and updates content references
- Dark mode: theme is set from a tiny `<head>` script (no light flash) with a `prefers-color-scheme` CSS fallback for no-JS; season swatches follow the theme
- Stale `dist/work/<slug>/` pages, OG images and cache entries are removed when a project is renamed or deleted (the old `dist/work/vizchitra/` page is gone)
- Headings and `**bold**` spans are escaped (a literal `<br>` is still allowed); `*` inside link URLs and spaced asterisks (`5 * 3 * 2`) no longer produce `<em>`
- Season colour table lives only in `build.py` (`SEASONS`) and reaches `script.js` as JSON; email and social URLs moved to `meta.md`, their labels, the `·` separator and RSS title prefixes to `labels.md`
- Articles "show more" handler moved from an inline Python string into `script.js`
- New tokens `--space-xs` (4px) and `--icon-sz-xl` (24px) replace raw pixel values
- Email-copy button works without the Clipboard API (legacy fallback), reports failure, announces via a live-region toast and no longer stacks timers
- Weather: a null temperature or AQI shows `--` instead of being cached as `0°C` / `null — Good`
- Season picker: `aria-expanded`, Escape to close, footnote clicks don't close it, 24px tap target
- Project markdown: multi-line `<!-- -->` comments are skipped; slugs must be a single path segment
- `--optimize-images` can convert animated GIFs, but keeps a GIF when the animated WebP would be larger (the three project GIFs: ~2x bigger as WebP, so they stay); transparency in LA/P images is flattened onto white like RGBA instead of going black
- One `parse_articles()` / `parse_playground()` shared by the page, feed and asset check; unused favicon accent parameter removed and favicon generation cached
- Decorative icon glyphs are `aria-hidden`; the active nav link has `aria-current="page"`
- Clock keeps one interval at most and doesn't tick in a hidden tab; the `—` pair separator and `°C` unit come from `labels.md`
- Link URLs with a scheme other than http/https/mailto (e.g. `javascript:`) render as `#`; every meta URL/attribute is escaped
- Projects without an `org` are skipped with a warning (they'd have a page but no card); `lastBuildDate` never falls back to year 1
- WCAG AA everywhere: the light accents for Mar, Apr, Jun, Oct and Nov were darkened to ≥4.5:1 against white (`#9870b0`→`#8f64a9`, `#b89010`→`#90700c`, `#a89018`→`#887413`, `#c85080`→`#c5477a`, `#b87878`→`#ab5f5f`); all dark-mode accents already passed. The season picker footnote opacity went 0.5 → 0.65. Monthly OG images regenerated
- OG heading supports `<br>` line breaks; work page heading split over two lines

---

## v4.2.2 — 2026-09-28

- Markdown links whose URL contains balanced parentheses (e.g. Wikipedia's `Foo_(bar)`) no longer get truncated at the first `)` — all link parsing now shares one `_LINK_RE` pattern

---

## v4.2.1 — 2026-09-28

- `requirements.txt` comment corrected — Pillow is required for every build (favicon + OG images), not just `--gen-monthly`
- Pre-commit hook runs `archive_lately.py` with the project `.venv` Python when present
- `archive_lately.py` no longer duplicates items when the hook runs more than once on the same day
- RSS `lastBuildDate` uses `datetime.now(timezone.utc)` instead of the deprecated `datetime.utcnow()`
- September seasonal accent applied to OG images; lately updated

---

## v4.2.0 — 2026-08-01

Per-page OG images, reshaped meta.md, build smoke check.

- Per-page OG images and meta tags — work, play, and every project case study now get their own Open Graph image and `<title>`/description, instead of sharing the homepage's
- `content/meta.md` reshaped: site-wide `url`/`site-name`/`favicon` plus a `## pagename` section per page (`title`, `description`, and for work/play, `heading`/`tagline`)
- OG images saved at 2400x1260 (2x the 1200x630 spec) for retina crispness; headline uses the font's real Bold weight instance (Schibsted Grotesk's variable font, swapped in for the previously-bundled static Regular)
- Domain label added to every OG image, colour-matched to the seasonal accent
- `smoke_check()` verifies every expected `dist/` file exists and is non-empty at the end of every build, failing loudly instead of shipping partial output

---

## v4.1.1 — 2026-05-10

- `check_content` now detects duplicate project slugs at build time

---

## v4.1.0 — 2026-04-26

Five case study pages, RSS feed, project ordering, lately archive automation, docs overhaul.

- Five case study pages: `data-for-india-product`, `data-for-india-viz`, `vizchitra-editorial`, `vizchitra-bengaluru`, `vyapaar-mne` (split from two placeholder files)
- `render_project_page` rebuilt: generic section parser with bold, italic, inline links, images, sub-headings, numbered lists
- RSS 2.0 feed (`dist/feed.xml`) aggregating articles, projects, lately archive, and playground
- Lately archive (`content/play/lately-archive.md`) with `## YYYY-MM-DD` date sections
- Pre-commit hook (`scripts/archive_lately.py`) auto-logs lately changes to archive on commit
- Project ordering via `content/work/project-order.md` (replaces alphabetical filename sort)
- Image optimisation flag (`--optimize-images`) converts PNG/JPG to WebP in-place
- Documentation overhaul: README, APP.md, COMMANDS.md, CHANGELOG.md, FUTURE.md, CLAUDE.md

---

## v4.0.0 — 2026-04-07

Problem-focused projects, case study pages, design system overhaul.

- Project cards rewritten around problem statements (not org names)
- Case study detail pages (`/work/<slug>/`) with full section renderer
- Design system overhaul: new spacing tokens, hover unification, `--on-accent`
- `render_project_page` introduced
- Playground section with 2-col image card grid
- Favicon redesigned; pre-generated monthly OG images

---

## v3.0.0 — 2026-04-05

Playground section, unified hover system, favicon redesign.

- `/play` page: playground card grid (2-col, external links, screenshot previews)
- Unified hover pattern across all bordered interactive elements
- Favicon redesigned with Pillow
- Season picker footnote injected from `labels.md`

---

## v2.8.0 — 2026-03-17

Gallery page, project pages, design system, labels, and docs.

- Gallery page with Glass.photo integration
- Project pages (initial placeholders)
- `content/labels.md` introduced for all UI copy
- Design system formally documented in README

---

## v2.7.x — 2026-03-17

- v2.7.2: Restructure content, clean up codebase
- v2.7.1: Play page reordering, rolodex rename, Glass pagination
- v2.7.0: Accessibility improvements, theming, icons, CI updates

---

## v2.6.x — 2026-02-19 to 2026-03-01

- v2.6.4: Monthly accent update
- v2.6.3: Build dist
- v2.6.2: Fix season active state, remove dead code, dedup CSS
- v2.6.1: Season picker footnote, fix letter-spacing
- v2.6.0: Gallery EXIF info overlay

---

## v2.5.0 — 2026-02-16

Articles section added to `/work` with show-more (batches of 6).

---

## v2.4.x — 2026-02-16

- v2.4.1: Fix workflow permissions, add manual triggers
- v2.4.0: Rolodex added to `/play` (randomised link list, shuffle)

---

## v2.3.x — 2026-02-15 to 2026-02-16

- v2.3.2: Switch weather and AQI to Open-Meteo (no API key required)
- v2.3.1: Standardise typography, polish section headers
- v2.3.0: Redesign work page — toolkit, bordered project cards

---

## v2.2.x — 2026-02-15

- v2.2.4: Clean OG image
- v2.2.3: Update meta copy and OG layout
- v2.2.2: Fix workflows
- v2.2.1: Clean up repo, simplify deploy
- v2.2.0: Design system formalised (merge from experiment branch)

---

## v2.1.x — 2026-02-14 to 2026-02-15

- v2.1.4: Standardise spacing tokens, full-viewport page intros
- v2.1.3: Update play page content
- v2.1.2: Update hero subtitle
- v2.1.1: Refine play page: session persistence, lately tags
- v2.1.0: Standardise type scale, add interests section

---

## v2.0.0 — 2026-02-14

Multi-page portfolio with `/work` and `/play`. GitHub Actions deploy.

- Split single-page design into three pages: home, work, play
- `build.py` introduced as the sole build step
- GitHub Actions Pages deployment
- Markdown-driven content system

---

## v1.3.x — 2026-02-13

- v1.3.4: Rebuild with updated about text
- v1.3.3: Update about copy
- v1.3.2: Finalise domain (thedataareclean.com)
- v1.3.1: Remove unused Inter font
- v1.3.0: Switch typeface from Inter to Schibsted Grotesk

---

## v1.2.x — 2026-02-13

- v1.2.4: Optimise caching, minification
- v1.2.3: Match OG image accent to hero
- v1.2.2: Auto-generate favicon with monthly accent colour
- v1.2.1: Square favicon
- v1.2.0: Meta tags, favicon, OG image, monthly auto-build CI

---

## v1.1.x — 2026-02-13

- v1.1.6: Update about copy, fix highlight selectors
- v1.1.5: Lowercase text, fix seasons, accent tagline
- v1.1.4: Fix seasonal accents (Bengaluru calendar)
- v1.1.3: Fix nav button hover sticking on mobile
- v1.1.2: Fix hero text wrapping on mobile, nav scroll
- v1.1.1: README with project structure
- v1.1.0: Split into content/style/script + markdown build system

---

## v1.0.0 — 2026-02-12

Initial brutalist personal website.

---

## v0.1.0 — 2026-02-12

Initial commit.
