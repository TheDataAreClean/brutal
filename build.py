#!/usr/bin/env python3
"""Build script for brutal site.

Reads markdown content files, renders them into HTML,
and assembles multi-page output: /, /work/, /play/.

Usage:
  python3 build.py                 — normal build
  python3 build.py --gen-monthly   — regenerate all 12 monthly OG images + favicons
                                     (requires: pip install Pillow)
  python3 build.py --optimize-images — convert all PNG/JPG/JPEG in assets/ to WebP
                                       and delete the originals (requires: pip install Pillow)
"""

import json
import re
import shutil
import sys
import urllib.request
from datetime import datetime, timezone
from html import escape
from pathlib import Path

BASE = Path(__file__).parent
CONTENT = BASE / 'content'
DIST = BASE / 'dist'

SEASON_COLORS = [
    '#c84520',  # Jan — Flame of Forest
    '#7d4abf',  # Feb — Jacaranda
    '#9870b0',  # Mar — Pongamia
    '#b89010',  # Apr — Golden Shower
    '#c83020',  # May — Gulmohar
    '#a89018',  # Jun — Copper Pod
    '#c84568',  # Jul — Oleander
    '#c82852',  # Aug — Bougainvillea
    '#8040a8',  # Sep — Purple Bauhinia
    '#c85080',  # Oct — Tabebuia Rosea
    '#b87878',  # Nov — Rain Tree
    '#c02838',  # Dec — Poinsettia
]


FONT_PATH = BASE / 'assets' / 'fonts' / 'SchibstedGrotesk.ttf'
ICON_FONT_PATH = BASE / 'assets' / 'fonts' / 'MaterialSymbolsSharp.woff2'

ICON_NAMES = [
    'arrow_outward', 'close', 'coffee', 'construction', 'dark_mode',
    'directions_run', 'edit_note', 'explore', 'headphones', 'info',
    'keyboard_arrow_down', 'light_mode', 'mail', 'menu_book', 'movie',
    'pedal_bike', 'photo_camera', 'place', 'refresh', 'school',
    'skillet', 'sports_esports',
]


_BOLD_RE = re.compile(r'\*\*(.+?)\*\*')
_ITALIC_RE = re.compile(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)')
_NUM_LIST_RE = re.compile(r'^\d+\.\s+')
_SECTION_HDG_RE = re.compile(r'^(#{2,4})(\s|$)')
_IMG_RE = re.compile(r'^!\[([^\]]*)\]\(([^)]+)\)$')
# [text](url) — url may contain one level of balanced parens, e.g. Wikipedia's Foo_(bar)
_LINK_RE = re.compile(r'\[(.+?)\]\(((?:[^()\s]|\([^()\s]*\))+)\)')


def parse_bold_segments(text):
    """Split text into [(string, is_bold)] segments for OG image rendering."""
    segments = []
    last = 0
    for m in _BOLD_RE.finditer(text):
        if m.start() > last:
            segments.append((text[last:m.start()], False))
        segments.append((m.group(1), True))
        last = m.end()
    if last < len(text):
        segments.append((text[last:], False))
    return segments


def draw_segments(draw, x, y, segments, font, base_color, accent_color):
    """Draw text segments with accent highlighting for bold parts."""
    cursor_x = x
    for text, is_bold in segments:
        color = accent_color if is_bold else base_color
        draw.text((cursor_x, y), text, fill=color, font=font)
        bbox = draw.textbbox((0, 0), text, font=font)
        cursor_x += bbox[2] - bbox[0]


def parse_heading_tagline(md):
    """Parse a '# heading' line + plain tagline line, as used by hero.md."""
    lines = [l.strip() for l in md.strip().split('\n') if l.strip()]
    heading = ''
    tagline = ''
    for line in lines:
        if line.startswith('# '):
            heading = line[2:]
        else:
            tagline = line
    return heading, tagline


def _wrap_segments(draw, raw_text, font, max_width):
    """Word-wrap **bold**-tagged text into lines, each a list of (text, is_bold) segments
    that fit max_width — so headline/tagline sizing can stay fixed everywhere and long
    copy (e.g. a project's problem statement) wraps instead of shrinking."""
    space_w = draw.textbbox((0, 0), ' ', font=font)[2]
    lines = []
    current = []
    current_width = 0

    def word_width(word):
        bbox = draw.textbbox((0, 0), word, font=font)
        return bbox[2] - bbox[0]

    def place(word, is_bold, w_width):
        nonlocal current, current_width
        extra = (space_w if current else 0) + w_width
        if current and current_width + extra > max_width:
            lines.append(current)
            current = []
            current_width = 0
            extra = w_width
        current.append((f' {word}' if current else word, is_bold))
        current_width += extra

    for chunk, is_bold in parse_bold_segments(raw_text):
        for word in chunk.split(' '):
            if not word:
                continue
            w_width = word_width(word)
            if w_width <= max_width:
                place(word, is_bold, w_width)
                continue
            # Word alone is wider than the box (e.g. one long unbroken org name) — hard-break
            # it into pieces that each fit, instead of letting it overflow the right edge.
            piece = ''
            for ch in word:
                candidate = piece + ch
                if piece and word_width(candidate) > max_width:
                    place(piece, is_bold, word_width(piece))
                    piece = ch
                else:
                    piece = candidate
            if piece:
                place(piece, is_bold, word_width(piece))
    if current:
        lines.append(current)
    return lines or [[('', False)]]


