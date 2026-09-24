#!/usr/bin/env python3
"""Bootstrap the docs/ tree: subfolders, an index, and the canonical-context glossary.

Idempotent: existing files are left untouched. It creates structure only — never
invent requirements. Run `docs_lint.py` afterwards to confirm the layout.

Usage:
    python scripts/init_docs.py [--docs docs] [--context-name NAME]
"""

import argparse
import sys
from pathlib import Path

SUBFOLDERS = ["context", "product", "architecture", "decisions", "development"]

INDEX_TEMPLATE = """# Documentation Index

{description}

| Subfolder | Purpose |
| :--- | :--- |
| `context/` | Canonical language and domain vocabulary |
| `product/` | Product requirements and domain behavior |
| `architecture/` | System design and technical contracts |
| `decisions/` | Architecture Decision Records |
| `development/` | Build, verify, and contribute |

Documents are named `docs/<subfolder>/<NNN>-<kebab-name>.md`.
"""

GLOSSARY_TEMPLATE = """# {context_name}

{description}

## Language

<!-- Add a row when a term is resolved. Meaning says what the term IS, in one or two sentences; list synonyms under Avoid. -->

| Term | Meaning | Avoid |
| :--- | :--- | :--- |
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--docs", default="docs", help="path to the docs directory (default: docs)")
    parser.add_argument("--context-name", default="Project Context", help="name for the canonical context")
    parser.add_argument("--description", default="", help="one-line description of the project/context")
    args = parser.parse_args()

    docs = Path(args.docs)
    description = args.description or "<One or two sentences on what this project is and why it exists.>"

    created = []
    existing = []

    for subfolder in SUBFOLDERS:
        path = docs / subfolder
        path.mkdir(parents=True, exist_ok=True)
        keep = path / ".gitkeep"
        if not any(path.iterdir()) and not keep.exists():
            keep.write_text("", encoding="utf-8")
            created.append(keep)

    index = docs / "README.md"
    if index.exists():
        existing.append(index)
    else:
        index.parent.mkdir(parents=True, exist_ok=True)
        index.write_text(INDEX_TEMPLATE.format(description=description), encoding="utf-8")
        created.append(index)

    glossary = docs / "context" / "001-ubiquitous-language.md"
    if glossary.exists():
        existing.append(glossary)
    else:
        glossary.write_text(
            GLOSSARY_TEMPLATE.format(context_name=args.context_name, description=description),
            encoding="utf-8",
        )
        created.append(glossary)

    for path in created:
        print(f"CREATE  {path}")
    for path in existing:
        print(f"SKIP    {path} (already exists)")

    # Drop placeholder .gitkeep files once a folder has real content.
    for subfolder in SUBFOLDERS:
        keep = docs / subfolder / ".gitkeep"
        if keep.exists() and any(p.name != ".gitkeep" for p in keep.parent.iterdir()):
            keep.unlink()

    print(f"\nNext: populate docs/context/001-ubiquitous-language.md with verified domain terms,")
    print("then document verified facts in the other subfolders. Run scripts/docs_lint.py to check.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
