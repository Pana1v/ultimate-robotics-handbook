#!/usr/bin/env python3
"""Render the GitBook sources into a static _site/ that mirrors how the live
GitBook renders: README.md as the home page (with its cover), the SUMMARY.md
sidebar, card grids shown as image cards, and the common {% %} blocks."""
import os
import re
import html
import shutil
from pathlib import Path

import markdown

ROOT = Path('.')
OUT = Path('_site')
SKIP_DIRS = {'_site', '_book', '.git', 'node_modules', 'thirdparty'}


def md_to_html_path(path):
    """A repo-relative .md path -> root-relative .html URL under _site."""
    p = path.split('#', 1)
    anchor = '#' + p[1] if len(p) > 1 else ''
    rel = p[0]
    if rel.endswith('README.md') and rel == 'README.md':
        return '/index.html' + anchor
    if rel.endswith('.md'):
        rel = rel[:-3] + '.html'
    return '/' + rel.lstrip('./') + anchor


def split_frontmatter(text):
    cover = None
    if text.startswith('---'):
        end = text.find('\n---', 3)
        if end != -1:
            fm = text[3:end]
            body = text[end + 4:]
            m = re.search(r'https?://\S+', fm) if 'cover:' in fm else None
            if m:
                cover = m.group(0).strip().rstrip('>').strip()
            return cover, body.lstrip('\n')
    return cover, text


def transform_liquid(text):
    text = re.sub(r'{%\s*hint style="(\w+)"\s*%}', r'<div class="hint hint-\1">', text)
    text = re.sub(r'{%\s*endhint\s*%}', '</div>', text)
    text = re.sub(r'{%\s*embed url="(.*?)"\s*%}', r'\n<p class="embed"><a href="\1">\1</a></p>\n', text)
    text = re.sub(r'{%\s*endembed\s*%}', '', text)
    text = re.sub(r'{%\s*tabs\s*%}', '<div class="tabs">', text)
    text = re.sub(r'{%\s*tab title="(.*?)"\s*%}', r'<div class="tab"><div class="tab-title">\1</div>', text)
    text = re.sub(r'{%\s*endtab\s*%}', '</div>', text)
    text = re.sub(r'{%\s*endtabs\s*%}', '</div>', text)
    return text


ROW_RE = re.compile(
    r'<tr><td>(.*?)</td>'
    r'<td>(?:<a href="(.*?)".*?</a>)?</td>'
    r'<td>(?:<a href="(.*?)".*?</a>)?</td></tr>',
    re.DOTALL,
)


def transform_cards(text, page_dir):
    def repl(m):
        tbody = m.group(0)
        cards = []
        for title, href, cover in ROW_RE.findall(tbody):
            title = html.unescape(re.sub(r'<.*?>', '', title)).strip()
            link = resolve_href(href, page_dir) if href else '#'
            if cover:
                cov = resolve_asset(cover, page_dir)
                img = f'<img loading="lazy" src="{html.escape(cov)}" alt="">'
            else:
                img = '<div class="card-noimg">no cover</div>'
            cards.append(
                f'<a class="card" href="{html.escape(link)}">{img}'
                f'<span class="card-title">{html.escape(title)}</span></a>'
            )
        return '<div class="cards">' + ''.join(cards) + '</div>'

    return re.sub(r'<table data-view="cards">.*?</table>', repl, text, flags=re.DOTALL)


def resolve_href(href, page_dir):
    """Resolve a page-relative link target to a root-relative _site URL."""
    if href.startswith(('http://', 'https://', '#', 'mailto:', '/')):
        return href
    repo_rel = os.path.normpath(os.path.join(page_dir, href.split('#', 1)[0]))
    anchor = ''
    if '#' in href:
        anchor = '#' + href.split('#', 1)[1]
    if repo_rel.endswith('.md'):
        return md_to_html_path(repo_rel) + anchor
    return '/' + repo_rel.replace(os.sep, '/') + anchor


def resolve_asset(src, page_dir):
    if src.startswith(('http://', 'https://', 'data:', '/')):
        return src
    repo_rel = os.path.normpath(os.path.join(page_dir, src))
    return '/' + repo_rel.replace(os.sep, '/')


def rewrite_links(html_text, page_dir):
    """Rewrite <a href> and <img src> in rendered HTML to root-relative URLs."""
    html_text = re.sub(
        r'href="([^"]+)"',
        lambda m: f'href="{resolve_href(m.group(1), page_dir)}"',
        html_text,
    )
    html_text = re.sub(
        r'(<img[^>]+?)src="([^"]+)"',
        lambda m: f'{m.group(1)}src="{resolve_asset(m.group(2), page_dir)}"',
        html_text,
    )
    return html_text


def parse_summary():
    nav = []
    for line in open('SUMMARY.md'):
        raw = line.rstrip('\n')
        h = re.match(r'^##\s+(.+)', raw)
        if h:
            nav.append(('section', 0, h.group(1).strip(), None))
            continue
        l = re.match(r'^(\s*)\*\s+\[(.+?)\]\((.+?)\)', raw)
        if l:
            depth = len(l.group(1)) // 2
            nav.append(('link', depth, l.group(2).strip(), l.group(3).strip()))
    return nav


def build_nav(nav, current_url):
    out = ['<nav class="sidebar"><div class="brand">📚 Ultimate Robotics Handbook</div>']
    for kind, depth, title, target in nav:
        if kind == 'section':
            out.append(f'<div class="nav-section">{html.escape(title)}</div>')
        else:
            url = md_to_html_path(target)
            cls = 'nav-link' + (' active' if url == current_url else '')
            pad = 12 + depth * 14
            out.append(
                f'<a class="{cls}" style="padding-left:{pad}px" '
                f'href="{html.escape(url)}">{html.escape(title)}</a>'
            )
    out.append('</nav>')
    return ''.join(out)


