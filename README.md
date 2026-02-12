# brutal

Personal portfolio site for [Arpit](https://thedataareclean.github.io/brutal/) — a brutalist, single-page design built with a markdown-driven build system.

## Structure

```
content/          ← editable markdown files
  hero.md
  about.md
  projects.md
  lately.md
  footer.md
template.html     ← structural HTML with {{placeholders}}
style.css         ← all styling
script.js         ← dark mode, seasons, live data
build.py          ← assembles dist/index.html (Python 3, no dependencies)
dist/index.html   ← generated output (deployed via GitHub Pages)
```

## Build

```
python3 build.py
```

Reads the markdown content files, renders them into HTML, inlines the CSS and JS, and writes `dist/index.html`.

## Edit content

Edit any file in `content/`, then run `python3 build.py`. The markdown format is minimal:

- `**bold**` in headings becomes accent-colored highlights
- `[text](url)` becomes links
- `- key: value` lists drive structured sections (projects, footer)

## Deploy

The site is served by GitHub Pages from the `main` branch root. Push to `main` and it goes live.

## Live

https://thedataareclean.github.io/brutal/
