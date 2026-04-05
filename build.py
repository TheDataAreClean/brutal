#!/usr/bin/env python3
"""Build script for brutal site.

Reads markdown content files, renders them into HTML,
and assembles multi-page output: /, /work/, /play/.

Usage:
  python3 build.py               — normal build
  python3 build.py --gen-monthly — regenerate all 12 monthly OG images + favicons
                                   (requires: pip install Pillow)
"""

import json
import re
import shutil
import sys
import urllib.request
from datetime import datetime
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


def parse_bold_segments(text):
    """Split text into segments: [(string, is_bold), ...].

    **bold** markers indicate accent-colored text.
    """
    segments = []
    parts = re.split(r'(\*\*.+?\*\*)', text)
    for part in parts:
        if part.startswith('**') and part.endswith('**'):
            segments.append((part[2:-2], True))
        else:
            segments.append((part, False))
    return segments


def draw_segments(draw, x, y, segments, font, base_color, accent_color):
    """Draw text segments with accent highlighting for bold parts."""
    cursor_x = x
    for text, is_bold in segments:
        color = accent_color if is_bold else base_color
        draw.text((cursor_x, y), text, fill=color, font=font)
        bbox = draw.textbbox((0, 0), text, font=font)
        cursor_x += bbox[2] - bbox[0]


def generate_og_image(accent_hex, hero_md, output_path):
    """Generate OG image matching the site's viewport-box layout."""
    from PIL import Image, ImageDraw, ImageFont

    width, height = 1200, 630
    margin = 40       # outer margin (viewport edge to box)
    box_pad = 60      # padding inside the box
    bar_h = 32        # top/bottom bar height

    # Parse hero content (keep ** markers for segment parsing)
    lines = [l.strip() for l in hero_md.strip().split('\n') if l.strip()]
    heading_raw = ''
    tagline_raw = ''
    for line in lines:
        if line.startswith('# '):
            heading_raw = line[2:]
        else:
            tagline_raw = line

    accent = tuple(int(accent_hex[i:i+2], 16) for i in (1, 3, 5))
    black = (0x1a, 0x1a, 0x1a)
    white = (0xff, 0xff, 0xff)

    img = Image.new('RGB', (width, height), white)
    draw = ImageDraw.Draw(img)

    # Draw content viewport box
    box_top = margin
    box_bottom = height - margin
    draw.rectangle([margin, box_top, width - margin, box_bottom], outline=black, width=1)

    # Draw accent cube inside viewport box, top-left
    cube_size = bar_h
    cube_x = margin + 1
    cube_y = box_top + 1
    draw.rectangle([cube_x, cube_y, cube_x + cube_size, cube_y + cube_size], fill=accent)

    # Load Schibsted Grotesk at two sizes
    font_lg = ImageFont.truetype(str(FONT_PATH), 64)
    font_sm = ImageFont.truetype(str(FONT_PATH), 24)

    # Strip ** for measurement
    heading_plain = heading_raw.replace('**', '')
    tagline_plain = tagline_raw.replace('**', '')

    # Position: bottom-left inside the content box
    h_bbox = draw.textbbox((0, 0), heading_plain, font=font_lg)
    h_h = h_bbox[3] - h_bbox[1]
    t_bbox = draw.textbbox((0, 0), tagline_plain, font=font_sm)
    t_h = t_bbox[3] - t_bbox[1]

    text_x = margin + box_pad
    total_h = h_h + 20 + t_h
    y_start = box_bottom - box_pad - total_h

    # Draw heading and tagline with accent on **bold** segments
    heading_segments = parse_bold_segments(heading_raw)
    tagline_segments = parse_bold_segments(tagline_raw)

    draw_segments(draw, text_x, y_start, heading_segments, font_lg, black, accent)
    draw_segments(draw, text_x, y_start + h_h + 20, tagline_segments, font_sm, black, accent)

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


def parse_inline(text):
    """Convert [text](url) to <a> tags."""
    return re.sub(
        r'\[(.+?)\]\((.+?)\)',
        r'<a href="\2" target="_blank" rel="noopener">\1</a>',
        text,
    )


def _apply_span(text, cls):
    """Convert **bold** to <span class="{cls}">bold</span>."""
    return re.sub(r'\*\*(.+?)\*\*', rf'<span class="{cls}">\1</span>', text)


def apply_highlight(text):
    return _apply_span(text, 'highlight')


def apply_name(text):
    return _apply_span(text, 'name')


def parse_kv_list(text):
    """Parse lines like '- key: value' into an ordered list of (key, value)."""
    items = []
    for line in text.strip().split('\n'):
        line = line.strip()
        if line.startswith('- '):
            key, _, value = line[2:].partition(':')
            items.append((key.strip(), value.strip()))
    return items


