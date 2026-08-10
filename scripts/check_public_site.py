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
from html import unescape

ROOT = Path(__file__).resolve().parents[1]
BASE = "/alte-lesart"
CORE = [f"{BASE}/index.html", f"{BASE}/sammlung.html", f"{BASE}/lesepfade.html", f"{BASE}/quellen.html"]
FORBIDDEN = ("_internal", "_topic_manifest", "Batch-Logs", ".md")
HEBREW_RE = re.compile(r"[\u0590-\u05ff]")

class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = set()
        self.anchor_stack = []
        self.nested_anchor_lines = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id"):
            self.ids.add(attrs["id"])
        if attrs.get("name"):
            self.ids.add(attrs["name"])
        if tag == "a":
            if self.anchor_stack:
                self.nested_anchor_lines.append(self.getpos()[0])
            self.anchor_stack.append(self.getpos()[0])
            if attrs.get("href"):
                self.links.append(attrs["href"])
        if tag == "link" and attrs.get("href"):
            self.links.append(attrs["href"])
        if tag == "script" and attrs.get("src"):
            self.links.append(attrs["src"])
    def handle_endtag(self, tag):
        if tag == "a" and self.anchor_stack:
            self.anchor_stack.pop()

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
            "focus mode styles present": "body.focus-mode",
            "reading flow hook styles present": ".flow-hook",
            "return cue styles present": ".return-cue",
            "chapter chip links present": ".chips a.chip",
            "chapter thread links present": ".chapter-thread a",
            "mobile first heading protected": "main>.section:first-child>h2{display:block;width:100%",
            "mobile intro protected": "main>.section:first-child>.section-intro,main>.section:first-child>.lead{width:100%",
        }
        for label, needle in contrast_guards.items():
            if needle not in css:
                errors.append(f"CSS contrast/geometry guard missing: {label}")
        for needle in (".cookie-banner", ".cookie-actions", ".consent-reset", "body.consent-required", ".cookie-card"):
            if needle not in css:
                errors.append(f"CSS consent guard missing: {needle}")
        if len(set(re.findall(r"body\.geo-\d\d\{--geo:([^;]+);", css))) < 30:
            errors.append("CSS geometry guard failed: expected 30 distinct page patterns")
    else:
        errors.append("Missing public CSS file assets/css/alte-lesart.css")
    workflow_path = ROOT / ".github/workflows/pages.yml"
    js_path = ROOT / "assets/js/alte-lesart.js"
    if js_path.exists():
        js = js_path.read_text(encoding="utf-8")
        for needle in ("alte-lesart-cookie-consent", "consent-required", "data-consent=\"accept\"", "Ohne Zustimmung ist die Nutzung der Website nicht möglich"):
            if needle not in js:
                errors.append(f"JS consent guard missing: {needle}")
        if "data-consent=\"reject\"" in js or "'rejected'" in js or '"rejected"' in js:
            errors.append("JS consent gate must not offer or persist rejection")
    else:
        errors.append("Missing public JS file assets/js/alte-lesart.js")
    workflow_path = ROOT / ".github/workflows/pages.yml"
    if workflow_path.exists():
        workflow = workflow_path.read_text(encoding="utf-8")
        if "datenschutz.html" not in workflow:
            errors.append("Pages workflow must publish datenschutz.html")
    else:
        errors.append("Missing Pages workflow .github/workflows/pages.yml")
    reading_blocks = {}
    repeated_reading_paragraphs = {}
    for page in pages:
        text = page.read_text(encoding="utf-8")
        rel = page.relative_to(ROOT)
        parser = LinkParser(); parser.feed(text)
        for line in parser.nested_anchor_lines:
            errors.append(f"{rel}: nested anchor tag near line {line}")
        if re.search(r"\bPremium\b", text, re.I):
            errors.append(f"{rel}: visitor-facing copy must not use marketing word Premium")
        for href in parser.links:
            if any(bad in href for bad in FORBIDDEN):
                errors.append(f"{rel}: forbidden public link -> {href}")
            target = link_to_path(href)
            if target and not target.exists():
                errors.append(f"{rel}: broken local link -> {href} ({target.relative_to(ROOT)})")
            if "#" in href and not href.startswith(("http://", "https://", "mailto:", "tel:")):
                fragment = href.split("#", 1)[1].split("?", 1)[0]
                fragment_target = page if href.startswith("#") else target
                if fragment and fragment_target and fragment_target.exists() and fragment_target.is_file():
                    target_parser = LinkParser(); target_parser.feed(fragment_target.read_text(encoding="utf-8"))
                    if fragment not in target_parser.ids:
                        errors.append(f"{rel}: broken fragment link -> {href}")
        if not rel.parts[0] in {"assets"}:
            for core in CORE:
                if core not in text:
                    errors.append(f"{rel}: missing core navigation link {core}")
            if f"{BASE}/datenschutz.html" not in text:
                errors.append(f"{rel}: missing privacy/consent link {BASE}/datenschutz.html")
            if "googletagmanager.com/gtag/js" in text or "function gtag" in text or "gtag('config'" in text:
                errors.append(f"{rel}: eager Google Analytics load before consent")
            if "G-D8TK9RQ0DE" in text and "window.ALTE_LESART_ANALYTICS_ID" not in text:
                errors.append(f"{rel}: analytics id is not behind consent handoff")
        is_teil_iii_intro = rel.parts == ("werke", "fuehrer-der-unschluessigen", "teil-iii", "einleitung.html")
        if rel.parts[:2] == ("werke", "fuehrer-der-unschluessigen") and (rel.name.startswith("kapitel-") or is_teil_iii_intro):
            reading = re.search(r'<div class="reading-text">(.*?)</div>', text, re.S)
            if reading:
                plain = unescape(re.sub(r"<[^>]+>", " ", reading.group(1)))
                plain = re.sub(r"\s+", " ", plain).strip().lower()
                min_words = 300 if len(rel.parts) >= 4 and rel.parts[2] in {"teil-ii", "teil-iii"} else 150
                if len(plain.split()) < min_words:
                    errors.append(f"{rel}: reading text is too thin ({len(plain.split())} words)")
                digest = re.sub(r"[^a-zäöüß0-9 ]", "", plain)
                if digest in reading_blocks:
                    errors.append(f"{rel}: duplicate reading-text matches {reading_blocks[digest]}")
                else:
                    reading_blocks[digest] = rel
                if len(rel.parts) >= 4 and rel.parts[2] in {"teil-ii", "teil-iii"}:
                    for paragraph in re.findall(r"<p>(.*?)</p>", reading.group(1), re.S):
                        paragraph_plain = unescape(re.sub(r"<[^>]+>", " ", paragraph))
                        paragraph_plain = re.sub(r"\s+", " ", paragraph_plain).strip().lower()
                        paragraph_digest = re.sub(r"[^a-zäöüß0-9 ]", "", paragraph_plain)
                        if len(paragraph_plain.split()) >= 24:
                            if paragraph_digest in repeated_reading_paragraphs:
                                errors.append(f"{rel}: repeated Teil-II reading paragraph also appears in {repeated_reading_paragraphs[paragraph_digest]}")
                            else:
                                repeated_reading_paragraphs[paragraph_digest] = rel
            else:
                errors.append(f"{rel}: missing reading-text block")
            chapter_match = re.search(r"kapitel-(\d{3})\.html", rel.name)
            current_chapter = int(chapter_match.group(1)) if chapter_match else None
            if len(rel.parts) >= 4 and rel.parts[2] == "teil-ii":
                part_label = "II"
                chapter_base = f"{BASE}/werke/fuehrer-der-unschluessigen/teil-ii"
                chapter_dir = ROOT / "werke/fuehrer-der-unschluessigen/teil-ii"
            elif len(rel.parts) >= 4 and rel.parts[2] == "teil-iii":
                part_label = "III"
                chapter_base = f"{BASE}/werke/fuehrer-der-unschluessigen/teil-iii"
                chapter_dir = ROOT / "werke/fuehrer-der-unschluessigen/teil-iii"
            else:
                part_label = "I"
                chapter_base = f"{BASE}/werke/fuehrer-der-unschluessigen"
                chapter_dir = ROOT / "werke/fuehrer-der-unschluessigen"
            thread = re.search(r'<div class="chapter-thread"[^>]*>(.*?)</div>', text, re.S)
            if not thread:
                errors.append(f"{rel}: missing chapter-thread navigation")
            else:
                thread_html = thread.group(1)
                expected_chapters = len(list(chapter_dir.glob("kapitel-*.html")))
                expected_links = expected_chapters + (1 if part_label == "III" else 0)
                if len(re.findall(r"<a\b", thread_html)) != expected_links:
                    errors.append(f"{rel}: chapter-thread must contain {expected_links} clickable links")
                if part_label == "III" and f'{chapter_base}/einleitung.html' not in thread_html:
                    errors.append(f"{rel}: Teil-III chapter-thread missing Einleitung link")
                if re.search(r"<span\b", thread_html):
                    errors.append(f"{rel}: chapter-thread contains non-clickable span")
                for i in range(1, expected_chapters + 1):
                    href = f'{chapter_base}/kapitel-{i:03d}.html'
                    if href not in thread_html:
                        errors.append(f"{rel}: missing clickable chapter number {part_label},{i}")
                    if f'aria-label="Kapitel {part_label},{i} öffnen"' not in thread_html:
                        errors.append(f"{rel}: missing accessible label for chapter number {part_label},{i}")
                    if f'title="Kapitel {part_label},{i}"' not in thread_html:
                        errors.append(f"{rel}: missing title for chapter number {part_label},{i}")
                    wrong_parts = [label for label in ("I", "II", "III") if label != part_label]
                    for wrong_part in wrong_parts:
                        if re.search(rf'Kapitel {wrong_part},\d+', thread_html):
                            errors.append(f"{rel}: chapter-thread contains wrong part label Kapitel {wrong_part},…")
                if current_chapter:
                    active_href = f'{chapter_base}/kapitel-{current_chapter:03d}.html'
                    active_link = re.search(rf'<a\b(?=[^>]*href="{re.escape(active_href)}")[^>]*>', thread_html)
                    if not active_link or 'aria-current="page"' not in active_link.group(0):
                        errors.append(f"{rel}: active chapter lacks aria-current")
                elif is_teil_iii_intro:
                    active_href = f'{chapter_base}/einleitung.html'
                    active_link = re.search(rf'<a\b(?=[^>]*href="{re.escape(active_href)}")[^>]*>', thread_html)
                    if not active_link or 'aria-current="page"' not in active_link.group(0):
                        errors.append(f"{rel}: active Teil-III Einleitung lacks aria-current")
            chips = re.search(r'<div class="chips">(.*?)</div>', text, re.S)
            if not chips or len(re.findall(r'<a class="chip"', chips.group(1))) != 4:
                errors.append(f"{rel}: metadata chips must all be clickable links")
            elif part_label == "II" and current_chapter:
                expected_topics = {
                    1: "beweis-und-praemissen",
                    2: "erster-beweger",
                    3: "unkoerperlichkeit-und-beweis",
                    4: "einheit-und-beweis",
                    5: "himmel-und-sphaeren",
                    6: "engel-und-intellekte",
                    7: "engel-und-intellekte",
                    8: "engel-und-intellekte",
                    9: "musik-der-sphaeren",
                    10: "himmel-und-sphaeren",
                    11: "himmel-und-sphaeren",
                    12: "engel-und-intellekte",
                    13: "schoepfung-und-beweis",
                    14: "aristoteles-und-tora",
                    15: "grenzen-des-verstandes",
                    16: "schoepfung-und-beweis",
                    17: "schoepfung-und-beweis",
                    18: "schoepfung-und-beweis",
                    19: "schoepfung-und-beweis",
                    20: "schoepfung-und-beweis",
                    21: "schoepfung-und-beweis",
                    22: "schoepfung-und-beweis",
                    23: "himmel-und-sphaeren",
                    24: "grenzen-des-verstandes",
                    25: "himmel-und-sphaeren",
                    26: "aristoteles-und-tora",
                    27: "himmel-und-sphaeren",
                    28: "schoepfung-und-beweis",
                    29: "aristoteles-und-tora",
                    30: "prophetie",
                    31: "maaseh-bereschit",
                    32: "schabbat-und-schoepfung",
                    33: "prophetie",
                    34: "sinai-und-prophetie",
                    35: "sinai-und-prophetie",
                    36: "sinai-und-prophetie",
                    37: "prophetie",
                    38: "prophetie",
                    39: "prophetie",
                    40: "prophetie-und-tora",
                    41: "prophetie-und-tora",
                    42: "traum-und-vision",
                    43: "traum-und-vision",
                    44: "gleichnis-und-prophetie",
                    45: "stimme-und-offenbarung",
                    46: "prophetische-grade",
                    47: "visionshandlung",
                    48: "metapher-und-uebertreibung",
                    49: "ursachen-und-zuschreibung",
                }
                expected_topic = expected_topics.get(current_chapter)
                chip_html = chips.group(1)
                if expected_topic and f'{BASE}/themen/{expected_topic}.html' not in chip_html:
                    errors.append(f"{rel}: expected thematic chip {expected_topic}")
            elif part_label == "III" and current_chapter:
                chip_html = chips.group(1)
                if f'{BASE}/themen/maaseh-merkavah.html' not in chip_html:
                    errors.append(f"{rel}: expected thematic chip maaseh-merkavah")
        if HEBREW_RE.search(text) and not re.search(r"Quelle|Status|Ibn-Tibbon|Quellen", text, re.I):
            errors.append(f"{rel}: Hebrew text without visible source/status marker")
    lesepfade = ROOT / "lesepfade.html"
    if lesepfade.exists():
        text = lesepfade.read_text(encoding="utf-8")
        for needle in (
            "Schöpfung, Ewigkeit und Gewissheit",
            "Naturordnung ohne falsche Notwendigkeit",
            "kapitel-013.html",
            "kapitel-021.html",
            "kapitel-030.html",
            "kapitel-031.html",
            "kapitel-033.html",
            "kapitel-034.html",
            "kapitel-037.html",
            "Sinai, Moses und Prophetie",
            "kapitel-038.html",
            "kapitel-042.html",
            "Prophetie wird öffentlich",
            "kapitel-043.html",
            "kapitel-045.html",
            "Engel, Gleichnis und Stimme",
            "engel-gleichnis-stimme",
            "kapitel-046.html",
            "kapitel-049.html",
            "Prophetische Leseregeln",
            "Ursachen und Zuschreibung",
            "maaseh-merkavah",
            "Ezechiels Wagenvision lesen",
            "teil-iii/einleitung.html",
            "teil-iii/kapitel-002.html",
            "Maaseh Merkavah",
        ):
            if needle not in text:
                errors.append(f"lesepfade.html: missing curated route marker {needle}")
        if "Kapitel 1–20" in text or "II,1–II,20" in text:
            errors.append("lesepfade.html: stale Teil-II range still visible")
    for chapter in range(21, 50):
        page = ROOT / f"werke/fuehrer-der-unschluessigen/teil-ii/kapitel-{chapter:03d}.html"
        if page.exists():
            text = page.read_text(encoding="utf-8")
            generic = f"Kapitel II,{chapter} gehört zum erweiterten Teil-II-Faden"
            if generic in text:
                errors.append(f"{page.relative_to(ROOT)}: generic foundation callout not replaced")
    if errors:
        print("QUALITY CHECK FAILED")
        for e in errors:
            print("-", e)
        return 1
    print(f"QUALITY CHECK OK — {len(pages)} public HTML files checked")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
