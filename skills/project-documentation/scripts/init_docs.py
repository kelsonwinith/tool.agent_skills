#!/usr/bin/env python3
"""Bootstrap the docs/ tree: root singletons, feature templates, and ADR folder.

Creates a lean, high-signal documentation structure:
  docs/
  ├── README.md               # Overview & feature index
  ├── context.md              # Canonical glossary (ubiquitous language) + global invariants
  ├── architecture.md         # System stack, components & data models
  ├── features/               # Scalable feature specs (flowcharts + conflict check)
  │   └── 001-example-feature.md
  └── decisions/              # Architecture Decision Records
      └── .gitkeep

Idempotent: existing files are left untouched.
If the repository already has code files, it advises the user to reverse-engineer
and document the existing baseline first.

Usage:
    python scripts/init_docs.py [--docs docs] [--project-name NAME] [--description DESC]
"""

import argparse
import sys
from pathlib import Path

README_TEMPLATE = """# {project_name} Documentation

{description}

## Document Map

| Document | Purpose | Status |
| :--- | :--- | :--- |
| [`context.md`](context.md) | Canonical ubiquitous language & global invariants | Active |
| [`architecture.md`](architecture.md) | System components, tech stack & data models | Active |
| `features/` | Feature specifications, Mermaid flowcharts & conflict audits | Active |
| `decisions/` | Architecture Decision Records (ADRs) | Active |

## Features Index

| ID | Feature | Flowchart | Conflict Status |
| :--- | :--- | :--- | :--- |
| 001 | [Example Feature](features/001-example-feature.md) | Yes | Resolved |
"""

CONTEXT_TEMPLATE = """# {project_name} Context & Ubiquitous Language

{description}

## Canonical Language

<!-- Add a row when a domain term is resolved. Meaning says what it IS; list forbidden synonyms in Avoid. -->
| Term | Meaning | Avoid |
| :--- | :--- | :--- |
| User | A registered person using the system. | Client, customer, account |

## Global Business Invariants

- **INV-001**: Every system entity must have a globally unique identifier.
- **INV-002**: Timestamps must be stored in UTC ISO 8601 format.
"""

ARCHITECTURE_TEMPLATE = """# System Architecture

## 1. System Overview & Tech Stack
- **Runtime / Language**: 
- **Frameworks & Libraries**: 
- **Storage / Database**: 

## 2. Core Architecture Diagram
```mermaid
graph TD
    Client[Client / Consumer] --> API[Application Service]
    API --> DB[(Primary Storage)]
```

## 3. Data Models
| Entity | Key Fields | Notes |
| :--- | :--- | :--- |
| `User` | `id`, `email`, `created_at` | Primary account entity |
"""

FEATURE_TEMPLATE = """# 001: Example Feature

**Document Version**: 0.1.0  
**Status**: Draft  
**Last Modified**: {date}

## 1. Purpose & Scope
A concise 1-2 sentence description of what this feature achieves and what is explicitly out of scope.

## 2. Logic Flowchart
```mermaid
flowchart TD
    Start([User Trigger]) --> Check{{Input Valid?}}
    Check -->|Yes| Execute[Process Action]
    Check -->|No| Fail[Return Error]
    Execute --> Done([Complete])
```

## 3. Requirements & Rules
- **FR-001**: System must validate user permissions prior to action.
- **FR-002**: Result status must be persisted and confirmed.

## 4. Cross-Feature Conflict & Overlap Check
- **Dependencies**: Relies on `context.md` (User entity).
- **Potential Overlaps**: Check against adjacent features.
- **Collision Analysis**: No contradictory business rules or state conflicts identified.
"""

CODE_EXTENSIONS = {
    ".ts", ".tsx", ".js", ".jsx", ".py", ".go", ".rs", ".java",
    ".kt", ".cs", ".cpp", ".c", ".rb", ".php", ".swift"
}
SKIP_DIRS = {".git", "node_modules", ".next", "dist", "build", "vendor", "__pycache__", "docs"}


