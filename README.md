# brutal

Personal portfolio site for [Arpit](https://thedataareclean.com) — a brutalist, multi-page design built with a markdown-driven build system.

## Structure

```
content/              ← editable markdown content
  meta.md             ← page title, description, OG tags
  hero.md             ← home page heading + tagline
  about.md            ← about section (work page)
  projects.md         ← project list (work page)
  work.md             ← skills + services (work page)
  lately.md           ← reading/listening/watching/etc (play page)
  interests.md        ← interest tags (play page)
  footer.md           ← footer content (all pages)
template.html         ← shared HTML shell with {{placeholders}}
style.css             ← all styling with design tokens
script.js             ← theme, seasons, live data
build.py              ← assembles dist/ (Python 3)
assets/               ← fonts, og-image, favicon
  fonts/SchibstedGrotesk.ttf
CNAME                 ← custom domain
```

### Output

```
dist/
  index.html          ← home (hero + tagline)
  work/index.html     ← work (about + skills + services + projects)
  play/index.html     ← play (lately + interests + photo gallery)
  assets/             ← copied from assets/
  CNAME               ← copied from root
```

## Pages

- **/** — full-viewport hero with name + tagline
- **/work** — about, skills grid, services grid, project list with outward links
- **/play** — lately (linked activity tags), interests (curiosity tags), Glass.photo masonry gallery

## Design system

### Type scale (minor-third ~1.2x)

| Token | Mobile (375px) | Desktop (1440px) | Use |
|---|---|---|---|
| `--text-display` | 32px | 128px | hero h1 |
| `--text-heading` | 24px | 36px | page intros, section titles, project names |
| `--text-subhead` | 18px | 24px | hero tagline |
| `--text-body` | 15px | 17px | descriptions, about text, boxes |
| `--text-small` | 13px | 13px | captions, footer, project roles |
| `--text-ui` | 11px | 11px | nav links, labels, toast |

### Spacing

| Token | Mobile | Desktop | Use |
|---|---|---|---|
| `--space-xl` | 64px | 120px | page intro, hero bottom |
| `--space-lg` | 48px | 80px | between sections, footer |
| `--space-md` | 24px | 40px | title→content, inner gaps |
| `--space-sm` | 12px | 12px | box gap |

### Colour

- `--black` / `--white` — swap in dark mode
- `--accent` — seasonal, set by JS per month (12 Bengaluru bloom colours)
- Theme and accent persist within a session via `sessionStorage`, reset on new visit

## Build

```
python3 build.py
```

Reads markdown content, fetches photos from Glass.photo, renders HTML, inlines CSS/JS, generates OG image + favicon (requires `pip install Pillow`), and writes to `dist/`.

## Edit content

Edit any file in `content/`, then run `python3 build.py`:

- `**bold**` in headings → accent-coloured highlights
- `[text](url)` → links (open in new tab)
- `- key: value` lists → structured sections

### Lately tags

In `lately.md`, add a `[title](url)` value to show a tag. Leave empty to hide:

```
- read: [Book Title](https://example.com)
- listened: [Episode Name](https://example.com)
- watched:
```

Available keys: `read`, `listened`, `watched`, `cooked`, `explored`, `played`, `built`, `learned`, `ran`, `cycled`, `photographed`, `drank`, `visited`, `wrote`.

## Deploy

GitHub Actions builds and deploys to GitHub Pages on push to `main`. Rebuilds monthly on the 1st for seasonal accent updates.

## Live

https://thedataareclean.com
