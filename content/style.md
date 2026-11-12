# the **style**,<br>tokens and components this site is built from.

## about this page

These are the design tokens and components this site is built from. Every value below is read from `style.css` and `build.py` when the site is built, so this page can't drift from the real thing.

Everything is live: hover the components, switch to dark mode, or pick a season to recolour the page. For how to write each content element, see the [reference](/reference/) page.

## fonts

One typeface for everything, loaded from Google Fonts in three weights. Code uses the system monospace.

<!-- fonts | the quick brown fox jumps over the lazy dog, 0123456789 -->
- font-sans: text, headings and interface. 400 by default, 500 for headings, 700 for names and labels.
- font-mono: code on the reference page.

## type scale

Six sizes on a minor-third scale. The four larger sizes are fluid: they grow with the screen between their mobile and desktop values.

<!-- type | the quick brown fox -->
- text-display: hero heading
- text-heading: page intros, section titles, case study heading
- text-subhead: hero tagline
- text-body: body text, card titles, toolkit and interests
- text-small: meta, footer, lately, rolodex, captions
- text-ui: nav, buttons, tags, section labels

## letter-spacing

Small text gets a little extra room. Line height is 1 for display, 1.05 for section titles, 1.4 for small text and 1.5 for everything else.

<!-- tracking | the quick brown fox jumps over the lazy dog -->
- ls-ui: interface text at `--text-ui`: nav, buttons, tags
- ls-label: small text at `--text-small`: meta, footer, captions

## colour

Two colours and an accent. `--black` and `--white` swap in dark mode, which is why nothing uses a raw colour.

<!-- colour -->
- black: text and borders
- white: background
- accent: links, accent words and hover fills. Set each month from the seasons below.
- on-accent: text and icons on an accent fill

## seasons

The accent follows Bengaluru's seasonal blooms, one per month. Every light accent passes 4.5:1 against white and every dark accent 4.5:1 against black. Pick one to recolour the page.

<!-- seasons -->

## spacing

<!-- space -->
- space-xs: tight gaps, list rows, scrollbar
- inner-gap: gaps inside cards and list items
- tag-gap: between tags
- space-sm: between boxes, also `--box-gap`
- btn-pad-x: side padding in text buttons
- bar-pad: above and below the top bar and nav
- bar-h: height of every bar and button
- space-md: title to content, inner gaps
- padding: page margin
- space-lg: between sections
- tag-pad: inside tags
- box-pad: inside bordered boxes

## icons

Material Symbols Sharp, cut down at build time to just the icons below. Its optical size always matches the size it's drawn at.

<!-- icon-sizes | mail -->
- icon-sz: inline icons
- icon-sz-lg: icons in buttons
- icon-sz-xl: every other icon
- nav-logo-sz: the season picker square

<!-- icons -->

## layout

- Above 1024px, project and article grids have three columns.
- Up to 1024px, they have two.
- Up to 768px, everything is one column.

The top bar and nav are fixed, and the content scrolls inside a bordered box between them.

## components

Everything you can click is a bordered box. On hover it fills with the accent, its text turns `--on-accent`, and its border takes the accent too. On touch screens the same fill shows while pressed.

<!-- components -->
- bar-box: the one interactive element, for icon and text buttons
- nav-link-box: the bottom nav; the current page is filled
- toast: confirms an action, like copying the email
- tag: the small tag, for inside project and article cards
- tag-lg: the large tag, a standalone box for toolkit, interests and case study headers
- name: accent words in headings and taglines
- project: a project card, linking to its case study
- article: a published piece, linking out
- lately-item: one thing from the lately list
- rolodex-item: one random link from a category
- playground-card: an outside project, with a preview
- footer: the first row is live info, values in accent and not clickable; the second row is buttons, the whole box is the link
