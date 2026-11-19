"""Steps of build.sh that are easier in Python.

    python3 browser-demo/pack.py backend OUT/py/fitfinder.json     backend code + catalog as {path: text}
    python3 browser-demo/pack.py fonts OUT                          use Google Fonts, drop bundled font files
    python3 browser-demo/pack.py page OUT/index.html                add fonts link and bootstrap.js to <head>
"""

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n    '
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,100..900&display=swap">')


def backend(out: str) -> None:
    # Product photos live on the brands' sites and can't load in a sandboxed page, so image links
    # are dropped; the app shows its garment illustration instead.
    files = {str(p): p.read_text() for p in sorted(Path("backend/app").rglob("*.py"))}
    catalog = json.loads(Path("backend/data/real_catalog.json").read_text())
    for p in catalog["products"]:
        p["image_url"] = None
    files["backend/data/real_catalog.json"] = json.dumps(catalog, separators=(",", ":"), ensure_ascii=False)
    Path(out).write_text(json.dumps(files, ensure_ascii=False))


def fonts(out: str) -> None:
    for f in Path(out, "assets").glob("*.woff2"):
        f.unlink()
    for f in Path(out, "assets").glob("*.css"):
        css = re.sub(r"@font-face\{[^}]*archivo[^}]*\}", "", f.read_text(), flags=re.I)
        f.write_text(css.replace("Archivo Variable", "Archivo"))


def page(index: str) -> None:
    boot = (HERE / "bootstrap.js").read_text()
    html = Path(index).read_text().replace('href="/favicon.svg"', 'href="./favicon.svg"')
    html = html.replace("<head>", f"<head>\n    {FONTS}\n    <script>\n{boot}\n    </script>", 1)
    Path(index).write_text(html)


if __name__ == "__main__":
    {"backend": backend, "fonts": fonts, "page": page}[sys.argv[1]](sys.argv[2])
