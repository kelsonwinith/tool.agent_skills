#!/usr/bin/env python3
"""Create a new numbered document in docs/flows/ or docs/decisions/.

Allocates the next zero-padded NNN in docs/<subfolder>/ and writes a file with
the structured Flow template (for `flows`) or ADR template (for `decisions`).

Usage:
    python scripts/new_doc.py <flows|decisions> <kebab-name> [--docs docs] [--title TITLE] [--status Draft]

Examples:
    python scripts/new_doc.py flows create-order --title "Create Order"
    python scripts/new_doc.py decisions store-orders-in-memory --title "Store orders in memory"
"""

import argparse
import re
import sys
from pathlib import Path

VALID_SUBFOLDERS = ("flows", "decisions")
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
NUMBERED_RE = re.compile(r"^(\d{3})-")
VALID_FLOW_STATUS = ("Draft", "Active")
VALID_ADR_STATUS = ("Proposed", "Accepted", "Deprecated", "Superseded")

FLOW_TEMPLATE = """# {title}

**Document Version**: 0.1.0
**Status**: {status}

## Overview & Actor

<!-- Who triggers this flow and what goal does it achieve? -->

## Business Rules

<!-- Rules and invariants enforced during this flow. -->

## Flow Steps

<!-- Step-by-step sequence (or Mermaid diagram) from trigger to completion. -->

## Edge Cases & Errors

<!-- Validation failures, conflict states, and recovery behavior. -->
"""

ADR_TEMPLATE = """# ADR-{number:03d}: {title}

## Status
{status}

## Context
<!-- What problem are we solving? What are the constraints and background? -->

## Decision
<!-- What technology, pattern, or architectural choice is being made? -->

## Alternatives Considered
- **Option 1**: <!-- Description and why it was rejected -->

## Consequences
- **Positive**: <!-- Benefits and simplifications -->
- **Negative / Trade-offs**: <!-- Complexity, migration cost, or limitations -->
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
    parser.add_argument("subfolder", help="numbered collection subfolder: 'flows' or 'decisions'")
    parser.add_argument("name", help="kebab-case document name, without the number or .md")
    parser.add_argument("--docs", default="docs", help="path to the docs directory (default: docs)")
    parser.add_argument("--title", default=None, help="document title (default: derived from the name)")
    parser.add_argument("--status", default=None, help="initial status (Draft|Active for flows, Proposed|Accepted for decisions)")
    args = parser.parse_args()

    if args.subfolder not in VALID_SUBFOLDERS:
        print(
            f"FAIL  subfolder '{args.subfolder}' must be one of: {', '.join(VALID_SUBFOLDERS)} "
            f"(singletons like product.md or ubiquitous-language.md live at the docs/ root without numbers)",
            file=sys.stderr,
        )
        return 1

    name = re.sub(r"^\d{3}-", "", args.name)
    if not NAME_RE.match(name):
        print(f"FAIL  name '{args.name}' must be lowercase kebab-case (no number, no .md)", file=sys.stderr)
        return 1

    docs = Path(args.docs)
    subfolder_dir = docs / args.subfolder
    number = next_number(subfolder_dir)
    filename = f"{number:03d}-{name}.md"
    path = subfolder_dir / filename

    if path.exists():
        print(f"FAIL  {path} already exists", file=sys.stderr)
        return 1

    title = args.title or " ".join(word.capitalize() for word in name.split("-"))

    if args.subfolder == "flows":
        status = args.status or "Draft"
        if status not in VALID_FLOW_STATUS:
            print(f"FAIL  flow status '{status}' must be one of {VALID_FLOW_STATUS}", file=sys.stderr)
            return 1
        content = FLOW_TEMPLATE.format(title=title, status=status)
    else:
        status = args.status or "Accepted"
        if status not in VALID_ADR_STATUS:
            print(f"FAIL  ADR status '{status}' must be one of {VALID_ADR_STATUS}", file=sys.stderr)
            return 1
        content = ADR_TEMPLATE.format(number=number, title=title, status=status)

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

    keep = subfolder_dir / ".gitkeep"
    if keep.exists():
        keep.unlink()

    print(f"CREATE  {path}")
    print(f"\nNext: fill in the document and link it in {docs}/README.md.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