def detect_existing_code(root: Path) -> bool:
    """Check if the root directory contains substantial existing code."""
    count = 0
    for path in root.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.is_file() and path.suffix in CODE_EXTENSIONS:
            count += 1
            if count >= 3:
                return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--docs", default="docs", help="path to the docs directory (default: docs)")
    parser.add_argument("--project-name", "--context-name", dest="project_name", default="Project", help="name for the project / context")
    parser.add_argument("--description", default="", help="one-line description of the project")
    args = parser.parse_args()

    docs = Path(args.docs)
    description = args.description or "<One or two sentences on what this project is and why it exists.>"
    project_name = args.project_name

    created = []
    existing = []

    # Ensure directories exist
    docs.mkdir(parents=True, exist_ok=True)
    features_dir = docs / "features"
    features_dir.mkdir(parents=True, exist_ok=True)
    decisions_dir = docs / "decisions"
    decisions_dir.mkdir(parents=True, exist_ok=True)
    requests_dir = docs / "requests"
    requests_dir.mkdir(parents=True, exist_ok=True)

    # 1. README.md
    readme_path = docs / "README.md"
    if readme_path.exists():
        existing.append(readme_path)
    else:
        readme_path.write_text(
            README_TEMPLATE.format(project_name=project_name, description=description),
            encoding="utf-8"
        )
        created.append(readme_path)

    # 2. context.md
    context_path = docs / "context.md"
    if context_path.exists():
        existing.append(context_path)
    else:
        context_path.write_text(
            CONTEXT_TEMPLATE.format(project_name=project_name, description=description),
            encoding="utf-8"
        )
        created.append(context_path)

    # 3. architecture.md
    arch_path = docs / "architecture.md"
    if arch_path.exists():
        existing.append(arch_path)
    else:
        arch_path.write_text(
            ARCHITECTURE_TEMPLATE.format(project_name=project_name),
            encoding="utf-8"
        )
        created.append(arch_path)

    # 4. Starter feature template (if features/ is empty)
    import datetime
    today = datetime.date.today().isoformat()
    feature_starter = features_dir / "001-example-feature.md"
    if not any(features_dir.glob("*.md")):
        feature_starter.write_text(
            FEATURE_TEMPLATE.format(date=today),
            encoding="utf-8"
        )
        created.append(feature_starter)
    else:
        existing.append(features_dir)

    # 5. decisions .gitkeep
    decisions_keep = decisions_dir / ".gitkeep"
    if not any(decisions_dir.iterdir()):
        decisions_keep.write_text("", encoding="utf-8")
        created.append(decisions_keep)

    # 6. Ensure docs/requests/ is ignored in .gitignore
    gitignore_path = (docs.parent / ".gitignore") if docs.parent.is_dir() else Path(".gitignore")
    ignore_entry = f"{docs.name}/requests/"
    if gitignore_path.exists():
        content = gitignore_path.read_text(encoding="utf-8")
        if ignore_entry not in content and "requests/" not in content:
            with gitignore_path.open("a", encoding="utf-8") as f:
                if not content.endswith("\n") and len(content) > 0:
                    f.write("\n")
                f.write(f"# User requirement alignment history (human reference only)\n{ignore_entry}\n")
            print(f"UPDATE  {gitignore_path} (added {ignore_entry})")
    else:
        gitignore_path.write_text(f"# User requirement alignment history (human reference only)\n{ignore_entry}\n", encoding="utf-8")
        print(f"CREATE  {gitignore_path} (added {ignore_entry})")

    for path in created:
        print(f"CREATE  {path}")
    for path in existing:
        print(f"SKIP    {path} (already exists)")

    # Advise reverse-engineering if codebase already exists
    root = Path.cwd()
    if detect_existing_code(root):
        print("\n[NOTE] Existing codebase detected!")
        print("Recommendation: Document the existing baseline before implementing new features.")
        print("1. Populate docs/context.md with terms found in code.")
        print("2. Outline docs/architecture.md based on current code structure.")
        print("3. Reverse-engineer existing core features into docs/features/.")

    print("\nNext: Update docs/context.md and docs/features/ as features are designed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