def generate_og_image(accent_hex, heading_raw, tagline_raw, domain_text, site_name, output_path):
    """Generate OG image matching the site's viewport-box layout.

    Saved at 2x the 1200x630 OG spec (2400x1260, same aspect ratio) — the spec size is a floor,
    and at native pixel density it gets upscaled (by browsers, Mac Preview, chat/social unfurl
    previews) on any retina/high-DPI display, which reads as blur no matter how clean the source
    pixels are. The border and accent cube are flat 1px-at-1x shapes — drawn straight at that 2x
    output resolution (not further supersampled) so they stay pixel-perfect. Text is drawn on a
    separate, more highly supersampled transparent layer and downsampled with LANCZOS onto the 2x
    base for smooth anti-aliased edges (also needed for the faux-bold headline stroke, which
    looked like a soft grey halo without it). Supersampling shapes too, tried first, blurred the
    border into a multi-pixel grey smear on downsample — so shapes and text are on separate layers.
    """
    from PIL import Image, ImageDraw, ImageFont

    OUT = 2   # final output scale vs the 1200x630 OG spec — ships crisp on retina/high-DPI
    width, height = 1200 * OUT, 630 * OUT
    margin = 40 * OUT       # outer margin (viewport edge to box)
    box_pad = 60 * OUT      # padding inside the box, around the heading/tagline block
    corner_pad = 16 * OUT   # inset for the domain label from the top-right corner
    bar_h = 32 * OUT        # top/bottom bar height

    # Schibsted Grotesk has no glyph for hyphen/non-breaking-hyphen variants — normalize to ASCII
    heading_raw = heading_raw.replace('‐', '-').replace('‑', '-')
    tagline_raw = tagline_raw.replace('‐', '-').replace('‑', '-')

    accent = tuple(int(accent_hex[i:i+2], 16) for i in (1, 3, 5))
    black = (0x1a, 0x1a, 0x1a)
    white = (0xff, 0xff, 0xff)

    img = Image.new('RGB', (width, height), white)
    draw = ImageDraw.Draw(img)

    # Draw content viewport box
    box_top = margin
    box_bottom = height - margin
    draw.rectangle([margin, box_top, width - margin, box_bottom], outline=black, width=OUT)

    # Draw accent cube inside viewport box, top-left
    cube_size = bar_h
    cube_x = margin + OUT
    cube_y = box_top + OUT
    draw.rectangle([cube_x, cube_y, cube_x + cube_size, cube_y + cube_size], fill=accent)

    # --- Text layer: drawn supersampled on transparent, then downsampled onto the 2x base
    # for smooth anti-aliasing ---
    SS = 3
    text_layer = Image.new('RGBA', (width * SS, height * SS), (255, 255, 255, 0))
    tdraw = ImageDraw.Draw(text_layer)
    margin_ss, box_pad_ss, corner_pad_ss = margin * SS, box_pad * SS, corner_pad * SS
    cube_size_ss, cube_y_ss = cube_size * SS, cube_y * SS
    box_bottom_ss = box_bottom * SS

    # Domain label, top-right, padded snug into the corner to mirror the cube on the left.
    # Site-name portion (e.g. "thedataareclean") takes the accent colour, the rest (".com") stays black —
    # same accent-on-bold rule the heading/tagline use.
    font_domain = ImageFont.truetype(str(FONT_PATH), 20 * OUT * SS)
    d_bbox = tdraw.textbbox((0, 0), domain_text, font=font_domain)
    d_w, d_h = d_bbox[2] - d_bbox[0], d_bbox[3] - d_bbox[1]
    domain_x = width * SS - margin_ss - corner_pad_ss - d_w
    domain_y = cube_y_ss + (cube_size_ss - d_h) // 2
    domain_segments = (
        [(site_name, True), (domain_text[len(site_name):], False)]
        if site_name and domain_text.startswith(site_name)
        else [(domain_text, False)]
    )
    draw_segments(tdraw, domain_x, domain_y, domain_segments, font_domain, black, accent)

    # Fixed sizes everywhere — long copy (e.g. a project's problem statement) wraps to
    # multiple lines instead of shrinking, so headline weight stays consistent across pages.
    # SchibstedGrotesk.ttf is a variable font — use its real Bold instance for the headline
    # rather than faking it with a stroke (which read as a soft halo / chunky outline).
    font_lg = ImageFont.truetype(str(FONT_PATH), 64 * OUT * SS)
    font_lg.set_variation_by_name('Bold')
    font_sm = ImageFont.truetype(str(FONT_PATH), 24 * OUT * SS)
    max_text_width = (width - 2 * margin - 2 * box_pad) * SS

    heading_lines = _wrap_segments(tdraw, heading_raw, font_lg, max_text_width)
    tagline_lines = _wrap_segments(tdraw, tagline_raw, font_sm, max_text_width)

    # Use fixed font metrics (ascent + descent), not each string's tight glyph bbox — bbox
    # height varies with which letters are present (descenders like 'y'/'p' vs none), which
    # would shift the baseline differently per page.
    t_ascent, t_descent = font_sm.getmetrics()
    t_line = t_ascent + t_descent

    # The line-height already reserves each font's descent as trailing whitespace, which reads
    # as the gap between lines — no extra gap needed on top of that.
    line_gap = 4 * OUT * SS
    text_x = margin_ss + box_pad_ss
    box_top_ss = box_top * SS
    available_h = (box_bottom_ss - box_pad_ss) - (box_top_ss + box_pad_ss)
    min_heading_size = 32 * OUT * SS

    # Safety net for unusually long headings (normal copy never triggers this): shrink and
    # rewrap the heading until the block fits, rather than letting it clip above the box.
    while True:
        h_ascent, h_descent = font_lg.getmetrics()
        h_line = h_ascent + h_descent
        total_h = len(heading_lines) * h_line + line_gap + len(tagline_lines) * t_line
        if total_h <= available_h or font_lg.size <= min_heading_size:
            break
        font_lg = ImageFont.truetype(str(FONT_PATH), max(min_heading_size, round(font_lg.size * 0.85)))
        font_lg.set_variation_by_name('Bold')
        heading_lines = _wrap_segments(tdraw, heading_raw, font_lg, max_text_width)

    y = box_bottom_ss - box_pad_ss - total_h

    for line in heading_lines:
        draw_segments(tdraw, text_x, y, line, font_lg, black, accent)
        y += h_line
    y += line_gap
    for line in tagline_lines:
        draw_segments(tdraw, text_x, y, line, font_sm, black, accent)
        y += t_line

    text_layer = text_layer.resize((width, height), Image.LANCZOS)
    img.paste(text_layer, (0, 0), text_layer)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path)


def generate_favicon(accent_hex, output_path):
    """Generate favicon: white background, black border box, black square bottom-left."""
    from PIL import Image, ImageDraw
    size = 64
    margin = 8
    cube_size = 13
    black = (0x1a, 0x1a, 0x1a)
    white = (0xff, 0xff, 0xff)
    img = Image.new('RGB', (size, size), white)
    draw = ImageDraw.Draw(img)
    draw.rectangle([margin, margin, size - margin, size - margin], outline=black, width=1)
    cube_x = margin + 1
    cube_y = size - margin - cube_size
    draw.rectangle([cube_x, cube_y, cube_x + cube_size, cube_y + cube_size], fill=black)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path)


def read(path):
    return Path(path).read_text()


def parse_labels(md):
    """Parse labels.md into a dict of key: value pairs."""
    labels = {}
    for line in md.strip().split('\n'):
        stripped = line.strip()
        if stripped.startswith('- '):
            key, _, value = stripped[2:].partition(':')
            labels[key.strip()] = value.strip()
    return labels


def slugify(text):
    """Convert a project name to a URL slug."""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')


def _project_fields(md):
    """Extract a project markdown's front-matter (before the first '## section') into a dict."""
    fields = {'slug': '', 'org': '', 'url': '', 'problem': '', 'year': '', 'tags': '', 'added': ''}
    for line in md.strip().split('\n'):
        s = line.strip()
        if s.startswith('- '):
            key, _, val = s[2:].partition(':')
            key, val = key.strip(), val.strip()
            if key in fields:
                fields[key] = val
        elif s.startswith('## '):
            break
    fields['slug'] = fields['slug'] or slugify(fields['org'])
    return fields


def parse_inline(text):
    """Convert [text](url) to <a> tags."""
    return _LINK_RE.sub(
        r'<a href="\2" target="_blank" rel="noopener">\1</a>',
        text,
    )


def _apply_span(text, cls):
    """Convert **bold** to <span class="{cls}">bold</span>."""
    return _BOLD_RE.sub(rf'<span class="{cls}">\1</span>', text)


def apply_highlight(text):
    return _apply_span(text, 'highlight')


def apply_name(text):
    return _apply_span(text, 'name')


def render_inline(text):
    """HTML-escape then convert **bold**, *italic*, [link](url) to inline HTML."""
    text = escape(text)
    text = _BOLD_RE.sub(r'<strong>\1</strong>', text)
    text = _ITALIC_RE.sub(r'<em>\1</em>', text)
    text = _LINK_RE.sub(r'<a href="\2" target="_blank" rel="noopener">\1</a>', text)
    return text


def parse_kv_list(text):
    """Parse lines like '- key: value' into an ordered list of (key, value)."""
    items = []
    for line in text.strip().split('\n'):
        line = line.strip()
        if line.startswith('- '):
            key, _, value = line[2:].partition(':')
            items.append((key.strip(), value.strip()))
    return items


def parse_meta(md):
    """Parse meta.md into (site, pages).

    Top-level '- key: value' lines (before any '## page' header) are site-wide.
    Each '## page' header starts a per-page block of overrides — title,
    description, and (for pages without their own hero-style content file)
    heading/tagline for the OG image.
    """
    blocks = re.split(r'(?m)^## (.+)$', md.strip())
    site = dict(parse_kv_list(blocks[0]))
    pages = {
        blocks[i].strip(): dict(parse_kv_list(blocks[i + 1]))
        for i in range(1, len(blocks), 2)
    }
    return site, pages


