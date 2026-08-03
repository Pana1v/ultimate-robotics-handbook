#!/bin/bash
# Handbook integrity audit.
#
# Checks three things the old version missed:
#   1. card-grid pages are DISCOVERED, not hardcoded (the old list had a
#      deleted file in it and silently skipped 8 real pages, including the
#      20-card root README)
#   2. every referenced asset actually EXISTS on disk (the old version only
#      string-matched ".gitbook/assets/", so a deleted asset still passed)
#   3. inline <figure> images and orphaned assets, which were never checked

cd "$(dirname "$0")" || exit 1

python3 <<'PYSCRIPT'
import re
import urllib.parse
from pathlib import Path

ROOT = Path(".").resolve()
ASSETS = ROOT / ".gitbook" / "assets"
SKIP = {"_book", ".git", "gif-staging", "node_modules"}

def pages():
    for p in sorted(ROOT.rglob("*.md")):
        if not SKIP.isdisjoint(p.parts):
            continue
        yield p

def resolve(page, ref):
    # GitBook wraps paths containing spaces or parens in angle brackets,
    # e.g. src="<../.gitbook/assets/download (1).png>".
    ref = urllib.parse.unquote(ref).strip().lstrip("<").rstrip(">")
    return (page.parent / ref).resolve()

card_pages = []
missing = []
inline_total = cover_total = 0
referenced = set()

ASSET_REF = re.compile(r"(?:src|href)\s*=\s*\"(<?[^\"]*\.gitbook/assets/[^\"]+>?)\"")
# Angle-bracket form must be tried first: filenames like "download (1).png"
# contain a ")" that would otherwise terminate the match early.
MD_REF = re.compile(r"!\[[^\]]*\]\((<[^>]+>|[^)]+)\)")

print("=== CARD COVERAGE ===\n")

for page in pages():
    text = page.read_text(encoding="utf-8", errors="ignore")
    rel = page.relative_to(ROOT)

    # Every asset reference on the page, whatever the syntax.
    for m in list(ASSET_REF.finditer(text)) + list(MD_REF.finditer(text)):
        ref = m.group(1)
        if ".gitbook/assets/" not in ref:
            continue
        target = resolve(page, ref)
        referenced.add(target.name)
        if not target.exists():
            missing.append(f"{rel} -> {ref}")

    if 'data-view="cards"' not in text:
        continue
    card_pages.append(rel)

    body = re.search(r"<tbody>(.*?)</tbody>", text, re.DOTALL)
    if not body:
        print(f"  {rel}: card grid present but no <tbody>")
        continue

    # Split on row boundaries rather than matching a title pattern, so cards
    # whose first cell opens with a tag (<td><strong>Hardware</strong>) count.
    rows = re.findall(r"<tr>(.*?)</tr>", body.group(1), re.DOTALL)
    filled = broken = empty = 0
    for row in rows:
        refs = ASSET_REF.findall(row)
        if not refs:
            empty += 1
        elif all(resolve(page, r).exists() for r in refs):
            filled += 1
        else:
            broken += 1
    cover_total += len(rows)

    flag = "" if (empty == 0 and broken == 0) else "   <-- needs attention"
    print(f"  {str(rel):68s} {filled}/{len(rows)} covers"
          f"{f', {empty} empty' if empty else ''}"
          f"{f', {broken} BROKEN' if broken else ''}{flag}")

inline_total = sum(
    len(ASSET_REF.findall(p.read_text(encoding='utf-8', errors='ignore')))
    for p in pages()
)

print(f"\n  {len(card_pages)} card-grid pages discovered\n")

print("=== ASSET INTEGRITY ===\n")
print(f"  {inline_total} local asset references checked")
if missing:
    print(f"  {len(missing)} BROKEN:")
    for m in missing:
        print(f"    {m}")
else:
    print("  0 broken references")

on_disk = {p.name for p in ASSETS.iterdir() if p.is_file()}
orphans = sorted(on_disk - referenced)
size = sum((ASSETS / o).stat().st_size for o in orphans)
print(f"\n  {len(on_disk)} assets on disk, {len(orphans)} orphaned"
      f" ({size/1e6:.1f} MB)")
for o in orphans[:15]:
    print(f"    {o}")
if len(orphans) > 15:
    print(f"    ... and {len(orphans)-15} more")

print("\n=== PAGES WITH NO VISUALS ===\n")
bare = []
for page in pages():
    text = page.read_text(encoding="utf-8", errors="ignore")
    if page.name == "SUMMARY.md":
        continue
    if not ASSET_REF.search(text) and not MD_REF.search(text):
        bare.append((len(text.splitlines()), page.relative_to(ROOT)))
bare.sort(reverse=True)
print(f"  {len(bare)} pages have no image, figure, or card cover")
for n, p in bare[:12]:
    print(f"    {n:4d} lines  {p}")
if len(bare) > 12:
    print(f"    ... and {len(bare)-12} more")

print()
PYSCRIPT
