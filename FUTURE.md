# FUTURE

Backlog and ideas. No shipped items live here — move them to [CHANGELOG.md](CHANGELOG.md) on release.

---

## NOW

Nothing urgent in progress.

---

## NEXT

### Analytics

**GoatCounter** is the recommendation: free forever for personal/non-commercial use, single script tag in `template.html`, no cookies, no personal data, GDPR-safe, ~3KB, open source. Alternatives: Umami Cloud (free tier, nicer dashboard), Cloudflare Web Analytics (zero JS, but requires routing through Cloudflare).

### Case study content

- `data-for-india-product` — `## impact` section is empty; fill in once data is available
- `vyapaar-mne` — team section still has placeholder text

### Instagram archive

Bring Instagram posts onto the site. Three approaches:

- **Instagram Graph API** — fetches at build time, same pattern as Glass.photo. Requires: professional account + Meta developer app + access token (expires every 60 days, needs a refresh step in the monthly Action). Most automated, most effort.
- **Manual JSON export** — download from Instagram settings → Your activity → Download your information. Parse in `build.py`, commit the file. No API, no tokens, fits the content-first philosophy. Lowest effort to start.
- **Third-party embed** (not recommended) — external dependency, JS embed, against the "no external cladding" aesthetic.

Recommendation: start with manual JSON export to get the page right. Layer in the API later if automation matters.

---

## LATER

### Product

- A writing/essays section separate from published articles — a space for thinking that isn't publication-shaped
- A now page: simpler than lately, just what I'm focused on right now in one sentence
- Show all articles without show-more, or paginate with page numbers instead of lazy expansion

### Tech debt

- `render_project_page` section parser could be extracted to a shared utility used by all section-based content

### DX

- Consider a watch mode: auto-rebuild `dist/` when any `content/` or source file changes (e.g. via `watchdog` or a simple polling loop)

---

*last updated: 2026-04-26*