def render_meta(title, description, url, image_url, favicon=''):
    title = escape(title)
    description = escape(description)
    return (
        f'  <title>{title}</title>\n'
        + (f'  <link rel="icon" type="image/png" href="{favicon}">\n' if favicon else '')
        + f'  <meta name="description" content="{description}">\n'
        f'  <meta property="og:type" content="website">\n'
        f'  <meta property="og:title" content="{title}">\n'
        f'  <meta property="og:description" content="{description}">\n'
        f'  <meta property="og:url" content="{url}">\n'
        f'  <meta property="og:image" content="{image_url}">\n'
        f'  <meta name="twitter:card" content="summary_large_image">\n'
        f'  <meta name="twitter:title" content="{title}">\n'
        f'  <meta name="twitter:description" content="{description}">\n'
        f'  <meta name="twitter:image" content="{image_url}">'
    )


def render_hero(md):
    heading, tagline = parse_heading_tagline(md)
    heading = apply_name(heading)
    tagline = apply_name(tagline)

    return (
        '  <!-- HERO -->\n'
        '  <header class="hero">\n'
        f'    <h1>{heading}</h1>\n'
        '    <p class="tagline">\n'
        f'      {tagline}\n'
        '    </p>\n'
        '  </header>'
    )


def render_about(md):
    lines = md.strip().split('\n')
    heading = ''
    paragraphs = []
    current = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith('# '):
            heading = stripped[2:]
        elif stripped == '':
            if current:
                paragraphs.append(' '.join(current))
                current = []
        else:
            current.append(stripped)
    if current:
        paragraphs.append(' '.join(current))

    # heading: "What is a **Data Communicator** ?"
    # → <span class="thin">What is a</span> <span class="highlight">Data Communicator</span> ?
    m = re.match(r'(.*?)\*\*(.+?)\*\*(.*)', heading)
    if m:
        before = m.group(1).strip()
        highlight = m.group(2)
        after = m.group(3)
        h2 = (
            '      <h2>\n'
            f'        <span class="thin">{before}</span>\n'
            f'        <span class="highlight">{highlight}</span>{after}\n'
            '      </h2>'
        )
    else:
        h2 = f'      <h2>{heading}</h2>'

    highlighted = [apply_highlight(p) for p in paragraphs]
    paras = '\n'.join(
        f'        <p>\n'
        f'          {p}\n'
        f'        </p>'
        for p in highlighted
    )

    return (
        '  <!-- ABOUT -->\n'
        '  <section>\n'
        '\n'
        '    <div class="about-content">\n'
        f'{h2}\n'
        '      <div class="about-text">\n'
        f'{paras}\n'
        '      </div>\n'
        '    </div>\n'
        '  </section>'
    )


def render_projects(heading_md, project_mds, labels):
    """Render the projects grid from a list of individual project markdown strings."""
    title = apply_highlight(heading_md.strip().lstrip('# '))
    case_study_label = labels.get('case-study', 'case study')
    projects = [f for f in (_project_fields(md) for md in project_mds) if f['org']]

    proj_parts = []
    for p in projects:
        problem = escape(p['problem'])
        year_html = (
            f' <span class="project-year">{escape(p["year"])}</span>'
            if p['year'] else ''
        )
        tags_html = ''
        if p['tags']:
            tag_spans = ''.join(
                f'<span class="project-tag">{t.strip()}</span>'
                for t in p['tags'].split(',') if t.strip()
            )
            if tag_spans:
                tags_html = f'\n        <span class="project-tags">{tag_spans}</span>'
        proj_parts.append(
            f'      <a class="project" href="{{{{nav_root}}}}work/{p["slug"]}/">\n'
            f'        <p class="project-problem">{problem}</p>\n'
            f'        <span class="project-meta"><span class="project-org">{escape(p["org"])}</span>{year_html}</span>{tags_html}\n'
            f'      </a>'
        )

    projects_inner = '\n'.join(proj_parts)

    return (
        '  <!-- PROJECTS -->\n'
        '  <section>\n'
        '    <h2 class="section-title">\n'
        f'      {title}\n'
        '    </h2>\n'
        '    <div class="projects">\n'
        f'{projects_inner}\n'
        '    </div>\n'
        '  </section>'
    )


def render_articles(md, labels):
    """Parse articles.md into a list of article cards."""
    lines = md.strip().split('\n')
    title = ''
    articles = []
    current = None

    for line in lines:
        stripped = line.strip()
        if stripped.startswith('# '):
            title = stripped[2:]
        elif stripped.startswith('## '):
            if current:
                articles.append(current)
            current = {'name': stripped[3:], 'publisher': '', 'date': '', 'tags': '', 'url': ''}
        elif stripped.startswith('- ') and current:
            key, _, value = stripped[2:].partition(':')
            key = key.strip()
            value = value.strip()
            if key in ('publisher', 'date', 'tags', 'url'):
                current[key] = value

    if current:
        articles.append(current)

    title = apply_highlight(title)

    initial = 6
    parts = []
    for idx, a in enumerate(articles):
        date_html = f' <span class="article-date">{a["date"]}</span>' if a['date'] else ''
        tags_html = ''
        if a.get('tags'):
            tag_spans = ''.join(
                f'<span class="article-tag">{t.strip()}</span>'
                for t in a['tags'].split(',')
                if t.strip()
            )
            if tag_spans:
                tags_html = f'\n        <span class="article-tags">{tag_spans}</span>'
        hidden = ' article-hidden' if idx >= initial else ''
        parts.append(
            f'      <a class="article{hidden}" href="{a["url"]}" target="_blank" rel="noopener">\n'
            f'        <span class="article-name">{a["name"]}</span>\n'
            f'        <span class="article-meta"><span class="article-publisher">{a["publisher"]}</span>{date_html}</span>{tags_html}\n'
            '        <span class="article-arrow"><span class="material-symbols-sharp">arrow_outward</span></span>\n'
            '      </a>'
        )

    articles_inner = '\n'.join(parts)

    show_more_label = labels.get('show-more', 'show more')
    has_more = len(articles) > initial
    show_more = (
        f'    <button type="button" class="bar-box articles-show-more" id="articles-show-more" aria-label="{show_more_label}">'
        f'{show_more_label} <span class="material-symbols-sharp">keyboard_arrow_down</span></button>\n'
        f'    <script>!function(){{var batch={initial};'
        'document.getElementById("articles-show-more").addEventListener("click",function(){'
        'var hidden=Array.from(document.querySelectorAll(".article-hidden"));'
        'hidden.slice(0,batch).forEach(function(el){{el.classList.remove("article-hidden");}});'
        'if(!document.querySelector(".article-hidden"))this.remove();'
        '});}();</script>\n'
    ) if has_more else ''

    return (
        '  <!-- ARTICLES -->\n'
        '  <section>\n'
        '    <h2 class="section-title">\n'
        f'      {title}\n'
        '    </h2>\n'
        '    <div class="articles">\n'
        f'{articles_inner}\n'
        '    </div>\n'
        + show_more
        + '  </section>'
    )


