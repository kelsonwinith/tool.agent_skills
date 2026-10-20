#!/usr/bin/env python3
"""Bootstrap the docs/ tree: flat singleton files + numbered flows/ and decisions/ folders.

Idempotent: existing files are left untouched. It creates structure only — never
invent requirements. Run `docs_lint.py` afterwards to confirm the layout.

Usage:
    python scripts/init_docs.py [--docs docs] [--context-name NAME] [--description DESC]
"""

import argparse
import sys
from pathlib import Path

NUMBERED_SUBFOLDERS = ["flows", "decisions"]

INDEX_TEMPLATE = """# Documentation Index

{description}

| Path | Purpose |
| :--- | :--- |
| [`ubiquitous-language.md`](./ubiquitous-language.md) | Canonical language and domain vocabulary (`Term \\| Meaning \\| Avoid`) |
| [`product.md`](./product.md) | Core product scope, personas, and global business rules |
| [`architecture.md`](./architecture.md) | System design, code structure, data model, and API contracts |
| [`development.md`](./development.md) | Setup, build, test, and verification commands |
| [`flows/`](./flows/) | Numbered user and system flows (`docs/flows/<NNN>-<kebab-name>.md`) |
| [`decisions/`](./decisions/) | Numbered Architecture Decision Records (`docs/decisions/<NNN>-<kebab-name>.md`) |
"""

GLOSSARY_TEMPLATE = """# {context_name}

{description}

## Language

<!-- Add a row when a term is resolved. Meaning says what the term IS, in one or two sentences; list synonyms under Avoid. -->

| Term | Meaning | Avoid |
| :--- | :--- | :--- |
"""

SINGLETON_TEMPLATES = {
    "product.md": """# Product Overview & Business Rules

**Document Version**: 0.1.0
**Status**: Draft

<!-- TODO: Document verified product scope, personas, and global business rules. -->
""",
    "architecture.md": """# System Architecture

**Document Version**: 0.1.0
**Status**: Draft

<!-- TODO: Document verified system design, code structure, data models, and API contracts. -->
""",
    "development.md": """# Development Guide

**Document Version**: 0.1.0
**Status**: Draft

<!-- TODO: Document verified setup, build, test, and lint commands. -->
""",
}


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

    docs.mkdir(parents=True, exist_ok=True)

    for subfolder in NUMBERED_SUBFOLDERS:
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
        index.write_text(INDEX_TEMPLATE.format(description=description), encoding="utf-8")
        created.append(index)

    glossary = docs / "ubiquitous-language.md"
    if glossary.exists() or (docs / "context").is_dir():
        existing.append(glossary)
    else:
        glossary.write_text(
            GLOSSARY_TEMPLATE.format(context_name=args.context_name, description=description),
            encoding="utf-8",
        )
        created.append(glossary)

    for filename, template in SINGLETON_TEMPLATES.items():
        target = docs / filename
        if target.exists():
            existing.append(target)
        else:
            target.write_text(template, encoding="utf-8")
            created.append(target)

    for path in created:
        print(f"CREATE  {path}")
    for path in existing:
        print(f"SKIP    {path} (already exists)")

    # Drop placeholder .gitkeep files once a folder has real content.
    for subfolder in NUMBERED_SUBFOLDERS:
        keep = docs / subfolder / ".gitkeep"
        if keep.exists() and any(p.name != ".gitkeep" for p in keep.parent.iterdir()):
            keep.unlink()

    print("\nNext: populate docs/ubiquitous-language.md with verified domain terms,")
    print("fill in docs/{product,architecture,development}.md, and add flows via scripts/new_doc.py.")
    print("Run scripts/docs_lint.py to check.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
