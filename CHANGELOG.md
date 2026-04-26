# CHANGELOG

Reverse-chronological. Versioning: **major** = redesign · **minor** = new feature/section/page · **patch** = content or bug fix. Content-only commits (lately updates, project edits) do not get version bumps.

---

## UNRELEASED

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