def render_lately(md):
    lines = md.strip().split('\n')
    title = ''
    kv_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('# '):
            title = stripped[2:]
        else:
            kv_lines.append(line)
    title = apply_highlight(title)
    items = parse_kv_list('\n'.join(kv_lines))
    label_map = {
        'read': ('menu_book', 'reading'),
        'listened': ('headphones', 'listening to'),
        'watched': ('movie', 'watching'),
        'cooked': ('skillet', 'cooking'),
        'explored': ('explore', 'exploring'),
        'played': ('sports_esports', 'playing'),
        'built': ('construction', 'building'),
        'learned': ('school', 'learning'),
        'ran': ('directions_run', 'running'),
        'cycled': ('pedal_bike', 'cycling'),
        'photographed': ('photo_camera', 'photographing'),
        'brewed': ('coffee', 'brewing'),
        'visited': ('place', 'visiting'),
        'wrote': ('edit_note', 'writing'),
    }

    parts = []
    for key, raw in items:
        raw = raw.strip()
        if not raw or key not in label_map:
            continue
        icon, label = label_map[key]
        # Extract URL and display text from [text](url), fall back to plain text
        m = _LINK_RE.match(raw)
        if m:
            display, url = m.group(1), m.group(2)
            parts.append(
                f'      <a class="lately-item" href="{url}" target="_blank" rel="noopener">\n'
                f'        <span class="lately-label"><span class="material-symbols-sharp">{icon}</span> {label}</span>\n'
                f'        <span class="lately-value">{display}</span>\n'
                '        <span class="lately-arrow"><span class="material-symbols-sharp">arrow_outward</span></span>\n'
                '      </a>'
            )
        else:
            parts.append(
                '      <div class="lately-item">\n'
                f'        <span class="lately-label"><span class="material-symbols-sharp">{icon}</span> {label}</span>\n'
                f'        <span class="lately-value">{raw}</span>\n'
                '      </div>'
            )

    return (
        '  <!-- LATELY -->\n'
        '  <section>\n'
        f'    <h2 class="section-title">{title}</h2>\n'
        '    <div class="lately-list">\n'
        + '\n'.join(parts) + '\n'
        + '    </div>\n'
        '  </section>'
    )


def render_footer(footer_md):
    items = dict(parse_kv_list(footer_md))
    location = items.get('location', '')
    designed = parse_inline(items.get('designed', ''))
    developed = parse_inline(items.get('developed', ''))
    license_text = parse_inline(items.get('license', ''))

    return (
        '    <div class="footer-meta">\n'
        f'      <span>{location}</span>\n'
        '      <span id="local-time">--:--</span>\n'
        '      <span id="temperature">--</span>\n'
        '      <span>AQI <span id="aqi">--</span></span>\n'
        '    </div>\n'
        '\n'
        '    <div class="footer-bottom">\n'
        f'      <span>{designed}</span>\n'
        f'      <span>{developed}</span>\n'
        f'      <span>{license_text}</span>\n'
        '    </div>'
    )


def render_toolkit(md):
    """Parse toolkit.md into a toolkit section."""
    lines = md.strip().split('\n')
    title = ''
    items = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith('# '):
            title = stripped[2:]
        elif stripped.startswith('- '):
            items.append(stripped[2:].strip())

    title = apply_highlight(title)

    boxes = '\n'.join(
        f'      <span class="offering-tag">{s}</span>'
        for s in items
    )

    return (
        '  <!-- OFFERINGS -->\n'
        '  <section>\n'
        f'    <h2 class="section-title">{title}</h2>\n'
        '    <div class="offerings">\n'
        f'{boxes}\n'
        '    </div>\n'
        '  </section>'
    )


