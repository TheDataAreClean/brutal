# brutal

Personal portfolio site for [Arpit](https://thedataareclean.com) — a brutalist, multi-page design built with a markdown-driven Python build system. No frameworks, no dependencies beyond Pillow.

**Live:** https://thedataareclean.com

## Quickstart

```bash
# First time
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# Build
python3 build.py

# Preview
cd dist && python3 -m http.server 9001
# open http://localhost:9001
```

## Docs

| File | What's in it |
|---|---|
| [APP.md](APP.md) | Architecture, design system, content formats, deploy |
| [COMMANDS.md](COMMANDS.md) | Copy-paste commands for every common task |
| [CLAUDE.md](CLAUDE.md) | Rules and constraints for AI-assisted editing |
| [CHANGELOG.md](CHANGELOG.md) | Version history |
| [FUTURE.md](FUTURE.md) | Backlog and ideas |
