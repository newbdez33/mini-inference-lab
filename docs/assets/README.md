# Site assets

- `mini-head.png`: approved Mini website avatar, derived from the character artwork. Production source images stay outside this repository.
- `fonts/noto-sans-sc-lab.woff2`: local Noto Sans SC variable font for display headings. The subset covers the catalog and first lesson titles. Its source and hash are in `fonts/source.json`; the SIL Open Font License is in `fonts/OFL.txt`.
- Body text uses native system fonts. On macOS, this is PingFang SC for Chinese and San Francisco for Latin text. Headings use the local font; code uses the system monospace font.
- `site.css`: shared theme tokens, catalog layout, and tutorial layout. Command blocks use a dark terminal surface in both themes.
- `theme.js`: sets the initial theme before paint and stores the visitor's choice across pages. Dark mode is the default.
- `site.js`: platform and device selection, tutorial copy controls, and current-section navigation. The top controls filter tutorial content marked with `data-platforms` and `data-devices`, including command blocks and installation help. Both choices persist in local storage. macOS uses CPU and hides the device control, while the saved Windows/Linux device choice remains available. Command blocks show a shell label and a copy button. Display-only shell prompts do not enter the clipboard.

In a lesson, group platform commands in a `div.platform-commands` with `markdown="1"`. Each child `div` must have `markdown="1"`, a `data-platforms` list (`macos`, `windows`, or `linux`), a leading platform label, and one fenced code block. Add `data-devices="cpu"` or `data-devices="cuda"` when commands differ by device; omit it for shared commands. Each group must provide exactly one matching panel for macOS/CPU, Windows/CPU, Windows/CUDA, Linux/CPU, and Linux/CUDA. Optional text after the command provides platform-specific guidance. Without JavaScript, all labeled variants remain readable.

For platform-specific or device-specific prose, use a `div` with the matching data attributes and `markdown="1"` without the command wrapper. When both attributes are present, both must match. Keep shared guidance outside these panels.

Keep body text at 16 pixels and supporting text at 13–14 pixels on all screen sizes. Check heading glyph coverage before adding a new lesson title. No external font request is made by the site.
