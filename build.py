#!/usr/bin/env python3
# Requires: pip install Pillow (for OG image + favicon generation)
"""Build script for portfolio site.

Reads markdown content files, renders them into HTML,
and assembles multi-page output: /, /work/, /play/.

Usage: python3 build.py
"""

import json
import re
import shutil
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
    bar_gap = 8       # gap between bar and box

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

    # Draw top bar: accent cube + thin line
    cube_size = bar_h
    draw.rectangle([margin, margin, margin + cube_size, margin + bar_h], fill=accent)

    # Draw content viewport box
    box_top = margin + bar_h + bar_gap
    box_bottom = height - margin
    draw.rectangle([margin, box_top, width - margin, box_bottom], outline=black, width=1)

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
        '    <h2 class="section-title">\n'
        f'      {title}\n'
        '    </h2>\n'
        '    <div class="projects">\n'
        f'{projects_inner}\n'
        '    </div>\n'
        '  </section>'
    )


def render_lately(md):
    items = dict(parse_kv_list(md))
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
        if not raw or raw == '\u2014':
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
        '    <div class="lately-list">\n'
        + '\n'.join(parts) + '\n'
        + '    </div>'
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


def render_work_section(md):
    """Parse work.md into skills grid + services grid HTML."""
    lines = md.strip().split('\n')
    current_section = None
    skills = []
    services = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith('# '):
            current_section = stripped[2:].strip().lower()
        elif stripped.startswith('- ') and current_section:
            value = stripped[2:].strip()
            if current_section == 'skills':
                skills.append(value)
            elif current_section == 'services':
                services.append(value)

    skill_boxes = '\n'.join(
        f'      <div class="skill-box">{s}</div>'
        for s in skills
    )
    service_boxes = '\n'.join(
        f'      <div class="service-box">{s}</div>'
        for s in services
    )

    return (
        '  <!-- SKILLS -->\n'
        '  <section>\n'
        '    <h2 class="section-title"><span class="highlight">skills</span></h2>\n'
        '    <div class="skills-grid">\n'
        f'{skill_boxes}\n'
        '    </div>\n'
        '  </section>\n'
        '\n'
        '  <!-- SERVICES -->\n'
        '  <section>\n'
        '    <h2 class="section-title"><span class="highlight">services</span></h2>\n'
        '    <div class="services-grid">\n'
        f'{service_boxes}\n'
        '    </div>\n'
        '  </section>'
    )


def fetch_glass_photos():
    """Fetch photos from Glass.photo profile, return list of {url, description}."""
    try:
        url = 'https://glass.photo/thedataareclean'
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (compatible; portfolio-build/1.0)',
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode('utf-8')

        # Extract __NEXT_DATA__ JSON
        match = re.search(
            r'<script\s+id="__NEXT_DATA__"\s+type="application/json">\s*({.+?})\s*</script>',
            html,
            re.DOTALL,
        )
        if not match:
            print('Warning: Could not find __NEXT_DATA__ in Glass.photo page.')
            return []

        data = json.loads(match.group(1))

        # Navigate to posts array: props.pageProps.fallbackData.posts.data
        posts = (
            data.get('props', {})
            .get('pageProps', {})
            .get('fallbackData', {})
            .get('posts', {})
            .get('data', [])
        )

        photos = []
        for post in posts:
            img_url = post.get('image1024x1024', '')
            desc = post.get('description', '')
            created = post.get('created_at', '')
            if img_url:
                photos.append({
                    'url': img_url,
                    'description': desc or '',
                    'created': created,
                })

        # Newest first
        photos.sort(key=lambda p: p['created'], reverse=True)

        print(f'Fetched {len(photos)} photos from Glass.photo')
        return photos

    except Exception as e:
        print(f'Warning: Glass.photo fetch failed ({e}), using empty gallery.')
        return []


def render_gallery(photos, num_cols=3):
    """Render masonry gallery with round-robin columns for desktop, order attrs for mobile."""
    if not photos:
        return ''

    # Distribute photos round-robin across columns
    cols = [[] for _ in range(num_cols)]
    for i, photo in enumerate(photos):
        cols[i % num_cols].append((i, photo))

    col_parts = []
    for col in cols:
        items = []
        for idx, photo in col:
            desc = escape(photo['description'])
            caption = f'\n          <figcaption>{desc}</figcaption>' if desc else ''
            items.append(
                f'        <figure class="gallery-item" style="order:{idx}">\n'
                f'          <img src="{photo["url"]}" alt="{desc}" loading="lazy">{caption}\n'
                f'        </figure>'
            )
        col_parts.append(
            '      <div class="gallery-col">\n'
            + '\n'.join(items) + '\n'
            + '      </div>'
        )

    return (
        '  <!-- GALLERY -->\n'
        '  <section>\n'
        '    <h2 class="section-title">some personal <span class="highlight">clicks</span></h2>\n'
        '    <div class="gallery">\n'
        + '\n'.join(col_parts) + '\n'
        + '    </div>\n'
        '  </section>'
    )


def render_home_body(hero_md):
    """Home page body: hero."""
    hero_html = render_hero(hero_md)
    return hero_html


