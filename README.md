# brutal

Personal portfolio site for [Arpit](https://thedataareclean.com) — a brutalist, multi-page design built with a markdown-driven build system.

## Structure

```
content/              <- editable markdown content
  meta.md             <- page title, description, OG tags
  hero.md             <- home page heading + tagline
  about.md            <- about section (work page)
  projects.md         <- project cards (work page)
  work.md             <- toolkit tags (work page)
  articles.md         <- published writings with tags (work page)
  lately.md           <- activity tags with links (play page)
  interests.md        <- curiosity tags (play page)
  rolodex.md          <- things i like — random 5 shown per visit (play page)
  footer.md           <- footer content (all pages)
template.html         <- shared HTML shell with {{placeholders}}
style.css             <- all styling with design tokens
script.js             <- theme, seasons, live data (Open-Meteo)
build.py              <- assembles dist/ (Python 3)
assets/               <- fonts, og-image, favicon
  fonts/SchibstedGrotesk.ttf
CNAME                 <- custom domain
```

### Output

```
dist/
  index.html          <- home (hero + tagline)
  work/index.html     <- work (about + toolkit + projects + articles)
  play/index.html     <- play (lately + interests + gallery + rolodex)
  assets/             <- copied from assets/
  CNAME               <- copied from root
```

## Pages

- **/** — full-viewport hero with name + tagline
- **/work** — about, toolkit (flex-wrap tags), project cards (bordered boxes with stretched links), published writings (article cards with publisher, date, tags)
- **/play** — lately (linked activity tags), interests (curiosity tags), Glass.photo masonry gallery (9 at a time with show more, EXIF info overlay per photo), rolodex (5 random links per visit with shuffle button)

## Design system

### Type scale (minor-third ~1.2x)

| Token | Mobile | Desktop | Use |
|---|---|---|---|
| `--text-display` | 32px | 128px | hero h1 |
| `--text-heading` | 24px | 36px | page intros, section titles, about h2 |
| `--text-subhead` | 18px | 24px | hero tagline |
| `--text-body` | 15px | 17px | about text, toolkit/interest tags, project/article names, subtitles |
| `--text-small` | 13px | 13px | project role/desc, article meta, lately, footer, rolodex, gallery info title |
| `--text-ui` | 11px | 11px | nav links, toast, season picker, article tags, gallery info overlay |

### Weight

| Weight | Use |
|---|---|
| 400 | default — body, tags, descriptions, labels |
| 500 | headings — section titles, about h2 |
| 700 | emphasis — project/article name, lately value, nav, toast, rolodex name, gallery info title/camera |

### Line-height

| Value | Use |
|---|---|
| 1 | `--text-display` (hero h1) |
| 1.05 | section titles |
| 1.4 | `--text-small` and `--text-ui` (project role/desc, article meta, lately, footer, rolodex, gallery info) |
| 1.5 | `--text-body` and above (about h2, about text, taglines, subtitles, toolkit/interest tags, project/article names) |

### Letter-spacing

| Value | Use |
|---|---|
| 1px | `--text-ui` (nav, toast, season picker, article tags, gallery info overlay, show-more) |
| 0.5px | `--text-small` labels (lately, footer, project role, article publisher/date) |

### Spacing

| Token | Mobile | Desktop | Use |
|---|---|---|---|
| `--space-xl` | 64px | 120px | page intro, hero bottom |
| `--space-lg` | 48px | 80px | between sections, footer |
| `--space-md` | 24px | 40px | title-to-content, inner gaps |
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

- `**bold**` in headings becomes accent-coloured highlights
- `[text](url)` becomes links (open in new tab)
- `- key: value` lists become structured sections

### Lately tags

In `lately.md`, add a `[title](url)` value to show a linked tag. Leave empty to hide:

```
- read: [Book Title](https://example.com)
- listened: [Episode Name](https://example.com)
- watched:
```

Available keys: `read`, `listened`, `watched`, `cooked`, `explored`, `played`, `built`, `learned`, `ran`, `cycled`, `photographed`, `drank`, `visited`, `wrote`.

### Rolodex

In `rolodex.md`, add `[name](url)` entries. 5 random items are shown per visit. Click the shuffle button for a new set:

```
- [The Pudding](https://pudding.cool)
- [Our World in Data](https://ourworldindata.org)
```

### Projects

In `projects.md`, each project is a `## Name` heading with `- role:`, `- url:`, `- desc:` fields. The whole card is clickable. `[text](url)` in descriptions creates inline links:

```
## Project Name
- role: your role
- url: https://example.com
- desc: description with [inline link](https://example.com).
```

### Articles

In `articles.md`, each article is a `## Title` heading with `- publisher:`, `- date:`, `- tags:` (comma-separated, up to 3), and `- url:` fields. Articles are displayed in the order they appear in the file (reverse chronological):

```
## Article Title
- publisher: Publisher Name
- date: Mon YYYY
- tags: topic, category, theme
- url: https://example.com/article
```

## Live data

The footer shows live data for Bengaluru via [Open-Meteo](https://open-meteo.com/) (free, no API key):

- **Local time** — `Asia/Kolkata` timezone, updates every 60s
- **Temperature** — Open-Meteo forecast API, cached 1h in localStorage
- **AQI** — Open-Meteo air quality API (US AQI), cached 1h in localStorage

## Deploy

Three GitHub Actions workflows:

| Workflow | Trigger | What it does |
|---|---|---|
| `pages.yml` | push to main | Deploys `dist/` to GitHub Pages |
| `monthly-build.yml` | 1st of every month | Rebuilds with Pillow for seasonal accent, commits dist + assets |
| `lately-reminder.yml` | every Sunday 9am IST | Creates a GitHub issue to update `content/lately.md` |

## Live

https://thedataareclean.com