PAGE = """<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
:root{{--accent:#3b66f5;--bg:#fff;--side:#f7f8fa;--border:#e6e8eb;--muted:#6b7280;}}
*{{box-sizing:border-box;}}
body{{margin:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;color:#1a1a1a;display:flex;}}
.sidebar{{width:300px;min-width:300px;height:100vh;overflow-y:auto;background:var(--side);border-right:1px solid var(--border);padding:16px 8px 60px;position:sticky;top:0;}}
.brand{{font-weight:700;font-size:15px;padding:8px 12px 16px;}}
.nav-section{{font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);margin:18px 0 4px;padding:0 12px;font-weight:600;}}
.nav-link{{display:block;padding:5px 12px;color:#374151;text-decoration:none;font-size:13.5px;border-radius:6px;}}
.nav-link:hover{{background:#eceef1;}}
.nav-link.active{{background:#e4ebff;color:var(--accent);font-weight:600;}}
.main{{flex:1;min-width:0;height:100vh;overflow-y:auto;}}
.content{{max-width:860px;margin:0 auto;padding:40px 48px 120px;}}
.cover{{width:100%;height:240px;object-fit:cover;display:block;}}
h1{{font-size:32px;margin:.2em 0 .6em;}}
h2{{font-size:24px;margin-top:1.6em;border-bottom:1px solid var(--border);padding-bottom:.3em;}}
h3{{font-size:19px;margin-top:1.4em;}}
a{{color:var(--accent);}}
img{{max-width:100%;border-radius:8px;}}
pre{{background:#0d1117;color:#e6edf3;padding:16px;border-radius:8px;overflow-x:auto;font-size:13px;}}
code{{background:#f0f1f3;padding:2px 6px;border-radius:4px;font-size:.9em;}}
pre code{{background:none;padding:0;}}
table{{border-collapse:collapse;width:100%;margin:16px 0;display:block;overflow-x:auto;}}
th,td{{border:1px solid var(--border);padding:8px 12px;text-align:left;font-size:14px;}}
th{{background:#f4f5f7;}}
blockquote{{border-left:4px solid var(--accent);margin:16px 0;padding:4px 16px;color:var(--muted);background:#f7f8fa;}}
.cards{{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:18px;margin:24px 0;}}
.card{{border:1px solid var(--border);border-radius:12px;overflow:hidden;text-decoration:none;color:#1a1a1a;background:#fff;transition:box-shadow .15s,transform .15s;display:flex;flex-direction:column;}}
.card:hover{{box-shadow:0 6px 20px rgba(0,0,0,.10);transform:translateY(-2px);}}
.card img{{width:100%;height:130px;object-fit:cover;border-radius:0;display:block;background:#eef0f3;}}
.card-noimg{{height:130px;display:flex;align-items:center;justify-content:center;color:#9aa0a6;background:#eef0f3;font-size:13px;}}
.card-title{{padding:12px 14px;font-weight:600;font-size:14.5px;}}
.hint{{padding:12px 16px;border-radius:8px;margin:16px 0;border:1px solid;}}
.hint-info{{background:#eef4ff;border-color:#cdddff;}}
.hint-warning{{background:#fff8e6;border-color:#ffe6a3;}}
.hint-danger{{background:#fff0f0;border-color:#ffc9c9;}}
.hint-success{{background:#eefaf0;border-color:#bce9c8;}}
.tabs{{border:1px solid var(--border);border-radius:8px;margin:16px 0;}}
.tab{{padding:8px 16px;border-top:1px solid var(--border);}}
.tab:first-child{{border-top:none;}}
.tab-title{{font-weight:600;font-size:13px;color:var(--accent);margin-bottom:6px;}}
.embed a{{word-break:break-all;}}
@media(max-width:820px){{.sidebar{{display:none;}}.content{{padding:24px;}}}}
</style></head><body>
{nav}
<main class="main"><div class="content">{cover}{body}</div></main>
</body></html>"""


def render_md(text, page_dir):
    cover, body = split_frontmatter(text)
    body = transform_liquid(body)
    body = transform_cards(body, page_dir)
    h = markdown.markdown(body, extensions=['tables', 'fenced_code', 'sane_lists', 'attr_list'])
    h = rewrite_links(h, page_dir)
    return cover, h


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()

    # copy asset/widget dirs verbatim
    for d in ['.gitbook', 'widgets']:
        if Path(d).exists():
            shutil.copytree(d, OUT / d)

    nav = parse_summary()

    md_files = []
    for dirpath, dirnames, filenames in os.walk('.'):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith('.')]
        for fn in filenames:
            if fn.endswith('.md') and fn != 'SUMMARY.md':
                md_files.append(os.path.relpath(os.path.join(dirpath, fn), '.'))

    count = 0
    for rel in md_files:
        page_dir = os.path.dirname(rel)
        text = open(rel, encoding='utf-8').read()
        cover, body = render_md(text, page_dir)
        title_m = re.search(r'<h1[^>]*>(.*?)</h1>', body)
        title = re.sub(r'<.*?>', '', title_m.group(1)) if title_m else rel
        url = md_to_html_path(rel)
        out_path = OUT / url.lstrip('/')
        out_path.parent.mkdir(parents=True, exist_ok=True)
        cover_html = f'<img class="cover" src="{html.escape(cover)}" alt="">' if cover else ''
        page = PAGE.format(title=html.escape(title), nav=build_nav(nav, url),
                           cover=cover_html, body=body)
        out_path.write_text(page, encoding='utf-8')
        count += 1

    print(f"✓ Rendered {count} pages into {OUT}/  (home: {OUT}/index.html)")


if __name__ == '__main__':
    main()
