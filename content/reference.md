# the **reference**,<br>every element this site can render.

## about this page

This page shows every element the site can render, and how to write each one. It is both a reference and a test: everything below is drawn by the same code that builds the case studies, so if something looks wrong here, it looks wrong there too.

All copy lives in `content/*.md` files. There is no markdown library: each part of the site reads its own small format, listed below. Edits show up after `python3 build.py`.

For fonts, colours, spacing and components, see the [style](/style/) page.

## inline text

Text can be **bold** or *italic*. Links look like [this](https://example.com/) and open in a new tab, while links to a page on this site, like the [style](/style/) page, open in the same one. File names and keys are written as `inline code`.

```
Text can be **bold** or *italic*.
Links look like [this](https://example.com/).
Links to a page on this site, like the [style](/style/) page, open in the same tab.
File names and keys are written as `inline code`.
```

Bold, italic and links work in case study paragraphs and lists, team lists and the footer. Everywhere else, text is shown as written.

## accent words

In headings and taglines, `**bold**` turns a word the accent colour instead of making it bold, like the heading at the top of this page. A `<br>` forces a line break.

```
# hello, i am **sam** !
a first line,<br>then a second with an **accent** word.
# **section** title
```

This works in the hero, the page intros, every section title and the `heading` lines in `meta.md`, which are also drawn on the share images.

## headings

Each `##` heading starts a section, shown as a small accent label like the ones on this page. A `###` heading is a sub-heading inside it.

### this is a sub-heading

The smallest heading level in a file becomes the section level, and one level deeper becomes a sub-heading. A section with nothing in it is skipped.

```
## approach

### first step
```

## paragraphs

Every line is its own paragraph.

Blank lines between them are optional and ignored, so a paragraph can't wrap across lines in the file.

```
Every line is its own paragraph.

Blank lines between them are optional and ignored.
```

## lists

- Bullets start with a dash and a space.
- Numbered items render the same way, so order is shown by position, not numbers.
- A list can sit between paragraphs, and a section with nothing but a list (like **team**) renders as one list.

```
- Bullets start with a dash and a space.
1. Numbered items render the same way.
```

## images

An image sits on its own line. The text in the brackets is its caption and alt text; leave it empty for no caption.

![A caption sits under the image.](/assets/samples/placeholder.svg)

```
![A caption sits under the image.](/assets/projects/sample.webp)
```

Two images in a row stack flush, with no gap between them. Images live in `assets/` and must be WebP: run `python3 build.py --optimize-images` after adding a PNG or JPG. The build warns about any case study image it can't find.

## code

Code blocks are wrapped in a line of three backticks above and below. They keep their spacing and scroll sideways instead of wrapping.

```
python3 build.py
python3 build.py --optimize-images
python3 build.py --gen-monthly
```

## comments

Anything between `<!--` and `-->` is hidden. Case studies use comments to label their parts, and the rolodex uses them to name categories.

```
<!-- CARD -->
```

## case studies

Each project is one file in `content/work/projects/`. The lines before the first `##` heading fill the project card and the top of its page; everything after is the case study, written with the elements above.

```
<!-- CARD -->
- problem: How might a small library understand what its readers need?
- org: Sample Studio
- year: 2024–2025
- tags: research, design, data

<!-- IDENTITY -->
- url: https://example.com/
- slug: sample-studio
- added: Jan 2025

<!-- CASE STUDY -->
## overview
Sample Studio helps small libraries plan their collections.

## team
- [Sam Example](https://example.com/), Lead Researcher
- Alex Sample, Designer
```

- **problem** is the heading on the card, the page and the share image.
- **org** and **year** sit under it. A project with no org is skipped.
- **slug** is the page address, `/work/<slug>/`. Without one, it's made from the org.
- **added** dates the project in the RSS feed.
- Card order is set in `content/work/project-order.md`, one slug per line. Projects not listed go last.

## articles

Published writing lives in `content/work/articles.md`, newest first. The first six show, and a button reveals the rest.

```
## A field guide to reading charts
- publisher: The Sample Review
- date: Jan 2025
- tags: data viz, essay
- url: https://example.com/
```

## playground

Each playground card is one line in `content/play/playground.md`: a link, an image from `assets/playground/`, a one-line description, and an optional year, split by `|`.

```
[sample project](https://example.com/) | sample.webp | a one-line description of the project. | 2025
```

## lately

`content/play/lately.md` holds one line per activity. A link makes the row clickable, plain text shows it unlinked, and an empty value hides the row.

```
- read: [A Book About Maps](https://example.com/)
- listened: A Sample Podcast
- watched:
```

The keys are read, listened, watched, cooked, explored, played, built, learned, ran, cycled, photographed, brewed, visited and wrote. Each one's icon is fixed, and the verb shown beside it is set in `labels.md`. Changed rows are logged to `lately-archive.md` on every commit, which feeds the RSS feed.

## rolodex

`content/play/ideas.md` groups links into categories. A comment names each category and its icon, and one random link per category shows on each visit.

```
<!-- data & visualisation | bar_chart -->
- [A Sample Blog](https://example.com/)
- [Another Sample Site](https://example.org/)
```

The icon must be one of the icons on the [style](/style/) page. A new one has to be added to `ICON_NAMES` in `build.py` first.

## tags

The toolkit (`content/work/toolkit.md`) and interests (`content/play/interests.md`) are plain lists, one tag per line. In interests, a line between the heading and the list becomes a subtitle.

```
# **section** title
an optional subtitle line.

- first tag
- second tag
```

## site text

- `content/hero.md` is the home page heading and tagline.
- `content/work/intro.md` and `content/play/intro.md` are the opening lines of work and play.
- `content/meta.md` sets each page's title, description and share image text.
- `content/footer.md` is the footer.
- `content/labels.md` holds every button, label and screen reader text. Its keys are fixed; only the values change.

## this page and style

This page is `content/reference.md`, written with the elements above. The [style](/style/) page is `content/style.md`, where a comment like `<!-- type | sample text -->` inserts a generated block, such as the type scale, with the lines below it as notes. Its values are read from `style.css` and `build.py` at build time, and its component demos use the generic content in `content/samples.md`.