def fetch_icon_font():
    """Download a subsetted Material Symbols Sharp woff2 via Google Fonts icon_names API."""
    icons = ','.join(sorted(ICON_NAMES))
    css_url = (
        'https://fonts.googleapis.com/css2?'
        'family=Material+Symbols+Sharp:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200'
        f'&icon_names={icons}&display=swap'
    )
    try:
        req = urllib.request.Request(css_url, headers={
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36',
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            css = resp.read().decode('utf-8')

        m = re.search(r"src:\s*url\(([^)]+)\)\s*format\('woff2'\)", css)
        if not m:
            print('Warning: could not find woff2 URL in icon font CSS, skipping.')
            return

        woff2_url = m.group(1).strip("'\"")
        ICON_FONT_PATH.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(woff2_url, ICON_FONT_PATH)
        print(f'Downloaded icon font ({ICON_FONT_PATH.stat().st_size:,} bytes)')

    except Exception as e:
        print(f'Warning: icon font download failed ({e}), keeping existing file.')


def render_playground(md):
    """Render playground section: linked image cards for external projects.

    Format per line: [Name](url) | image-filename.png | one-line description | year (optional)
    Images are served from assets/playground/.
    """
    lines = [l.strip() for l in md.strip().split('\n') if l.strip()]
    title = ''
    cards = []
    for line in lines:
        if line.startswith('# '):
            title = apply_highlight(line[2:])
        elif '|' in line:
            parts = [p.strip() for p in line.split('|', 3)]
            if len(parts) >= 3:
                m = _LINK_RE.match(parts[0])
                if m:
                    cards.append({
                        'name': m.group(1), 'url': m.group(2),
                        'img': parts[1], 'desc': parts[2],
                        'year': parts[3] if len(parts) == 4 else '',
                    })

    if not cards:
        return ''

    card_parts = []
    for c in cards:
        year_html = f'          <span class="playground-card-year">{escape(c["year"])}</span>\n' if c['year'] else ''
        card_parts.append(
            f'      <a class="playground-card" href="{escape(c["url"])}" target="_blank" rel="noopener" aria-label="{escape(c["name"])}">\n'
            f'        <div class="playground-card-img">\n'
            f'          <img src="{{{{nav_root}}}}assets/playground/{escape(c["img"])}" alt="{escape(c["name"])}" loading="lazy">\n'
            f'        </div>\n'
            f'        <div class="playground-card-body">\n'
            f'          <div class="playground-card-header">\n'
            f'            <span class="playground-card-name">{escape(c["name"])}</span>\n'
            f'            <span class="material-symbols-sharp playground-card-arrow" aria-hidden="true">arrow_outward</span>\n'
            f'          </div>\n'
            f'{year_html}'
            f'          <span class="playground-card-desc">{escape(c["desc"])}</span>\n'
            f'        </div>\n'
            f'      </a>'
        )

    return (
        '  <!-- PLAYGROUND -->\n'
        '  <section>\n'
        '    <h2 class="section-title">\n'
        f'      {title}\n'
        '    </h2>\n'
        '    <div class="playground-grid">\n'
        + '\n'.join(card_parts) + '\n'
        + '    </div>\n'
        '  </section>'
    )


def render_page_intro(text):
    """Render an opening tagline, **bold** becomes accent-colored."""
    styled = apply_name(text)
    return (
        '  <section class="page-intro">\n'
        f'    <p class="tagline">{styled}</p>\n'
        '  </section>'
    )


def render_work_body(intro_md, about_md, toolkit_md, projects_heading_md, project_mds, articles_md, labels):
    """Work page body: intro + about + toolkit + projects + articles."""
    intro_html = render_page_intro(intro_md.strip())
    about_html = render_about(about_md)
    toolkit_html = render_toolkit(toolkit_md)
    projects_html = render_projects(projects_heading_md, project_mds, labels)
    articles_html = render_articles(articles_md, labels)
    return intro_html + '\n\n' + about_html + '\n\n' + toolkit_html + '\n\n' + projects_html + '\n\n' + articles_html


def render_interests(md):
    """Parse interests.md into a tag list."""
    lines = md.strip().split('\n')
    title = ''
    subtitle = ''
    tags = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('# '):
            title = stripped[2:]
        elif stripped.startswith('- '):
            tags.append(stripped[2:].strip())
        elif stripped and not title:
            pass  # skip lines before heading
        elif stripped and not subtitle:
            subtitle = stripped

    title = apply_highlight(title)

    tag_html = '\n'.join(
        f'      <span class="interest-tag">{t}</span>'
        for t in tags
    )
    subtitle_html = f'    <p class="section-subtitle">{subtitle}</p>\n' if subtitle else ''

    return (
        '  <!-- INTERESTS -->\n'
        '  <section>\n'
        f'    <h2 class="section-title">{title}</h2>\n'
        f'{subtitle_html}'
        '    <div class="interests">\n'
        f'{tag_html}\n'
        '    </div>\n'
        '  </section>'
    )


def render_rolodex(md):
    """Parse ideas.md into a hidden list, JS picks 5 random on each load."""
    title = ''
    items = []
    for line in md.strip().split('\n'):
        stripped = line.strip()
        if stripped.startswith('# '):
            title = stripped[2:]
        elif stripped.startswith('- '):
            m = _LINK_RE.match(stripped[2:].strip())
            if m:
                items.append({'name': m.group(1), 'url': m.group(2)})

    title = apply_highlight(title)
    items_json = json.dumps(items)

    return (
        '  <!-- ROLODEX -->\n'
        '  <section>\n'
        '    <div class="rolodex-header">\n'
        f'      <h2 class="section-title">{title}</h2>\n'
        '      <button type="button" class="bar-box" id="rolodex-refresh" aria-label="Shuffle">'
        '<span class="material-symbols-sharp">refresh</span></button>\n'
        '    </div>\n'
        '    <div class="rolodex" id="rolodex"></div>\n'
        f'    <script>!function(){{var items={items_json};'
        'function shuffle(){var el=document.getElementById("rolodex");el.textContent="";'
        'var a=items.slice();for(var i=a.length-1;i>0;i--){var j=Math.floor(Math.random()*(i+1));var t=a[i];a[i]=a[j];a[j]=t;}'
        'a.slice(0,5).forEach(function(item){'
        'var link=document.createElement("a");link.className="rolodex-item";'
        'link.href=item.url;link.target="_blank";link.rel="noopener";'
        'var name=document.createElement("span");name.className="rolodex-name";name.textContent=item.name;'
        'var arrow=document.createElement("span");arrow.className="rolodex-arrow";'
        'arrow.innerHTML=\'<span class="material-symbols-sharp">arrow_outward</span>\';'
        'link.appendChild(name);link.appendChild(arrow);el.appendChild(link);'
        '});}'
        'shuffle();document.getElementById("rolodex-refresh").addEventListener("click",shuffle);'
        '}();</script>\n'
        '  </section>'
    )


def render_project_page(md, labels):
    """Parse a project detail markdown file into a case study page body."""
    lines = md.strip().split('\n')

    # --- Pass 1: extract front-matter key-value pairs (before first ## heading) ---
    front = _project_fields(md)
    org, url, problem, tags, year = front['org'], front['url'], front['problem'], front['tags'], front['year']

    # --- Pass 2: collect sections generically ---
    # Find the minimum heading level in this file — that becomes the section level.
    # Headings exactly one level deeper become subheadings within the current section.
    # Headings more than one level deeper start a new top-level section (skipped depth).
    section_level = min(
        (len(m.group(1)) for line in lines
         for m in [_SECTION_HDG_RE.match(line.strip())] if m),
        default=2,
    )
    subheading_level = section_level + 1

    sections = []
    current = None
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('<!--'):
            continue
        m = _SECTION_HDG_RE.match(stripped)
        if m:
            level = len(m.group(1))
            heading = stripped[level:].strip()
            if level == subheading_level and current is not None:
                current['lines'].append(('subheading', heading))
            else:
                current = {'heading': heading, 'lines': []}
                sections.append(current)
        elif current is not None and stripped:
            current['lines'].append(('line', stripped))

    # --- Render each section ---
    def _render_figure(caption, src):
        alt = escape(caption)
        s = escape(src)
        cap_html = f'\n      <figcaption class="project-figcaption">{alt}</figcaption>' if caption else ''
        return f'    <figure class="project-figure">\n      <img src="{s}" alt="{alt}" loading="lazy">{cap_html}\n    </figure>'

    def _render_section(sec):
        heading = escape(sec['heading'])
        raw_lines = sec['lines']
        if not raw_lines:
            return None

        # Classify each raw line into typed items for rendering
        # ('p', text) | ('li', text) | ('img', caption, src) | ('sub', text)
        items = []
        for kind, text in raw_lines:
            if kind == 'subheading':
                items.append(('sub', text))
            else:
                m = _IMG_RE.match(text)
                if m:
                    items.append(('img', m.group(1), m.group(2)))
                elif text.startswith('- '):
                    items.append(('li', text[2:]))
                elif _NUM_LIST_RE.match(text):
                    items.append(('li', _NUM_LIST_RE.sub('', text, count=1)))
                else:
                    items.append(('p', text))

        if not items:
            return None

        # Detect pure bullet-list sections (no paragraphs, no images, no subheadings)
        only_bullets = all(g[0] == 'li' for g in items)

        inner_parts = []

        if only_bullets:
            lis = '\n'.join(f'        <li>{render_inline(g[1])}</li>' for g in items)
            inner_parts.append(f'    <ul class="project-detail-list">\n{lis}\n    </ul>')
        else:
            # Track open list state across mixed content
            in_list = False
            for g in items:
                kind = g[0]
                if kind == 'sub':
                    if in_list:
                        inner_parts.append('    </ul>')
                        in_list = False
                    inner_parts.append(f'    <h3 class="project-subheading">{escape(g[1])}</h3>')
                elif kind == 'li':
                    if not in_list:
                        inner_parts.append('    <ul class="project-detail-list">')
                        in_list = True
                    inner_parts.append(f'      <li>{render_inline(g[1])}</li>')
                elif kind == 'p':
                    if in_list:
                        inner_parts.append('    </ul>')
                        in_list = False
                    inner_parts.append(f'    <p>{render_inline(g[1])}</p>')
                elif kind == 'img':
                    if in_list:
                        inner_parts.append('    </ul>')
                        in_list = False
                    inner_parts.append(_render_figure(g[1], g[2]))
            if in_list:
                inner_parts.append('    </ul>')

        if not inner_parts:
            return None

        inner = '\n'.join(inner_parts)
        return (
            '  <section class="project-section">\n'
            f'    <h2 class="section-title">{heading}</h2>\n'
            '    <div class="project-detail-text">\n'
            f'{inner}\n'
            '    </div>\n'
            '  </section>'
        )

    content_sections = [s for sec in sections for s in [_render_section(sec)] if s]

    visit_label = labels.get('visit-site', 'visit site')
    back_label = labels.get('back-to-work', '← back to work')

    meta_parts = [escape(p) for p in [org, year] if p]
    meta_html = ' · '.join(meta_parts)

    visit_btn = (
        f'<a class="bar-box project-visit-btn" href="{url}" target="_blank" rel="noopener" aria-label="{visit_label}">'
        f'<span class="material-symbols-sharp">arrow_outward</span></a>'
    ) if url else ''

    back_btn = f'    <a class="bar-box project-back" href="../">{back_label}</a>\n'

    heading = escape(problem) if problem else escape(org)

    tag_spans = ''.join(
        f'<span class="project-tag">{t.strip()}</span>'
        for t in tags.split(',') if t.strip()
    ) if tags else ''
    tags_row = (
        f'    <div class="project-header-tags">'
        f'<span class="project-tags">{tag_spans}</span>'
        + visit_btn +
        f'</div>\n'
    ) if (tag_spans or visit_btn) else ''

    back_section = f'  <section class="project-back-section">\n{back_btn}  </section>'

    return (
        '  <!-- PROJECT DETAIL -->\n'
        '  <section class="project-header">\n'
        f'    <h1 class="project-problem-heading">{heading}</h1>\n'
        + (f'    <p class="project-detail-meta">{meta_html}</p>\n' if meta_html else '')
        + tags_row
        + '  </section>\n\n'
        + ('\n\n'.join(content_sections) + '\n\n' if content_sections else '')
        + back_section
    )


def _to_pubdate(date_str):
    """Convert 'Mon YYYY', 'Month YYYY', or 'YYYY' to (datetime, RFC 822 string).

    Uses the 1st of the month as convention for month-only dates,
    and Jan 1st for year-only dates. Returns (None, None) if unparseable.
    """
    s = date_str.strip()
    try:
        dt = datetime.strptime(s, '%Y-%m-%d')
        return dt, dt.strftime('%a, %d %b %Y 00:00:00 +0000')
    except ValueError:
        pass
    for fmt in ('%b %Y', '%B %Y'):
        try:
            dt = datetime.strptime(s, fmt)
            return dt, dt.strftime('%a, %d %b %Y 00:00:00 +0000')
        except ValueError:
            pass
    try:
        dt = datetime(int(s), 1, 1)
        return dt, dt.strftime('%a, %d %b %Y 00:00:00 +0000')
    except ValueError:
        pass
    return None, None




def _abs_url(src, site_url):
    """Make a src path absolute. Prepends site_url for relative/root-relative paths."""
    if not src or src.startswith('http'):
        return src
    return site_url.rstrip('/') + '/' + src.lstrip('/')


def _domain_text(site_url):
    """Strip the protocol from a site URL, e.g. 'https://example.com' -> 'example.com'."""
    return re.sub(r'^https?://', '', site_url).rstrip('/')


def _first_project_image(md):
    """Return the src of the first ![...](src) found in a project markdown file."""
    for line in md.strip().split('\n'):
        m = _IMG_RE.match(line.strip())
        if m:
            return m.group(2)
    return None


def _feed_item(title, link, desc, date_str, guid, image_url=None):
    """Build a single RSS <item> block. Returns (datetime, xml_str) for sorting."""
    dt, pub = _to_pubdate(date_str) if date_str else (None, None)
    media = f'      <media:content url="{escape(image_url)}" medium="image"/>\n' if image_url else ''
    xml = (
        '    <item>\n'
        f'      <title>{escape(title)}</title>\n'
        f'      <link>{escape(link)}</link>\n'
        + (f'      <description>{escape(desc)}</description>\n' if desc else '')
        + (f'      <pubDate>{pub}</pubDate>\n' if pub else '')
        + f'      <guid isPermaLink="{"true" if link == guid else "false"}">{escape(guid)}</guid>\n'
        + media
        + '    </item>'
    )
    return dt or datetime.min, xml


def render_feed(articles_md, project_mds, lately_archive_md, playground_md, site_url, site_title, site_desc):
    """Generate RSS 2.0 feed XML aggregating articles, projects, lately, and playground."""
    site_url = site_url.rstrip('/')

    entries = []  # list of (datetime, xml_str)

    # --- Articles ---
    lines = articles_md.strip().split('\n')
    current = None
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('## '):
            if current:
                entries.append(_feed_item(
                    title=current['name'],
                    link=current['url'],
                    desc=' · '.join(filter(None, [current['publisher'], current['tags']])),
                    date_str=current['date'],
                    guid=current['url'],
                ))
            current = {'name': stripped[3:], 'publisher': '', 'date': '', 'tags': '', 'url': ''}
        elif stripped.startswith('- ') and current:
            key, _, value = stripped[2:].partition(':')
            key, value = key.strip(), value.strip()
            if key in ('publisher', 'date', 'tags', 'url'):
                current[key] = value
    if current:
        entries.append(_feed_item(
            title=current['name'],
            link=current['url'],
            desc=' · '.join(filter(None, [current['publisher'], current['tags']])),
            date_str=current['date'],
            guid=current['url'],
        ))

    # --- Projects ---
    for md in project_mds:
        p = _project_fields(md)
        if not p['added'] or not p['slug']:
            continue
        link = f'{site_url}/work/{p["slug"]}/'
        img_src = _first_project_image(md)
        entries.append(_feed_item(
            title=f'new case study: {p["org"]}',
            link=link,
            desc=p['problem'],
            date_str=p['added'],
            guid=link,
            image_url=_abs_url(img_src, site_url) if img_src else None,
        ))

    # --- Lately (from archive: ## Mon YYYY sections → items) ---
    label_map = {
        'read': 'reading', 'listened': 'listening to', 'watched': 'watching',
        'cooked': 'cooking', 'explored': 'exploring', 'played': 'playing',
        'built': 'building', 'learned': 'learning', 'ran': 'running',
        'cycled': 'cycling', 'photographed': 'photographing', 'brewed': 'brewing',
        'visited': 'visiting', 'wrote': 'writing',
    }
    current_date = ''
    for line in lately_archive_md.strip().split('\n'):
        s = line.strip()
        if s.startswith('## '):
            current_date = s[3:].strip()
            continue
        if not s.startswith('- ') or not current_date:
            continue
        key, _, raw = s[2:].partition(':')
        key, raw = key.strip(), raw.strip()
        if key not in label_map or not raw:
            continue
        m = _LINK_RE.match(raw)
        if m:
            display, url = m.group(1), m.group(2)
        else:
            display, url = raw, site_url
        label = label_map[key]
        entries.append(_feed_item(
            title=f'lately {label}: {display}',
            link=url,
            desc='',
            date_str=current_date,
            guid=f'lately:{key}:{url}',
        ))

    # --- Playground ---
    for line in playground_md.strip().split('\n'):
        s = line.strip()
        if '|' not in s or s.startswith('#'):
            continue
        parts = [p.strip() for p in s.split('|', 3)]
        if len(parts) < 3:
            continue
        m = _LINK_RE.match(parts[0])
        if not m:
            continue
        name, url = m.group(1), m.group(2)
        img_file = parts[1]
        desc = parts[2]
        year = parts[3] if len(parts) == 4 else ''
        entries.append(_feed_item(
            title=f'playground: {name}',
            link=url,
            desc=desc,
            date_str=year,
            guid=url,
            image_url=_abs_url(f'/assets/playground/{img_file}', site_url),
        ))

    # Sort newest first
    entries.sort(key=lambda e: e[0], reverse=True)

    now_rfc822 = datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S +0000')
    feed_url = f'{site_url}/feed.xml'
    items_xml = '\n'.join(xml for _, xml in entries)

    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:media="http://search.yahoo.com/mrss/">\n'
        '  <channel>\n'
        f'    <title>{escape(site_title)}</title>\n'
        f'    <link>{escape(site_url)}</link>\n'
        f'    <description>{escape(site_desc)}</description>\n'
        '    <language>en</language>\n'
        f'    <lastBuildDate>{now_rfc822}</lastBuildDate>\n'
        f'    <atom:link href="{escape(feed_url)}" rel="self" type="application/rss+xml"/>\n'
        f'{items_xml}\n'
        '  </channel>\n'
        '</rss>\n'
    )


def render_play_body(intro_md, lately_md, playground_md, interests_md, rolodex_md):
    """Play page body: intro + lately + playground + ideas + interests."""
    intro_html = render_page_intro(intro_md.strip())
    lately_html = render_lately(lately_md)
    playground_html = render_playground(playground_md)
    rolodex_html = render_rolodex(rolodex_md)
    interests_html = render_interests(interests_md)
    parts = [intro_html, lately_html]
    if playground_html:
        parts.append(playground_html)
    parts.append(rolodex_html)
    parts.append(interests_html)
    return '\n\n'.join(parts)


def render_page(template, css, js, meta_html, footer_html, body_html, active_nav, depth=0, labels=None):
    """Assemble a full HTML page with shared nav/footer, inlined CSS/JS."""
    prefix = '../' * depth if depth > 0 else ''

    html = template
    html = html.replace('{{meta}}', meta_html)
    html = html.replace('{{body}}', body_html)
    html = html.replace('{{footer}}', footer_html)
    html = html.replace('{{toast_email_copied}}', (labels or {}).get('email-copied', 'email copied'))
    html = html.replace('{{season_info}}', (labels or {}).get('season-info', ''))
    html = html.replace('{{feed_title}}', (labels or {}).get('feed-title', 'RSS Feed'))

    # Nav active states
    html = html.replace('{{nav_root}}', prefix)
    html = html.replace('{{nav_work_active}}', 'active' if active_nav == 'work' else '')
    html = html.replace('{{nav_play_active}}', 'active' if active_nav == 'play' else '')

    # Fix asset paths for subpages
    if prefix:
        html = html.replace('href="assets/', f'href="{prefix}assets/')
        html = html.replace('src="assets/', f'src="{prefix}assets/')
        html = html.replace('content="assets/', f'content="{prefix}assets/')

    # Inline minified CSS (rewrite url(assets/...) for subpages)
    minified_css = minify_css(css)
    if prefix:
        minified_css = minified_css.replace('url(assets/', f'url({prefix}assets/')
    html = html.replace(
        '  <link rel="stylesheet" href="style.css">',
        '  <style>\n' + minified_css + '  </style>',
    )

    # Inline minified JS
    html = html.replace(
        '  <script src="script.js"></script>',
        '  <script>\n' + minify_js(js) + '  </script>',
    )

    return html


def minify_css(css):
    """Remove comments and collapse whitespace in CSS."""
    css = re.sub(r'/\*.*?\*/', '', css, flags=re.DOTALL)
    css = re.sub(r'\n\s*\n', '\n', css)
    lines = []
    for line in css.split('\n'):
        stripped = line.rstrip()
        if stripped:
            lines.append(stripped)
    return '\n'.join(lines) + '\n'


def minify_js(js):
    """Remove blank lines and trailing whitespace in JS."""
    lines = []
    for line in js.split('\n'):
        stripped = line.rstrip()
        if stripped:
            lines.append(stripped)
    return '\n'.join(lines) + '\n'


def check_content(project_mds, playground_md):
    """Validate project and playground content.

    Checks for duplicate slugs, missing image assets, and missing playground assets.
    Prints a warning for each issue. Never halts the build.
    Returns the number of warnings emitted.
    """
    warnings = []
    seen_slugs = {}

    for md in project_mds:
        # Extract slug for readable warning labels
        slug = ''
        for line in md.strip().split('\n'):
            s = line.strip()
            if s.startswith('- slug:'):
                slug = s[7:].strip()
                break
            if s.startswith('## '):
                break

        if slug:
            if slug in seen_slugs:
                warnings.append(f'Warning: duplicate slug "{slug}"')
            else:
                seen_slugs[slug] = True

        for line in md.strip().split('\n'):
            m = _IMG_RE.match(line.strip())
            if not m:
                continue
            src = m.group(2)
            if src.startswith('http'):
                continue  # external URLs — skip
            path = BASE / src.lstrip('/')
            if not path.exists():
                label = f'[{slug}]' if slug else '[project]'
                warnings.append(f'Warning: missing asset {label}: {src}')

    for line in playground_md.strip().split('\n'):
        s = line.strip()
        if '|' not in s or s.startswith('#'):
            continue
        parts = [p.strip() for p in s.split('|', 3)]
        if len(parts) < 2:
            continue
        img_file = parts[1]
        path = BASE / 'assets' / 'playground' / img_file
        if not path.exists():
            warnings.append(f'Warning: missing playground asset: assets/playground/{img_file}')

    for w in warnings:
        print(w)
    return len(warnings)


def smoke_check(pages, project_fields):
    """Verify the build actually produced what it claims to.

    Doesn't check the output is *correct* — just that every expected dist/ file exists and
    is non-empty, so a swallowed exception or a silently-skipped write fails the build loudly
    instead of shipping stale or partial output.
    """
    expected = [DIST / path for path, *_rest in pages]
    expected += [
        DIST / 'feed.xml',
        DIST / 'assets' / 'favicon.png',
        DIST / 'assets' / 'og-image.png',
        DIST / 'assets' / 'og' / 'work.png',
        DIST / 'assets' / 'og' / 'play.png',
    ]
    expected += [DIST / 'assets' / 'og' / 'work' / f'{f["slug"]}.png' for f in project_fields]

    missing = [p for p in expected if not p.exists() or p.stat().st_size == 0]
    if missing:
        print('Smoke check FAILED — missing or empty output:')
        for p in missing:
            print(f'  {p.relative_to(DIST.parent)}')
        sys.exit(1)
    print(f'Smoke check passed — {len(expected)} expected files present.')


def build():
    template = read(BASE / 'template.html')
    css = read(BASE / 'style.css')
    js = read(BASE / 'script.js')

    site, meta_pages = parse_meta(read(CONTENT / 'meta.md'))
    domain_text = _domain_text(site.get('url', ''))
    site_name = site.get('site-name', '')
    # .get(page, {}) + .get(key, '') below so an incomplete meta.md (a missing section or
    # key) degrades to an empty string instead of crashing the build with a KeyError.
    home_meta = meta_pages.get('home', {})
    work_meta = meta_pages.get('work', {})
    play_meta = meta_pages.get('play', {})
    footer_md  = read(CONTENT / 'footer.md')
    hero_md    = read(CONTENT / 'hero.md')

    work_intro_md   = read(CONTENT / 'work' / 'intro.md')
    about_md            = read(CONTENT / 'work' / 'about.md')
    toolkit_md          = read(CONTENT / 'work' / 'toolkit.md')
    projects_heading_md = read(CONTENT / 'work' / 'projects.md')
    articles_md         = read(CONTENT / 'work' / 'articles.md')

    play_intro_md       = read(CONTENT / 'play' / 'intro.md')
    lately_md           = read(CONTENT / 'play' / 'lately.md')
    lately_archive_md   = read(CONTENT / 'play' / 'lately-archive.md')
    playground_md       = read(CONTENT / 'play' / 'playground.md')
    ideas_md            = read(CONTENT / 'play' / 'ideas.md')
    interests_md        = read(CONTENT / 'play' / 'interests.md')

    labels = parse_labels(read(CONTENT / 'labels.md'))

    # Shared pieces
    footer_html = render_footer(footer_md)

    # Download subsetted icon font
    fetch_icon_font()

    # Project files (shared by grid cards and detail pages)
    project_detail_files = list((CONTENT / 'work' / 'projects').glob('*.md'))
    project_mds_all = [read(f) for f in project_detail_files]

    # Validate image references before building
    check_content(project_mds_all, playground_md)

    # Page bodies
    home_body = render_hero(hero_md)
    play_body = render_play_body(play_intro_md, lately_md, playground_md, interests_md, ideas_md)

    # Project detail pages — use the slug parsed from the markdown (same slug the card links use).
    # Parse each project's front-matter once and carry the result alongside its md everywhere below,
    # rather than re-parsing per use.
    project_fields_all = [(md, _project_fields(md)) for md in project_mds_all]

    # Order projects by content/work/project-order.md (one slug per line).
    # Projects not listed appear after ordered ones.
    _order_md = read(CONTENT / 'work' / 'project-order.md')
    _order_slugs = [l.strip()[2:].strip() for l in _order_md.splitlines() if l.strip().startswith('- ')]
    project_fields_all.sort(key=lambda pair: _order_slugs.index(pair[1]['slug']) if pair[1]['slug'] in _order_slugs else len(_order_slugs))
    project_mds = [md for md, _ in project_fields_all]
    project_fields = [f for _, f in project_fields_all]

    work_body = render_work_body(work_intro_md, about_md, toolkit_md, projects_heading_md, project_mds, articles_md, labels)

    project_pages = [
        (f'work/{f["slug"]}/index.html', render_project_page(md, labels), 'work', 2)
        for md, f in zip(project_mds, project_fields)
    ]

    # Copy pre-generated monthly OG image (home)
    month = datetime.now().month  # 1-indexed
    monthly = BASE / 'assets' / 'monthly'
    og_src = monthly / f'og-{month:02d}.png'
    if og_src.exists():
        shutil.copy2(og_src, BASE / 'assets' / 'og-image.png')
    else:
        print(f'Warning: monthly OG image missing for month {month:02d}, run: python3 build.py --gen-monthly')

    # Generate static favicon
    accent = SEASON_COLORS[month - 1]
    generate_favicon(accent, BASE / 'assets' / 'favicon.png')

    # Generate per-page OG images (work, play, each project) — built fresh every run
    # so they always match current content, unlike home's precomputed monthly set.
    og_dir = BASE / 'assets' / 'og'
    generate_og_image(accent, work_meta.get('heading', ''), work_meta.get('tagline', ''), domain_text, site_name, og_dir / 'work.png')
    generate_og_image(accent, play_meta.get('heading', ''), play_meta.get('tagline', ''), domain_text, site_name, og_dir / 'play.png')
    for f in project_fields:
        year_display = re.sub(r'\s*[-–—]\s*', ' - ', f['year']) if f['year'] else ''
        org_display = f'**{f["org"]}**' if f['org'] else ''
        project_tagline = ' · '.join(p for p in [org_display, year_display] if p)
        generate_og_image(accent, f['problem'], project_tagline, domain_text, site_name, og_dir / 'work' / f'{f["slug"]}.png')

    # Per-page meta tags — title/description/image differ per page instead of being shared site-wide
    site_url = site.get('url', '').rstrip('/')
    favicon = site.get('favicon', '')

    home_meta_html = render_meta(
        home_meta.get('title', ''), home_meta.get('description', ''), site_url + '/',
        _abs_url('assets/og-image.png', site_url), favicon,
    )
    work_meta_html = render_meta(
        work_meta.get('title', ''), work_meta.get('description', ''), site_url + '/work/',
        _abs_url('assets/og/work.png', site_url), favicon,
    )
    play_meta_html = render_meta(
        play_meta.get('title', ''), play_meta.get('description', ''), site_url + '/play/',
        _abs_url('assets/og/play.png', site_url), favicon,
    )

    def _project_meta_html(f):
        title = f'{f["org"]} | {site_name}' if f['org'] else home_meta.get('title', '')
        return render_meta(
            title, f['problem'], site_url + f'/work/{f["slug"]}/',
            _abs_url(f'assets/og/work/{f["slug"]}.png', site_url), favicon,
        )

    # Build pages
    pages = [
        ('index.html', home_meta_html, home_body, 'home', 0),
        ('work/index.html', work_meta_html, work_body, 'work', 1),
        ('play/index.html', play_meta_html, play_body, 'play', 1),
        *[(path, _project_meta_html(f), body, active, depth)
          for f, (path, body, active, depth) in zip(project_fields, project_pages)],
    ]

    DIST.mkdir(exist_ok=True)

    for path, page_meta_html, body, active, depth in pages:
        html = render_page(template, css, js, page_meta_html, footer_html, body, active, depth, labels=labels)
        out = DIST / path
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html)
        print(f'Built dist/{path} ({len(html)} bytes)')

    # Copy assets
    assets_src = BASE / 'assets'
    if assets_src.is_dir():
        assets_dst = DIST / 'assets'
        if assets_dst.exists():
            shutil.rmtree(assets_dst)
        shutil.copytree(assets_src, assets_dst, ignore=shutil.ignore_patterns('README.md', 'monthly'))

    # Generate RSS feed
    feed_xml = render_feed(articles_md, project_mds, lately_archive_md, playground_md, site_url, home_meta['title'], home_meta['description'])
    (DIST / 'feed.xml').write_text(feed_xml)
    print(f'Built dist/feed.xml ({len(feed_xml)} bytes)')

    # Copy CNAME for GitHub Pages
    cname = BASE / 'CNAME'
    if cname.exists():
        shutil.copy2(cname, DIST / 'CNAME')

    smoke_check(pages, project_fields)
    print(f'Done — og accent: {accent}')


