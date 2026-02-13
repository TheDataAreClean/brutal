#!/usr/bin/env python3
# Requires: pip install Pillow (for OG image + favicon generation)
"""Build script for portfolio site.

Reads markdown content files, renders them into HTML,
and assembles the final dist/index.html.

Usage: python3 build.py
"""

import re
import shutil
from datetime import datetime
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


FONT_PATH = BASE / 'assets' / 'fonts' / 'Inter.ttf'


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
    """Generate OG image with Inter font, matching hero section design."""
    from PIL import Image, ImageDraw, ImageFont

    width, height = 1200, 630
    padding = 80

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

    img = Image.new('RGB', (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Load Inter at two sizes
    font_lg = ImageFont.truetype(str(FONT_PATH), 72)
    font_sm = ImageFont.truetype(str(FONT_PATH), 28)

    # Strip ** for measurement
    heading_plain = heading_raw.replace('**', '')
    tagline_plain = tagline_raw.replace('**', '')

    # Position: bottom-left aligned, like the hero section
    h_bbox = draw.textbbox((0, 0), heading_plain, font=font_lg)
    h_h = h_bbox[3] - h_bbox[1]
    t_bbox = draw.textbbox((0, 0), tagline_plain, font=font_sm)
    t_h = t_bbox[3] - t_bbox[1]

    total_h = h_h + 24 + t_h
    y_start = height - padding - total_h

    # Draw heading and tagline with accent on **bold** segments
    heading_segments = parse_bold_segments(heading_raw)
    tagline_segments = parse_bold_segments(tagline_raw)

    draw_segments(draw, padding, y_start, heading_segments, font_lg, black, accent)
    draw_segments(draw, padding, y_start + h_h + 24, tagline_segments, font_sm, black, accent)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path)


def generate_favicon(accent_hex, output_path):
    """Generate a solid accent color favicon."""
    from PIL import Image
    accent = tuple(int(accent_hex[i:i+2], 16) for i in (1, 3, 5))
    img = Image.new('RGB', (64, 64), accent)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path)


def read(path):
    return Path(path).read_text()


def parse_inline(text):
    """Convert [text](url) to <a> tags."""
    return re.sub(
        r'\[(.+?)\]\((.+?)\)',
        r'<a href="\2" target="_blank" rel="noopener">\1</a>',
        text,
    )


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
    twitter = items.get('twitter', '')
    lang = items.get('lang', 'en')

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
        + (f'\n  <meta name="twitter:site" content="@{twitter}">' if twitter else '')
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

    # **text** → <span class="name">text</span>
    heading = re.sub(r'\*\*(.+?)\*\*', r'<span class="name">\1</span>', heading)
    tagline = re.sub(r'\*\*(.+?)\*\*', r'<span class="name">\1</span>', tagline)

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

    highlighted = [
        re.sub(r'\*\*(.+?)\*\*', r'<span class="highlight">\1</span>', p)
        for p in paragraphs
    ]
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


def render_projects(md):
    lines = md.strip().split('\n')
    title = ''
    projects = []
    current_project = None

    for line in lines:
        stripped = line.strip()
        if stripped.startswith('# '):
            title = stripped[2:]
        elif stripped.startswith('## '):
            if current_project:
                projects.append(current_project)
            current_project = {'name': stripped[3:], 'role': '', 'url': '', 'desc': ''}
        elif stripped.startswith('- ') and current_project:
            key, _, value = stripped[2:].partition(':')
            key = key.strip()
            value = value.strip()
            if key in ('role', 'url', 'desc'):
                current_project[key] = value

    if current_project:
        projects.append(current_project)

    # **text** → <span class="highlight">text</span>
    title = re.sub(r'\*\*(.+?)\*\*', r'<span class="highlight">\1</span>', title)

    proj_parts = []
    for p in projects:
        desc = parse_inline(p['desc'])
        proj_parts.append(
            '      <div class="project">\n'
            f'        <a class="project-header" href="{p["url"]}" target="_blank" rel="noopener">\n'
            f'          <span class="project-name">{p["name"]}</span>\n'
            '          <span class="project-arrow"><span class="material-symbols-sharp">arrow_outward</span></span>\n'
            '        </a>\n'
            f'        <span class="project-role">{p["role"]}</span>\n'
            f'        <span class="project-desc">{desc}</span>\n'
            '      </div>'
        )

    projects_inner = '\n'.join(proj_parts)

    return (
        '  <!-- PROJECTS -->\n'
        '  <section class="projects-section">\n'
        '    <h2 class="projects-title">\n'
        f'      {title}\n'
        '    </h2>\n'
        '    <div class="projects">\n'
        f'{projects_inner}\n'
        '    </div>\n'
        '  </section>'
    )


