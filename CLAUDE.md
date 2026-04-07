# Portfolio — CLAUDE.md

> For project structure, content formats, design token tables, and how to edit content — see **README.md**. This file covers rules, constraints, and things that are easy to get wrong.

## Build

```bash
python3 build.py
```

No dev server. Edits only take effect after a build. `dist/` is git-tracked — commit both source and `dist/` together.

## Content-first principle

**All user-visible text lives in `content/*.md` files.** Never write copy into `build.py`, `template.html`, `script.js`, or `style.css`. This includes:

- Section headings → each section's own `.md` file (the `# ` line)
- Button and UI labels → `content/labels.md` (keys are fixed; edit values only)
- Project section headings → each project's `.md` file (`## overview`, `## what i did`, etc.)
- Season picker footnote → `labels.md` key `season-info`; injected into HTML via `data-info` attribute on `#season-dropdown`; read by `script.js` from the DOM

If a string appears on the page, it must be editable without touching Python or CSS.

## Architecture

`build()` reads all content, calls render functions, then calls `render_page()` per page. Each render function is responsible for parsing its own markdown format — there is no markdown library.

| Function | Input | Output |
|---|---|---|
| `render_hero(md)` | hero.md | hero header |
| `render_about(md)` | about.md | two-column section |
| `render_toolkit(md)` | toolkit.md | tag cloud |
| `render_projects(heading_md, mds, labels)` | projects.md + projects/*.md | 3-col grid of internal-link cards (problem, org, year, tags) |
| `render_articles(md, labels)` | articles.md | 3-col grid + show-more |
| `render_lately(md)` | lately.md | activity list |
| `render_playground(md)` | playground.md | 2-col linked image card grid |
| `render_rolodex(md)` | ideas.md | randomised link list |
| `render_interests(md)` | interests.md | tag cloud |
| `render_project_page(md, labels)` | projects/*.md | case study page (problem as h1, org·year meta, tags+visit row, sections) |
| `render_page(template, css, js, ...)` | all above | complete HTML file |

`render_page()` rewrites asset paths based on `depth`: `0` = home, `1` = work/play (`../`), `2` = project detail (`../../`).

Template placeholders replaced by `render_page()`:

| Placeholder | Source |
|---|---|
| `{{meta}}` | meta.md |
| `{{body}}` | render function output |
| `{{footer}}` | footer.md |
| `{{nav_root}}` | depth-based prefix |
| `{{nav_work_active}}` | active page |
| `{{nav_play_active}}` | active page |
| `{{toast_email_copied}}` | `labels.md` key `email-copied` |
| `{{season_info}}` | `labels.md` key `season-info` |

Key helpers: `parse_kv_list` (lines → list of tuples), `parse_labels` (lines → dict), `slugify` (heading → URL slug), `_BOLD_RE` (compiled `**x**` regex — shared by `parse_bold_segments()` and `_apply_span()`), `_apply_span(text, cls)` (shared `**x**` → `<span>` impl), `apply_highlight` / `apply_name` (wrappers around `_apply_span`), `parse_inline` (`[x](url)` → `<a>`), `escape` (HTML-escape a string).

## Design system rules

- **Never use raw color values** — always use a CSS custom property. Dark mode works by swapping `--black`/`--white` at the `:root` level; hardcoded colors break it.
- **Never use magic numbers** — use spacing tokens. Full list in README.md. Key ones: `--space-sm/md/lg/xl`, `--box-gap`, `--inner-gap`, `--bar-h`, `--bar-pad`, `--btn-pad-x`, `--icon-sz`, `--icon-sz-lg`, `--ls-ui`, `--ls-label`, `--tag-pad`, `--tag-gap`.
- **New tokens must be documented** — add them to the comment block at the top of `style.css` with a description, and update the tables in README.md.
- **`.bar-box` is the universal interactive element** — extend with modifier classes only, never override base styles inline. Text bar-boxes add `width: auto` and `padding: 0 var(--btn-pad-x)`.
- **Icon sizes** — use `var(--icon-sz)` (16px) for inline/small icons and `var(--icon-sz-lg)` (18px) for bar-box icons. The `opsz` value in `font-variation-settings` must match numerically.
- **Hover pattern** — all bordered interactive box elements (`.bar-box`, `.project`, `.article`, `.lately-item`, `.rolodex-item`, `.playground-card`, `.nav-link-box`, `.season-option`) use the same hover: `background: var(--accent)`, `color: var(--on-accent)`, `border-color: var(--accent)`. Accent-coloured children (arrows, labels, publisher) must also be overridden to `var(--on-accent)` on hover. Always wrap in `@media (hover: hover)`.
- **`--on-accent`** — `#ffffff` in light mode, `#000000` in dark mode. Always use this token for text/icons on accent-coloured fills — never hardcode white or black.

## Accessibility rules

- Every icon-only button or link must have `aria-label`.
- Non-submit buttons must have `type="button"`.
- Hover styles must be inside `@media (hover: hover)` — touch devices must not get hover states.
- The `skip-to-content` link in `template.html` must remain the first focusable element.
- New icons must be added to `ICON_NAMES` in `build.py` — the font is subsetted at build time; missing icons render as blank.

## Release workflow

After a feature or fix is complete:

1. **Rebuild** — `python3 build.py` (required; `dist/` must match source)
2. **Commit** — stage both source files and `dist/` together
3. **Push** — `git push origin main` (triggers GitHub Actions deploy)
4. **Tag** — for any non-trivial change:
   ```bash
   git tag -a v1.x.x -m "short description"
   git push origin v1.x.x
   ```
5. **GitHub release** — only for minor and major versions (new features, redesigns). Patch tags do not need a GitHub release. Go to `github.com/<user>/<repo>/releases/new`, select the tag, write a short changelog, publish.

**When to tag:** every meaningful change — new feature, content update, design fix. Err on the side of tagging more often. Patch bumps are cheap.

**Versioning:** major = redesign, minor = new feature/section/page, patch = content or bug fix.

## Do not

- **No hardcoded copy in `build.py` or `script.js`** — use `content/labels.md`.
- **No raw colors in CSS** — use custom properties.
- **No new CSS tokens without documentation** in both `style.css` and README.md.
- **No new icons without updating `ICON_NAMES`** in `build.py`.
- **No bare interactive elements** — every button and icon link needs `aria-label` or visible text.
- **No hover styles outside `@media (hover: hover)`**.
- **No committing without rebuilding** — `dist/` must reflect the current source.
- **No pushing without tagging** — tag every meaningful commit after pushing.
- **No hardcoded letter-spacing values** — use `var(--ls-ui)` (1px, for nav/tags/buttons) or `var(--ls-label)` (0.5px, for meta/footer/small text).
- **No hardcoded tag padding or gap** — use `var(--tag-pad)` and `var(--tag-gap)`.