def render_meta(md):
    items = dict(parse_kv_list(md))
    title = items.get('title', '')
    desc = items.get('description', '')
    url = items.get('url', '')
    image = items.get('image', '')
    favicon = items.get('favicon', '')
    image_url = url.rstrip('/') + '/' + image if image and not image.startswith('http') else image

    return (
        f'  <title>{title}</title>\n'
        + (f'  <link rel="icon" type="image/png" href="{favicon}">\n' if favicon else '')
        + f'  <meta name="description" content="{desc}">\n'
        f'  <meta property="og:type" content="website">\n'
        f'  <meta property="og:title" content="{title}">\n'
        f'  <meta property="og:description" content="{desc}">\n'
        f'  <meta property="og:url" content="{url}">\n'
        f'  <meta property="og:image" content="{image_url}">\n'
        f'  <meta name="twitter:card" content="summary_large_image">\n'
        f'  <meta name="twitter:title" content="{title}">\n'
        f'  <meta name="twitter:description" content="{desc}">\n'
        f'  <meta name="twitter:image" content="{image_url}">'
    )


def render_hero(md):
    lines = [l for l in md.strip().split('\n') if l.strip()]
    heading = ''
    tagline = ''
    for line in lines:
        line = line.strip()
        if line.startswith('# '):
            heading = line[2:]
        else:
            tagline = line

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
    projects = []

    for md in project_mds:
        p = {'name': '', 'role': '', 'url': '', 'desc': '', 'slug': ''}
        for line in md.strip().split('\n'):
            stripped = line.strip()
            if stripped.startswith('# '):
                p['name'] = stripped[2:]
                p['slug'] = slugify(stripped[2:])
            elif stripped.startswith('- ') and not stripped.startswith('## '):
                key, _, value = stripped[2:].partition(':')
                key = key.strip()
                value = value.strip()
                if key in ('role', 'url', 'desc'):
                    p[key] = value
            elif stripped.startswith('## '):
                break  # stop at first section heading
        if p['name']:
            projects.append(p)

    proj_parts = []
    for p in projects:
        desc = parse_inline(p['desc'])
        proj_parts.append(
            f'      <div class="project">\n'
            f'        <span class="project-name">{p["name"]}</span>\n'
            f'        <span class="project-role">{p["role"]}</span>\n'
            f'        <span class="project-desc">{desc}</span>\n'
            '        <div class="project-actions">\n'
            f'          <a class="bar-box project-visit" href="{p["url"]}" target="_blank" rel="noopener" aria-label="Visit site"><span class="material-symbols-sharp">arrow_outward</span></a>\n'
            f'          <a class="bar-box project-casestudy" href="{{{{nav_root}}}}work/{p["slug"]}/">{case_study_label}</a>\n'
            '        </div>\n'
            '      </div>'
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
    items = dict(parse_kv_list('\n'.join(kv_lines)))
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
        'drank': ('coffee', 'drinking'),
        'visited': ('place', 'visiting'),
        'wrote': ('edit_note', 'writing'),
    }

    order = ('read', 'listened', 'watched', 'cooked', 'explored',
             'played', 'built', 'learned', 'ran', 'cycled',
             'photographed', 'drank', 'visited', 'wrote')

    parts = []
    for key in order:
        raw = items.get(key, '').strip()
        if not raw:
            continue
        icon, label = label_map[key]
        # Extract URL and display text from [text](url), fall back to plain text
        m = re.match(r'\[(.+?)\]\((.+?)\)', raw)
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
                m = re.match(r'\[(.+?)\]\((.+?)\)', parts[0])
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
        '    <div class="projects">\n'
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
    work_html = render_toolkit(toolkit_md)
    projects_html = render_projects(projects_heading_md, project_mds, labels)
    articles_html = render_articles(articles_md, labels)
    return intro_html + '\n\n' + about_html + '\n\n' + work_html + '\n\n' + projects_html + '\n\n' + articles_html


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
            m = re.match(r'\[(.+?)\]\((.+?)\)', stripped[2:].strip())
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
    name = ''
    role = ''
    url = ''
    section = None
    section_headings = {}  # section_key -> display heading from markdown
    section_order = ['overview', 'contribution', 'highlights']
    section_idx = 0
    overview_lines = []
    contribution_items = []
    highlight_items = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith('# '):
            name = stripped[2:]
        elif stripped.startswith('- role:'):
            role = stripped[7:].strip()
        elif stripped.startswith('- url:'):
            url = stripped[6:].strip()
        elif stripped.startswith('## ') and not stripped.startswith('- '):
            if section_idx < len(section_order):
                key = section_order[section_idx]
                section_headings[key] = stripped[3:]
                section = key
                section_idx += 1
        elif section == 'overview' and stripped and not stripped.startswith('- '):
            overview_lines.append(stripped)
        elif section == 'contribution' and stripped.startswith('- '):
            contribution_items.append(stripped[2:])
        elif section == 'highlights' and stripped.startswith('- '):
            highlight_items.append(stripped[2:])

    overview_heading = section_headings.get('overview', 'overview')
    contrib_heading = section_headings.get('contribution', 'what i did')
    highlights_heading = section_headings.get('highlights', 'highlights')

    visit_label = labels.get('visit-site', 'visit site')
    back_label = labels.get('back-to-work', '← back to work')

    overview_html = '\n'.join(
        f'        <p>{p}</p>' for p in overview_lines
    )
    contrib_html = '\n'.join(
        f'        <li>{item}</li>' for item in contribution_items
    )
    highlights_html = '\n'.join(
        f'        <div class="project-highlight">{parse_inline(item)}</div>'
        for item in highlight_items
    )

    visit_btn = (
        f'    <a class="bar-box project-back" href="{url}" target="_blank" rel="noopener">'
        f'{visit_label} <span class="material-symbols-sharp">arrow_outward</span></a>\n'
    ) if url else ''

    last_section = (
        '  <section>\n'
        f'    <h2 class="section-title">{highlights_heading}</h2>\n'
        '    <div class="project-highlights">\n'
        f'{highlights_html}\n'
        '    </div>\n'
        f'    <a class="bar-box project-back" href="../">{back_label}</a>\n'
        '  </section>'
        if highlights_html else
        '  <section>\n'
        f'    <a class="bar-box project-back" href="../">{back_label}</a>\n'
        '  </section>'
    )

    return (
        '  <!-- PROJECT DETAIL -->\n'
        '  <section class="project-header">\n'
        f'    <h1>{name}</h1>\n'
        f'    <p class="project-role">{role}</p>\n'
        f'    {visit_btn}'
        '  </section>\n\n'
        '  <section>\n'
        f'    <h2 class="section-title">{overview_heading}</h2>\n'
        '    <div class="project-detail-text">\n'
        f'{overview_html}\n'
        '    </div>\n'
        '  </section>\n\n'
        '  <section>\n'
        f'    <h2 class="section-title">{contrib_heading}</h2>\n'
        '    <ul class="project-detail-list">\n'
        f'{contrib_html}\n'
        '    </ul>\n'
        '  </section>\n\n'
        + last_section
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


def build():
    template = read(BASE / 'template.html')
    css = read(BASE / 'style.css')
    js = read(BASE / 'script.js')

    meta_md    = read(CONTENT / 'meta.md')
    footer_md  = read(CONTENT / 'footer.md')
    hero_md    = read(CONTENT / 'hero.md')

    work_intro_md   = read(CONTENT / 'work' / 'intro.md')
    about_md            = read(CONTENT / 'work' / 'about.md')
    toolkit_md          = read(CONTENT / 'work' / 'toolkit.md')
    projects_heading_md = read(CONTENT / 'work' / 'projects.md')
    articles_md         = read(CONTENT / 'work' / 'articles.md')

    play_intro_md   = read(CONTENT / 'play' / 'intro.md')
    lately_md       = read(CONTENT / 'play' / 'lately.md')
    playground_md   = read(CONTENT / 'play' / 'playground.md')
    ideas_md        = read(CONTENT / 'play' / 'ideas.md')
    interests_md    = read(CONTENT / 'play' / 'interests.md')

    labels = parse_labels(read(CONTENT / 'labels.md'))

    # Shared pieces
    meta_html = render_meta(meta_md)
    footer_html = render_footer(footer_md)

    # Download subsetted icon font
    fetch_icon_font()

    # Project files (shared by grid cards and detail pages)
    project_detail_files = sorted((CONTENT / 'work' / 'projects').glob('*.md'))
    project_mds = [read(f) for f in project_detail_files]

    # Page bodies
    home_body = render_hero(hero_md)
    work_body = render_work_body(work_intro_md, about_md, toolkit_md, projects_heading_md, project_mds, articles_md, labels)
    play_body = render_play_body(play_intro_md, lately_md, playground_md, interests_md, ideas_md)

    # Project detail pages
    project_pages = [
        (f'work/{f.stem}/index.html', render_project_page(md, labels), 'work', 2)
        for f, md in zip(project_detail_files, project_mds)
    ]

    # Copy pre-generated monthly OG image
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

    # Build pages
    pages = [
        ('index.html', home_body, 'home', 0),
        ('work/index.html', work_body, 'work', 1),
        ('play/index.html', play_body, 'play', 1),
        *project_pages,
    ]

    DIST.mkdir(exist_ok=True)

    for path, body, active, depth in pages:
        html = render_page(template, css, js, meta_html, footer_html, body, active, depth, labels=labels)
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

    # Copy CNAME for GitHub Pages
    cname = BASE / 'CNAME'
    if cname.exists():
        shutil.copy2(cname, DIST / 'CNAME')

    print(f'Done — og accent: {accent}')


MONTH_NAMES = [
    'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
]


def generate_monthly_assets():
    """Generate all 12 monthly OG images into assets/monthly/."""
    hero_md = (CONTENT / 'hero.md').read_text()
    out_dir = BASE / 'assets' / 'monthly'
    out_dir.mkdir(parents=True, exist_ok=True)
    for i, (accent, name) in enumerate(zip(SEASON_COLORS, MONTH_NAMES), start=1):
        og_path = out_dir / f'og-{i:02d}.png'
        generate_og_image(accent, hero_md, og_path)
        print(f'Generated {name} ({accent}): {og_path.name}')
    print('Done — all 12 monthly OG images generated.')


if __name__ == '__main__':
    if '--gen-monthly' in sys.argv:
        generate_monthly_assets()
    else:
        build()
