# Repository scope

This public repository is for viewers. Keep tutorials, runnable experiments, public example output, and downloadable experiment packages here.

- Keep all video scripts, storyboards, character references, narration, renders, and production review notes in the private `newbdez33/mini-inference-studio` repository.
- Do not publish Tailscale addresses or local production paths here.
- `episode-01/README.md` is the canonical first lesson. The root URL is the course catalog; lessons use numeric routes such as `/1/`. Build `docs/index.html`, `docs/1/index.html`, the legacy `/ep1/` redirect, and ZIP downloads with `scripts/build_site.py`; do not edit generated files directly.
- Keep experiment ZIP files limited to runnable code and required dependencies or configuration. Keep Markdown tutorials and reference run records outside the ZIP files.
- Use `python` in all Python command examples. Keep venv setup optional and collapsed by default, with creation, activation, and interpreter checks matched to the global platform selection. Do not require a virtual environment in pip commands.
- Keep the approved graphite, mint, and pink theme, Mini head icon, and native body fonts consistent between the catalog and lessons. Body text is 16 pixels; supporting text is 13–14 pixels on desktop and mobile.
- Show an estimated duration in minutes on every experiment card, lesson introduction, and downloadable README. Include reading and hands-on work; state first-time installation and download waits separately.
- Run checks locally. Use GitHub Pages only for the requested static publication; do not add general CI workflows.
- The user will test the tutorial before video production resumes.
