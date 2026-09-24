#!/usr/bin/env python3
"""Create a new document with the next free number in a docs subfolder.

Allocates the next zero-padded NNN in docs/<subfolder>/ and writes a file with
the standard header block, so numbering stays unique without manual bookkeeping.

Usage:
    python scripts/new_doc.py <subfolder> <kebab-name> [--docs docs] [--title TITLE] [--status Draft]

Example:
    python scripts/new_doc.py product 004-notification-rules --title "Notification Rules"
"""

import argparse
import re
import sys
from pathlib import Path

SUBFOLDER_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
NUMBERED_RE = re.compile(r"^(\d{3})-")
VALID_STATUS = ("Draft", "Active")


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
    parser.add_argument("subfolder", help="registered docs subfolder, e.g. product, architecture")
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
    number = next_number(subfolder_dir)
    filename = f"{number:03d}-{name}.md"
    path = subfolder_dir / filename

    if path.exists():
        print(f"FAIL  {path} already exists", file=sys.stderr)
        return 1

    title = args.title or " ".join(word.capitalize() for word in name.split("-"))
    content = f"# {title}\n\n**Document Version**: 0.1.0\n**Status**: {args.status}\n\n"

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

    print(f"CREATE  {path}")
    print(f"\nNext: fill in the document and add it to {docs}/README.md.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
