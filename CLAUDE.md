# Portfolio — CLAUDE.md

Rules, constraints, and things easy to get wrong. For architecture, content formats, and design token reference — see [APP.md](APP.md).

## Build

```bash
python3 build.py
```

No dev server. Edits only take effect after a build. `dist/` is git-tracked — commit both source and `dist/` together.

## Content-first principle

**All user-visible text lives in `content/*.md` files.** Never write copy into `build.py`, `template.html`, `script.js`, or `style.css`. This includes:

- Section headings → each section's own `.md` file
- Button and UI labels → `content/labels.md` (keys are fixed; edit values only)
- Project section headings → each project's `.md` file (`## overview`, `## what i did`, etc.)
- Season picker footnote → `labels.md` key `season-info`

If a string appears on the page, it must be editable without touching Python or CSS.

## Architecture

See [APP.md](APP.md) for the full render function table, template placeholder reference, and key helpers. Short version: `build()` reads all content, calls render functions, calls `render_page()` per page. No markdown library — each render function parses its own format.

## Design system rules

- **Never use raw color values** — always use a CSS custom property. Dark mode swaps `--black`/`--white` at `:root`; hardcoded colors break it.
- **Never use magic numbers** — use spacing tokens. Full token tables in [APP.md](APP.md).
- **New tokens must be documented** — add to the comment block at the top of `style.css` and to the tables in APP.md.
- **`.bar-box` is the universal interactive element** — extend with modifier classes only, never override base styles inline.
- **Icon sizes** — `var(--icon-sz)` (16px) for inline icons, `var(--icon-sz-lg)` (18px) for bar-box icons. The `opsz` value in `font-variation-settings` must match numerically.
- **Hover pattern** — all bordered interactive elements use: `background: var(--accent)`, `color: var(--on-accent)`, `border-color: var(--accent)`. Accent-coloured children must also override to `var(--on-accent)`. Always wrap in `@media (hover: hover)`.
- **`--on-accent`** — `#ffffff` light / `#000000` dark. Always use for text/icons on accent fills.

## Accessibility rules

- Every icon-only button or link must have `aria-label`.
- Non-submit buttons must have `type="button"`.
- Hover styles must be inside `@media (hover: hover)`.
- The `skip-to-content` link in `template.html` must remain the first focusable element.

## Release workflow

1. **Rebuild** — `python3 build.py`
2. **Commit** — stage source and `dist/` together
3. **Push** — `git push origin main`
4. **Tag** — `git tag -a vX.Y.Z -m "description"` && `git push origin vX.Y.Z`
5. **GitHub release** — minor and major only; patches don't need one
6. **CHANGELOG** — move UNRELEASED entries to the new version

Versioning: **major** = redesign · **minor** = new feature/section/page · **patch** = content or bug fix.

## Do not

- **No hardcoded copy in `build.py` or `script.js`** — use `content/labels.md`.
- **No raw colors in CSS** — use custom properties.
- **No new CSS tokens without documentation** in `style.css` and APP.md.
- **No new icons without updating `ICON_NAMES`** in `build.py`.
- **No bare interactive elements** — every button and icon link needs `aria-label` or visible text.
- **No hover styles outside `@media (hover: hover)`**.
- **No committing without rebuilding** — `dist/` must reflect the current source.
- **No pushing without tagging** — tag every meaningful commit after pushing.
- **No hardcoded letter-spacing** — use `var(--ls-ui)` (1px) or `var(--ls-label)` (0.5px).
- **No hardcoded tag padding or gap** — use `var(--tag-pad)` and `var(--tag-gap)`.
- **No unoptimised images** — all raster images in `assets/` must be WebP. Run `python3 build.py --optimize-images` after adding any PNG/JPG. Exceptions: `favicon.png`, `og-image.png`, `assets/monthly/`.
