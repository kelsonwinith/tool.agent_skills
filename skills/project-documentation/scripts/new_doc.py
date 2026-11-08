#!/usr/bin/env python3
"""Create a new document with the next free number in a docs subfolder.

Allocates the next zero-padded NNN in docs/<subfolder>/ and writes a file with
the standard template (including Mermaid flowchart and cross-feature conflict check
for features).

Usage:
    python scripts/new_doc.py <subfolder> <kebab-name> [--docs docs] [--title TITLE] [--status Draft]

Example:
    python scripts/new_doc.py features user-authentication --title "User Authentication"
"""

import argparse
import datetime
import re
import sys
from pathlib import Path

SUBFOLDER_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
NUMBERED_RE = re.compile(r"^(\d{3})-")
VALID_STATUS = ("Draft", "Active")

FEATURE_TEMPLATE = """# {number}: {title}

**Document Version**: 0.1.0  
**Status**: {status}  
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
- **FR-001**: [Primary functional requirement]
- **FR-002**: [Secondary requirement or constraint]

## 4. Cross-Feature Conflict & Overlap Check
- **Dependencies**: Relies on `context.md` concepts.
- **Potential Overlaps**: [List related features under docs/features/]
- **Collision Analysis**: [Verify no contradictory business rules or state conflicts]
"""

DECISION_TEMPLATE = """# ADR-{number}: {title}

## Status
{status}

## Context
[What problem are we solving? What are the constraints, requirements, and background?]

## Decision
[What is the change/choice being made? What technology, pattern, or architecture is selected?]

## Alternatives Considered
- **Option 1**: [Description and why it was rejected]
- **Option 2**: [Description and why it was rejected]

## Consequences
- **Positive**: [Benefits, simplifications, performance improvements]
- **Negative / Trade-offs**: [Complexity, migration cost, limitations]
"""

GENERIC_TEMPLATE = """# {title}

**Document Version**: 0.1.0  
**Status**: {status}  
**Last Modified**: {date}

## Overview
[Description of {title}]
"""


def next_number(subfolder_dir: Path) -> int:
    highest = 0
    if subfolder_dir.is_dir():
        for path in subfolder_dir.glob("*.md"):
            match = NUMBERED_RE.match(path.name)
            if match:
                highest = max(highest, int(match.group(1)))
    return highest + 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("subfolder", help="registered docs subfolder (e.g. features, decisions)")
    parser.add_argument("name", help="kebab-case document name, without the number or .md")
    parser.add_argument("--docs", default="docs", help="path to the docs directory (default: docs)")
    parser.add_argument("--title", default=None, help="document title (default: derived from the name)")
    parser.add_argument("--status", default="Draft", choices=VALID_STATUS, help="initial status (default: Draft)")
    args = parser.parse_args()

    if not SUBFOLDER_RE.match(args.subfolder):
        print(f"FAIL  subfolder '{args.subfolder}' must be lowercase kebab-case", file=sys.stderr)
        return 1

    name = re.sub(r"^\d{3}-", "", args.name)
    if not NAME_RE.match(name):
        print(f"FAIL  name '{args.name}' must be lowercase kebab-case (no number, no .md)", file=sys.stderr)
        return 1

    docs = Path(args.docs)
    subfolder_dir = docs / args.subfolder
    number_val = next_number(subfolder_dir)
    number_str = f"{number_val:03d}"
    filename = f"{number_str}-{name}.md"
    path = subfolder_dir / filename

    if path.exists():
        print(f"FAIL  {path} already exists", file=sys.stderr)
        return 1

    title = args.title or " ".join(word.capitalize() for word in name.split("-"))
    today = datetime.date.today().isoformat()

    if args.subfolder == "features":
        content = FEATURE_TEMPLATE.format(
            number=number_str,
            title=title,
            status=args.status,
            date=today,
        )
    elif args.subfolder == "decisions":
        content = DECISION_TEMPLATE.format(
            number=number_str,
            title=title,
            status="Proposed" if args.status == "Draft" else "Accepted",
        )
    else:
        content = GENERIC_TEMPLATE.format(
            title=title,
            status=args.status,
            date=today,
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

    print(f"CREATE  {path}")
    print(f"\nNext: fill in the document details, flowchart, and verify conflict check against existing features.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
