"""Build the public tutorial and its reproducible experiment package."""

from __future__ import annotations

import hashlib
import html
import json
import shutil
import zipfile
from pathlib import Path

import markdown


ROOT = Path(__file__).resolve().parents[1]
EPISODE = ROOT / "episode-01"
SITE = ROOT / "docs"
PACKAGE_FILES = ("README.md", "example_infer.py", "requirements.txt", "terminal-recordings.json")
DOWNLOAD_URL = "https://github.com/newbdez33/mini-inference-lab/raw/refs/heads/main/packages/mini-lab-01.zip"


def build_package() -> Path:
    output = ROOT / "packages" / "mini-lab-01.zip"
    output.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in PACKAGE_FILES:
            entry = zipfile.ZipInfo(f"mini-lab-01/{name}", date_time=(2026, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, (EPISODE / name).read_bytes())
    return output


def main() -> None:
    source = (EPISODE / "README.md").read_text(encoding="utf-8")
    title, _, source = source.partition("\n")
    records = json.loads((EPISODE / "terminal-recordings.json").read_text())
    for run in records["runs"]:
        if run["input"] not in source:
            raise ValueError(f"Tutorial input differs from the captured run: {run['id']}")
        if run["answer"] not in source:
            raise ValueError(f"Tutorial output differs from the captured run: {run['id']}")
    converter = markdown.Markdown(extensions=["fenced_code", "tables", "toc", "attr_list", "md_in_html"])
    content = converter.convert(source.replace(DOWNLOAD_URL, "../downloads/mini-lab-01.zip"))
    template = (ROOT / "scripts" / "lesson.html").read_text(encoding="utf-8")
    lesson_title = html.escape(title.removeprefix("# "))
    style_version = hashlib.sha256((SITE / "assets" / "site.css").read_bytes()).hexdigest()[:12]
    page = template.replace("{{TITLE}}", lesson_title)
    page = page.replace("{{FIRST_PROMPT}}", html.escape(records["runs"][0]["input"]))
    page = page.replace("{{FIRST_ANSWER}}", html.escape(records["runs"][0]["answer"]))
    page = page.replace("{{STYLE_VERSION}}", style_version)
    page = page.replace("{{TOC}}", converter.toc).replace("{{CONTENT}}", content)
    SITE.mkdir(exist_ok=True)
    lesson = SITE / "ep1"
    lesson.mkdir(exist_ok=True)
    (lesson / "index.html").write_text(page, encoding="utf-8")
    catalog = (ROOT / "scripts" / "catalog.html").read_text(encoding="utf-8")
    catalog = catalog.replace("{{STYLE_VERSION}}", style_version)
    (SITE / "index.html").write_text(catalog.replace("{{EP1_TITLE}}", lesson_title), encoding="utf-8")
    (SITE / ".nojekyll").touch()
    package = build_package()
    downloads = SITE / "downloads"
    downloads.mkdir(exist_ok=True)
    shutil.copy2(package, downloads / package.name)
    for name in PACKAGE_FILES:
        shutil.copy2(EPISODE / name, downloads / name)
    digest = hashlib.sha256(package.read_bytes()).hexdigest()
    (downloads / "SHA256SUMS").write_text(f"{digest}  {package.name}\n")
    print(f"Built the catalog, ep1 tutorial, and {package.name} ({package.stat().st_size} bytes).")


if __name__ == "__main__":
    main()