MONTH_NAMES = [
    'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
]


def generate_monthly_assets():
    """Generate all 12 monthly OG images into assets/monthly/."""
    heading, tagline = parse_heading_tagline((CONTENT / 'hero.md').read_text())
    site, _ = parse_meta((CONTENT / 'meta.md').read_text())
    domain_text = _domain_text(site.get('url', ''))
    site_name = site.get('site-name', '')
    out_dir = BASE / 'assets' / 'monthly'
    out_dir.mkdir(parents=True, exist_ok=True)
    for i, (accent, name) in enumerate(zip(SEASON_COLORS, MONTH_NAMES), start=1):
        og_path = out_dir / f'og-{i:02d}.png'
        generate_og_image(accent, heading, tagline, domain_text, site_name, og_path)
        print(f'Generated {name} ({accent}): {og_path.name}')
    print('Done — all 12 monthly OG images generated.')


def optimize_images():
    """Convert all PNG/JPG/JPEG in assets/ to WebP and delete the originals.

    Skips: assets/monthly/ (source OG images), assets/fonts/, favicon.png.
    Already-WebP files are ignored. Run once after adding new raster images.
    """
    from PIL import Image

    SKIP_FILES = {'favicon.png', 'og-image.png'}
    SKIP_DIRS = {'monthly', 'fonts', 'og'}
    EXTENSIONS = {'.png', '.jpg', '.jpeg'}
    TARGET_W = 1200
    QUALITY = 82

    assets = BASE / 'assets'
    candidates = [
        p for p in assets.rglob('*')
        if p.suffix.lower() in EXTENSIONS
        and p.name not in SKIP_FILES
        and not any(part in SKIP_DIRS for part in p.parts)
    ]

    if not candidates:
        print('No images to optimise.')
        return

    for src in sorted(candidates):
        img = Image.open(src)
        # Flatten alpha to white
        if img.mode in ('RGBA', 'LA', 'P'):
            if img.mode == 'P':
                img = img.convert('RGBA')
            bg = Image.new('RGB', img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = bg
        elif img.mode != 'RGB':
            img = img.convert('RGB')

        # Downscale if wider than target
        w, h = img.size
        if w > TARGET_W:
            img = img.resize((TARGET_W, round(h * TARGET_W / w)), Image.LANCZOS)

        out = src.with_suffix('.webp')
        img.save(out, 'WEBP', quality=QUALITY, method=6)
        orig_kb = src.stat().st_size / 1024
        new_kb = out.stat().st_size / 1024
        src.unlink()
        rel = src.relative_to(BASE)
        print(f'{rel}  {orig_kb:.0f}KB → {out.name}  {new_kb:.0f}KB  ({new_kb/orig_kb*100:.0f}%)')

    print('Done — all images optimised.')


if __name__ == '__main__':
    if '--gen-monthly' in sys.argv:
        generate_monthly_assets()
    elif '--optimize-images' in sys.argv:
        optimize_images()
    else:
        build()
