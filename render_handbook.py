#!/usr/bin/env python3
import os
import markdown
import re
from pathlib import Path

def extract_cards_from_markdown(content):
    """Extract card grids from markdown tables."""
    # Find all card tables and convert to HTML
    pattern = r'<table data-view="cards">.*?</table>'
    
    # For now, just mark them as card sections
    content = content.replace('<table data-view="cards">', '<div class="card-grid">')
    content = content.replace('</table>', '</div>')
    
    return content

def render_file(filepath):
    """Render a single markdown file to HTML."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Convert markdown to HTML
        html = markdown.markdown(content, extensions=['tables', 'fenced_code'])
        html = extract_cards_from_markdown(html)
        
        return html
    except:
        return f"<p>Error reading {filepath}</p>"

def generate_index():
    """Generate an index of all sections."""
    sections = []
    
    for item in sorted(os.listdir('.')):
        if os.path.isdir(item) and not item.startswith('.') and item != '_book':
            # Check for landing page
            landing = f"{item}/{item}.md"
            if not os.path.exists(landing):
                landing = find_landing(item)
            if landing:
                title = extract_title(landing)
                if title:
                    sections.append((item, title, landing))

    return sections

def find_landing(item):
    """Fallback: the section landing page is the single top-level .md
    in the directory that carries a card grid."""
    candidates = []
    for name in sorted(os.listdir(item)):
        path = f"{item}/{name}"
        if os.path.isfile(path) and name.endswith('.md'):
            with open(path, 'r') as f:
                if 'data-view="cards"' in f.read():
                    candidates.append(path)
    return candidates[0] if len(candidates) == 1 else None

def extract_title(filepath):
    """Return the first '# ' heading, skipping any YAML frontmatter."""
    with open(filepath, 'r') as f:
        lines = f.read().splitlines()
    i = 0
    if lines and lines[0].strip() == '---':
        i = 1
        while i < len(lines) and lines[i].strip() != '---':
            i += 1
        i += 1
    for line in lines[i:]:
        if line.startswith('# '):
            return line[2:].strip()
    return None

# Generate HTML
html_template = """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Ultimate Robotics Handbook</title>
  <style>
    * {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
    body {{ max-width: 1200px; margin: 0 auto; padding: 20px; background: #f5f5f5; }}
    h1 {{ color: #1a1a1a; border-bottom: 3px solid #0066cc; padding-bottom: 10px; }}
    h2 {{ color: #333; margin-top: 40px; }}
    a {{ color: #0066cc; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .section-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 15px; margin: 20px 0; }}
    .section-card {{ 
      border: 1px solid #ddd; 
      padding: 20px; 
      border-radius: 8px; 
      background: white;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
      transition: box-shadow 0.2s;
    }}
    .section-card:hover {{ box-shadow: 0 4px 8px rgba(0,0,0,0.15); }}
    .section-card h3 {{ margin-top: 0; color: #0066cc; }}
    .card-grid {{ 
      background: #f9f9f9; 
      border: 1px solid #ddd; 
      padding: 15px; 
      border-radius: 4px;
      margin: 10px 0;
    }}
    code {{ background: #f0f0f0; padding: 2px 6px; border-radius: 3px; font-size: 0.9em; }}
    pre {{ background: #2d2d2d; color: #f8f8f2; padding: 15px; border-radius: 4px; overflow-x: auto; }}
    table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
    th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
    th {{ background: #f0f0f0; }}
  </style>
</head>
<body>
  <h1>📚 Ultimate Robotics Handbook</h1>
  
  <h2>🎯 All Sections</h2>
  <p>Comprehensive robotics engineering reference covering foundations, software, hardware, perception, control, and learning.</p>
  
  <div class="section-grid">
    {sections}
  </div>
  
  <hr>
  <p><small>Last updated: {timestamp}</small></p>
</body>
</html>"""

import datetime
timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

sections = generate_index()
section_cards = '\n'.join([
    f'<div class="section-card"><h3><a href="{path}">{title}</a></h3><p>{item}/</p></div>'
    for item, title, path in sections
])

html = html_template.format(sections=section_cards, timestamp=timestamp)

with open('index.html', 'w') as f:
    f.write(html)

print(f"✓ Generated index.html with {len(sections)} sections")
