import os
import re

terms = ["pendente", "parcial", "não", "não é", "memorysaver", "langsmith", "build", "tbd", "próximo nightly", "evidências externas"]

files_to_search = [
    "README.md",
    "docs/entrega.md",
    "docs/github-kanban.md"
]

dirs_to_search = [
    "docs/evidencias",
    "docs/lowcode",
    ".github/workflows"
]

all_paths = list(files_to_search)

for d in dirs_to_search:
    if os.path.exists(d):
        if os.path.isdir(d):
            for root, _, files in os.walk(d):
                for f in files:
                    all_paths.append(os.path.join(root, f))
        else:
            all_paths.append(d)

found = []
for path in all_paths:
    if not os.path.exists(path):
        continue
    if os.path.isdir(path):
        continue
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            for l_num, line in enumerate(f, 1):
                line_lower = line.lower()
                for term in terms:
                    if term in line_lower:
                        found.append((path, l_num, term, line.strip()))
                        break
    except Exception as e:
        pass

print(f"Total findings: {len(found)}")
# Let's print the findings related to contradictions or technical limitations
# We'll group them or filter them in Python to identify context or write them to a small summary file
with open("search_results.txt", "w", encoding="utf-8") as out:
    for path, l_num, term, line in found:
        out.write(f"[{path}:{l_num}] (Term: {term}) -> {line}\n")