def render_lately(md):
    items = dict(parse_kv_list(md))
    icon_map = {
        'read': 'menu_book',
        'listened': 'headphones',
        'watched': 'movie',
    }

    parts = []
    for key in ('read', 'listened', 'watched'):
        value = items.get(key, '\u2014')
        icon = icon_map[key]
        parts.append(
            '      <div class="footer-lately-item">\n'
            f'        <span class="material-symbols-sharp">{icon}</span>\n'
            f'        <span class="footer-lately-value">{value}</span>\n'
            '      </div>'
        )

    return (
        '    <div class="footer-lately">\n'
        + '\n'.join(parts) + '\n'
        + '    </div>'
    )


def render_footer(footer_md, lately_md):
    items = dict(parse_kv_list(footer_md))
    email = items.get('email', '')
    location = items.get('location', '')
    credit = parse_inline(items.get('credit', ''))
    license_text = parse_inline(items.get('license', ''))
    handle = parse_inline(items.get('handle', ''))
    year = items.get('year', '')

    lately = render_lately(lately_md)

    return (
        '    <div class="footer-email">\n'
        f'      <span>{email}</span>\n'
        '      <button class="footer-email-copy" onclick="copyEmail()" aria-label="Copy email">\n'
        '        <span class="material-symbols-sharp">content_copy</span>\n'
        '      </button>\n'
        '    </div>\n'
        '\n'
        f'{lately}\n'
        '\n'
        '    <div class="footer-meta">\n'
        f'      <span>{location}</span>\n'
        '\n'
        '      <span id="local-time">--:--</span>\n'
        '\n'
        '      <span id="temperature">--</span>\n'
        '\n'
        '      <span>AQI <span id="aqi">--</span></span>\n'
        '    </div>\n'
        '\n'
        '    <div class="footer-bottom">\n'
        f'      <span>{license_text} \u00b7 {handle} \u00b7 {year}</span>\n'
        f'      <span>{credit}</span>\n'
        '    </div>'
    )


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

    meta_md = read(CONTENT / 'meta.md')
    hero_md = read(CONTENT / 'hero.md')
    about_md = read(CONTENT / 'about.md')
    projects_md = read(CONTENT / 'projects.md')
    lately_md = read(CONTENT / 'lately.md')
    footer_md = read(CONTENT / 'footer.md')

    # Render content sections
    meta_html = render_meta(meta_md)
    hero_html = render_hero(hero_md)
    about_html = render_about(about_md)
    projects_html = render_projects(projects_md)
    footer_html = render_footer(footer_md, lately_md)

    # Assemble page
    html = template
    html = html.replace('{{meta}}', meta_html)
    html = html.replace('{{hero}}', hero_html)
    html = html.replace('{{about}}', about_html)
    html = html.replace('{{projects}}', projects_html)
    html = html.replace('{{footer}}', footer_html)

    # Inline minified CSS
    html = html.replace(
        '  <link rel="stylesheet" href="style.css">',
        '  <style>\n' + minify_css(css) + '  </style>',
    )

    # Inline minified JS
    html = html.replace(
        '  <script src="script.js"></script>',
        '  <script>\n' + minify_js(js) + '  </script>',
    )

    # Generate seasonal images
    month = datetime.now().month - 1  # 0-indexed
    accent = SEASON_COLORS[month]
    try:
        generate_og_image(accent, hero_md, BASE / 'assets' / 'og-image.png')
        generate_favicon(accent, BASE / 'assets' / 'favicon.png')
    except Exception as e:
        print(f'Warning: image generation failed ({e}), skipping.')

    # Write output
    DIST.mkdir(exist_ok=True)
    (DIST / 'index.html').write_text(html)

    # Copy assets
    assets_src = BASE / 'assets'
    if assets_src.is_dir():
        assets_dst = DIST / 'assets'
        if assets_dst.exists():
            shutil.rmtree(assets_dst)
        shutil.copytree(assets_src, assets_dst, ignore=shutil.ignore_patterns('README.md'))

    print(f'Built dist/index.html ({len(html)} bytes) — og accent: {accent}')


if __name__ == '__main__':
    build()
