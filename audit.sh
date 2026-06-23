#!/bin/bash

echo "=== CARD COVERAGE AUDIT ==="
echo ""

count_cards() {
  file="$1"
  [ -f "$file" ] || return
  
  section=$(basename $(dirname "$file"))
  
  # Use Python to parse the HTML properly
  python3 <<PYSCRIPT
import re
with open('$file', 'r') as f:
  content = f.read()
  
# Extract tbody
match = re.search(r'<tbody>(.*?)</tbody>', content, re.DOTALL)
if not match:
  print(f"❌ $section: No card grid found")
  exit()

tbody = match.group(1)

# Find all card rows (lines starting with <tr><td>card_title)
rows = re.findall(r'<tr><td>([^<]+)<', tbody)

filled = 0
empty = 0
cards_info = []

for row in rows:
  card_title = row.strip()
  # Check if this row in tbody has a cover
  row_full = re.search(f'<tr><td>{re.escape(card_title)}<.*?</tr>', tbody, re.DOTALL)
  if row_full and '.gitbook/assets/' in row_full.group(0):
    filled += 1
    # Extract image name
    img_match = re.search(r'\.gitbook/assets/([^"]+)', row_full.group(0))
    img = img_match.group(1) if img_match else 'unknown'
    cards_info.append(f"  ✅ {card_title}")
  else:
    empty += 1
    cards_info.append(f"  ❌ {card_title}")

total = filled + empty
print(f"📁 {section}")
for info in cards_info:
  print(info)
print(f"  → {filled}/{total} cards have covers ({empty} empty)\n")

PYSCRIPT
}

# Check all sections
for file in \
  ros-2/ros-2.md \
  robot-learning/robot-learning.md \
  slam-and-state-estimation/slam-and-state-estimation.md \
  programming-for-robotics/programming-for-robotics.md \
  foundations/foundations.md \
  authors-projects/authors-projects.md \
  widgets/widgets.md \
  frontiers-and-emerging-fields/frontiers-and-emerging-fields.md \
  career-paths-and-research-opportunities/career-paths-and-research-opportunities.md \
  common-mechanisms/common-mechanisms.md \
  hardware/hardware.md \
  computer-aided-designs-and-simulations/computer-aided-design-and-simulations.md \
  drones-rocketry-and-aviation/drones.md \
  embedded-systems-for-robotics/embedded-systems.md \
  mathematical-and-programming-foundations/mathematical-and-programming-foundations.md \
  perception-and-computer-vision/perception-and-computer-vision.md; do
  count_cards "$file"
done
