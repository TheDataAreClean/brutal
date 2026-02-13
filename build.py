#!/usr/bin/env python3
"""Build script for portfolio site.

Reads markdown content files, renders them into HTML,
and assembles the final dist/index.html.

Usage: python3 build.py
"""

import re
from pathlib import Path

BASE = Path(__file__).parent
CONTENT = BASE / 'content'
DIST = BASE / 'dist'


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
    handle = items.get('handle', '')
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
        f'      <span>{credit}</span>\n'
        f'      <span>{license_text} \u00b7 {handle} \u00b7 {year}</span>\n'
        '    </div>'
    )


def build():
    template = read(BASE / 'template.html')
    css = read(BASE / 'style.css')
    js = read(BASE / 'script.js')

    hero_md = read(CONTENT / 'hero.md')
    about_md = read(CONTENT / 'about.md')
    projects_md = read(CONTENT / 'projects.md')
    lately_md = read(CONTENT / 'lately.md')
    footer_md = read(CONTENT / 'footer.md')

    # Render content sections
    hero_html = render_hero(hero_md)
    about_html = render_about(about_md)
    projects_html = render_projects(projects_md)
    footer_html = render_footer(footer_md, lately_md)

    # Assemble page
    html = template
    html = html.replace('{{hero}}', hero_html)
    html = html.replace('{{about}}', about_html)
    html = html.replace('{{projects}}', projects_html)
    html = html.replace('{{footer}}', footer_html)

    # Inline CSS
    html = html.replace(
        '  <link rel="stylesheet" href="style.css">',
        '  <style>\n' + css + '  </style>',
    )

    # Inline JS
    html = html.replace(
        '  <script src="script.js"></script>',
        '  <script>\n' + js + '  </script>',
    )

    # Write output
    DIST.mkdir(exist_ok=True)
    (DIST / 'index.html').write_text(html)
    print(f'Built dist/index.html ({len(html)} bytes)')


if __name__ == '__main__':
    build()
