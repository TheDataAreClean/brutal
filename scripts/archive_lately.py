#!/usr/bin/env python3
"""Pre-commit hook: log new/changed lately.md items to lately-archive.md with today's date."""

import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LATELY = ROOT / 'content/play/lately.md'
ARCHIVE = ROOT / 'content/play/lately-archive.md'
TODAY = date.today().isoformat()
REL_LATELY = 'content/play/lately.md'


def parse_items(text):
    items = {}
    for line in text.strip().split('\n'):
        s = line.strip()
        if s.startswith('- '):
            key, _, val = s[2:].partition(':')
            val = val.strip()
            if val:
                items[key.strip()] = val
    return items


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT)] + list(args),
                                   stderr=subprocess.DEVNULL).decode()


def is_staged():
    result = subprocess.run(['git', '-C', str(ROOT), 'diff', '--cached', '--name-only'],
                            capture_output=True, text=True)
    return REL_LATELY in result.stdout.split('\n')


def main():
    if not is_staged():
        return 0

    try:
        staged = parse_items(git('show', f':{REL_LATELY}'))
    except subprocess.CalledProcessError:
        return 0

    try:
        head = parse_items(git('show', f'HEAD:{REL_LATELY}'))
    except subprocess.CalledProcessError:
        head = {}

    changed = {k: v for k, v in staged.items() if head.get(k) != v}
    if not changed:
        return 0

    archive_text = ARCHIVE.read_text() if ARCHIVE.exists() else ''
    new_lines = [f'- {k}: {v}' for k, v in changed.items()]
    header = f'## {TODAY}'

    if header in archive_text:
        lines = archive_text.split('\n')
        result = []
        i = 0
        while i < len(lines):
            if lines[i].strip() == header:
                # Collect the whole section
                result.append(lines[i])
                i += 1
                while i < len(lines) and not lines[i].startswith('## '):
                    if lines[i].strip():
                        result.append(lines[i])
                    i += 1
                result.extend(new_lines)
                result.append('')
            else:
                result.append(lines[i])
                i += 1
        archive_text = '\n'.join(result)
    else:
        new_section = header + '\n' + '\n'.join(new_lines) + '\n'
        archive_text = new_section + '\n' + archive_text if archive_text else new_section

    ARCHIVE.write_text(archive_text)
    subprocess.run(['git', '-C', str(ROOT), 'add', str(ARCHIVE)])
    print(f'[archive_lately] logged {len(changed)} item(s) → lately-archive.md ({TODAY})')
    return 0


if __name__ == '__main__':
    sys.exit(main())
