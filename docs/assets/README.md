# Site assets

- `mini-head.png`: approved Mini website avatar, derived from the character artwork. Production source images stay outside this repository.
- `fonts/noto-sans-sc-lab.woff2`: local Noto Sans SC variable font for display headings. The subset covers the catalog and first lesson titles. Its source and hash are in `fonts/source.json`; the SIL Open Font License is in `fonts/OFL.txt`.
- Body text uses native system fonts. On macOS, this is PingFang SC for Chinese and San Francisco for Latin text. Headings use the local font; code uses the system monospace font.
- `site.css`: shared theme tokens, catalog layout, and tutorial layout.
- `theme.js`: sets the initial theme before paint and stores the visitor's choice across pages. Dark mode is the default.
- `site.js`: platform selection, tutorial copy controls, and current-section navigation. Platform choices stay in sync across the top switcher and command tabs and persist in local storage.

In a lesson, group platform commands in a `div.platform-commands` with `markdown="1"`. Each child `div` must have `markdown="1"`, a `data-platforms` list (`macos`, `windows`, or `linux`), a leading platform label, and one fenced code block. A panel can serve multiple platforms. Each group must cover all three platforms exactly once. Optional text after the command provides platform-specific guidance. Without JavaScript, all labeled variants remain readable.

Keep body text at 16 pixels and supporting text at 13–14 pixels on all screen sizes. Check heading glyph coverage before adding a new lesson title. No external font request is made by the site.