def render_page_intro(text):
    """Render an opening tagline, **bold** becomes accent-colored."""
    styled = re.sub(r'\*\*(.+?)\*\*', r'<span class="name">\1</span>', text)
    return (
        '  <section class="page-intro">\n'
        f'    <p class="tagline">{styled}</p>\n'
        '  </section>'
    )


def render_work_body(work_md, projects_md, about_md):
    """Work page body: intro + about + skills + services + projects."""
    intro_html = render_page_intro('at work,<br>i am a multi-disciplinary **data communicator**.')
    about_html = render_about(about_md)
    work_html = render_work_section(work_md)
    projects_html = render_projects(projects_md)
    return intro_html + '\n\n' + about_html + '\n\n' + work_html + '\n\n' + projects_html


def render_interests(md):
    """Parse interests.md into a tag list."""
    lines = md.strip().split('\n')
    tags = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('- '):
            tags.append(stripped[2:].strip())

    tag_html = '\n'.join(
        f'      <span class="interest-tag">{t}</span>'
        for t in tags
    )

    return (
        '  <!-- INTERESTS -->\n'
        '  <section>\n'
        '    <h2 class="section-title">other <span class="highlight">stuff</span></h2>\n'
        '    <p class="section-subtitle">that i am curious about, in no particular order.</p>\n'
        '    <div class="interests">\n'
        f'{tag_html}\n'
        '    </div>\n'
        '  </section>'
    )


def render_play_body(lately_md, interests_md, photos):
    """Play page body: intro + interests + lately + photo gallery."""
    intro_html = render_page_intro('during **play**,<br>i do **whatever i want**.')
    lately_html = (
        '  <!-- LATELY -->\n'
        '  <section>\n'
        '    <h2 class="section-title"><span class="highlight">lately</span>, i have been..</h2>\n'
        + render_lately(lately_md) + '\n'
        + '  </section>'
    )
    gallery_html = render_gallery(photos)
    interests_html = render_interests(interests_md)
    parts = [intro_html, lately_html, interests_html]
    if gallery_html:
        parts.append(gallery_html)
    return '\n\n'.join(parts)


def render_page(template, css, js, meta_html, footer_html, body_html, active_nav, depth=0):
    """Assemble a full HTML page with shared nav/footer, inlined CSS/JS."""
    # Navigation root path (relative)
    nav_root = '../' * depth if depth > 0 else ''
    # Asset path prefix
    asset_prefix = '../' * depth if depth > 0 else ''

    html = template
    html = html.replace('{{meta}}', meta_html)
    html = html.replace('{{body}}', body_html)
    html = html.replace('{{footer}}', footer_html)

    # Nav active states
    html = html.replace('{{nav_root}}', nav_root)
    html = html.replace('{{nav_work_active}}', 'active' if active_nav == 'work' else '')
    html = html.replace('{{nav_play_active}}', 'active' if active_nav == 'play' else '')

    # Fix asset paths for subpages
    if asset_prefix:
        html = html.replace('href="assets/', f'href="{asset_prefix}assets/')
        html = html.replace('src="assets/', f'src="{asset_prefix}assets/')
        html = html.replace('content="assets/', f'content="{asset_prefix}assets/')

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

    meta_md = read(CONTENT / 'meta.md')
    hero_md = read(CONTENT / 'hero.md')
    about_md = read(CONTENT / 'about.md')
    projects_md = read(CONTENT / 'projects.md')
    lately_md = read(CONTENT / 'lately.md')
    footer_md = read(CONTENT / 'footer.md')
    work_md = read(CONTENT / 'work.md')
    interests_md = read(CONTENT / 'interests.md')

    # Shared pieces
    meta_html = render_meta(meta_md)
    footer_html = render_footer(footer_md)

    # Fetch Glass.photo images
    photos = fetch_glass_photos()

    # Page bodies
    home_body = render_home_body(hero_md)
    work_body = render_work_body(work_md, projects_md, about_md)
    play_body = render_play_body(lately_md, interests_md, photos)

    # Generate seasonal images
    month = datetime.now().month - 1  # 0-indexed
    accent = SEASON_COLORS[month]
    try:
        generate_og_image(accent, hero_md, BASE / 'assets' / 'og-image.png')
        generate_favicon(accent, BASE / 'assets' / 'favicon.png')
    except Exception as e:
        print(f'Warning: image generation failed ({e}), skipping.')

    # Build pages
    pages = [
        ('index.html', home_body, 'home', 0),
        ('work/index.html', work_body, 'work', 1),
        ('play/index.html', play_body, 'play', 1),
    ]

    DIST.mkdir(exist_ok=True)

    for path, body, active, depth in pages:
        html = render_page(template, css, js, meta_html, footer_html, body, active, depth)
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
        shutil.copytree(assets_src, assets_dst, ignore=shutil.ignore_patterns('README.md'))

    # Copy CNAME for GitHub Pages
    cname = BASE / 'CNAME'
    if cname.exists():
        shutil.copy2(cname, DIST / 'CNAME')

    print(f'Done — og accent: {accent}')


if __name__ == '__main__':
    build()
