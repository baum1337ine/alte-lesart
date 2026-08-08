#!/usr/bin/env python3
"""Quality gate for the public Alte Lesart HTML site.

Checks:
- no public HTML links to internal/private material (.md, _internal, manifests/logs)
- local /alte-lesart/*.html links resolve to files
- every public HTML page links to core navigation pages
- pages with Hebrew text include a visible source/status marker
"""
from __future__ import annotations
import re
import sys
from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]
BASE = "/alte-lesart"
CORE = [f"{BASE}/index.html", f"{BASE}/sammlung.html", f"{BASE}/lesepfade.html", f"{BASE}/quellen.html"]
FORBIDDEN = ("_internal", "_topic_manifest", "Batch-Logs", ".md")
HEBREW_RE = re.compile(r"[\u0590-\u05ff]")

class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])
        if tag == "link" and attrs.get("href"):
            self.links.append(attrs["href"])
        if tag == "script" and attrs.get("src"):
            self.links.append(attrs["src"])

def public_html_files():
    for p in ROOT.rglob("*.html"):
        rel = p.relative_to(ROOT)
        if any(part.startswith(".") or part.startswith("_") for part in rel.parts):
            continue
        yield p

def link_to_path(href: str) -> Path | None:
    href = href.split("#",1)[0].split("?",1)[0]
    if not href or href.startswith(("http://", "https://", "mailto:", "tel:")):
        return None
    if href.startswith(BASE + "/"):
        rel = href[len(BASE)+1:]
    elif href.startswith("/"):
        return None
    else:
        rel = href
    if rel.endswith("/"):
        rel += "index.html"
    return ROOT / rel

def main() -> int:
    errors = []
    pages = list(public_html_files())
    css_path = ROOT / "assets/css/alte-lesart.css"
    if css_path.exists():
        css = css_path.read_text(encoding="utf-8")
        contrast_guards = {
            "global high-contrast eyebrow": ".eyebrow{display:inline-flex;align-items:center;gap:.45rem;color:#241306;background:#ffe1a0",
            "first section intro protected on dark background": "main>.section:first-child>.section-intro,main>.section:first-child>.lead{display:block",
            "first section intro light text": "color:#fff4d0;background:rgba(18,13,9,.56)",
            "geometry classes visibly vary": "--geo-transform:rotate(",
        }
        for label, needle in contrast_guards.items():
            if needle not in css:
                errors.append(f"CSS contrast/geometry guard missing: {label}")
        if len(set(re.findall(r"body\.geo-\d\d\{--geo:([^;]+);", css))) < 30:
            errors.append("CSS geometry guard failed: expected 30 distinct page patterns")
    else:
        errors.append("Missing public CSS file assets/css/alte-lesart.css")
    for page in pages:
        text = page.read_text(encoding="utf-8")
        rel = page.relative_to(ROOT)
        parser = LinkParser(); parser.feed(text)
        for href in parser.links:
            if any(bad in href for bad in FORBIDDEN):
                errors.append(f"{rel}: forbidden public link -> {href}")
            target = link_to_path(href)
            if target and not target.exists():
                errors.append(f"{rel}: broken local link -> {href} ({target.relative_to(ROOT)})")
        if not rel.parts[0] in {"assets"}:
            for core in CORE:
                if core not in text:
                    errors.append(f"{rel}: missing core navigation link {core}")
        if HEBREW_RE.search(text) and not re.search(r"Quelle|Status|Ibn-Tibbon|Quellen", text, re.I):
            errors.append(f"{rel}: Hebrew text without visible source/status marker")
    if errors:
        print("QUALITY CHECK FAILED")
        for e in errors:
            print("-", e)
        return 1
    print(f"QUALITY CHECK OK — {len(pages)} public HTML files checked")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
