#!/usr/bin/env python3
"""Validate a project's docs/ tree against the numbered documentation convention.

Checks (see SKILL.md):
  1. Every markdown file lives at docs/<subfolder>/<NNN>-<kebab-name>.md.
  2. No ad-hoc markdown files sit directly under docs/ (except docs/README.md).
  3. <NNN> is a 3-digit number, unique within its subfolder.
  4. Subfolder and file names are lowercase kebab-case.
  5. Every document (except the index) opens with the header block:
     **Document Version**: X.Y.Z and **Status**: Draft|Active|Deprecated.

Usage:
    python scripts/docs_lint.py [docs_dir]   # docs_dir defaults to "docs"

Exit code is 1 when any FAIL is reported, 0 otherwise.
"""

import argparse
import re
import sys
from pathlib import Path

SUBFOLDER_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FILENAME_RE = re.compile(r"^(\d{3})-([a-z0-9]+(?:-[a-z0-9]+)*)\.md$")
VERSION_RE = re.compile(r"^\*\*Document Version\*\*:\s*\S+", re.MULTILINE)
STATUS_RE = re.compile(r"^\*\*Status\*\*:\s*(Draft|Active|Deprecated)\b", re.MULTILINE)

IGNORED_ROOT_FILES = {"readme.md"}
# The canonical-context glossary and ADR records have their own formats
# (see SKILL.md) and are not required to carry a version header.
HEADER_EXEMPT_SUBFOLDERS = {"context", "decisions"}


def lint(docs_dir: Path):
    failures = []
    warnings = []

    if not docs_dir.is_dir():
        return [f"{docs_dir}: not a directory"], []

    if not (docs_dir / "README.md").exists():
        warnings.append(f"{docs_dir}/README.md: missing docs index (optional but recommended)")

    numbers = {}  # subfolder -> {number: filename}

    for path in sorted(docs_dir.rglob("*.md")):
        rel = path.relative_to(docs_dir)
        parts = rel.parts

        if len(parts) == 1:
            if rel.name.lower() in IGNORED_ROOT_FILES:
                continue
            failures.append(
                f"{docs_dir}/{rel}: file sits directly under docs/ — move it into a "
                f"registered subfolder as <NNN>-<kebab-name>.md"
            )
            continue

        if len(parts) != 2:
            failures.append(f"{docs_dir}/{rel}: expected docs/<subfolder>/<NNN>-<name>.md")

        subfolder, filename = parts[0], parts[-1]

        if not SUBFOLDER_RE.match(subfolder):
            failures.append(f"{docs_dir}/{rel}: subfolder '{subfolder}' is not kebab-case")

        match = FILENAME_RE.match(filename)
        if not match:
            failures.append(
                f"{docs_dir}/{rel}: filename must be <NNN>-<kebab-name>.md "
                f"(3-digit number, lowercase kebab-case)"
            )
            continue

        number = match.group(1)
        numbers.setdefault(subfolder, {})
        if number in numbers[subfolder]:
            failures.append(
                f"{docs_dir}/{rel}: number {number} already used by "
                f"{numbers[subfolder][number]} in '{subfolder}/'"
            )
        else:
            numbers[subfolder][number] = filename

        text = path.read_text(encoding="utf-8", errors="replace")
        if subfolder not in HEADER_EXEMPT_SUBFOLDERS:
            if not VERSION_RE.search(text):
                failures.append(f"{docs_dir}/{rel}: missing '**Document Version**: X.Y.Z' header")
            if not STATUS_RE.search(text):
                failures.append(
                    f"{docs_dir}/{rel}: missing '**Status**: Draft|Active|Deprecated' header"
                )

    return failures, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("docs_dir", nargs="?", default="docs", help="path to the docs directory (default: docs)")
    args = parser.parse_args()

    failures, warnings = lint(Path(args.docs_dir))

    for warning in warnings:
        print(f"WARN  {warning}")
    for failure in failures:
        print(f"FAIL  {failure}")

    if failures:
        print(f"\nFAIL: {len(failures)} error(s), {len(warnings)} warning(s)")
        return 1
    print(f"\nPASS: docs tree is valid ({len(warnings)} warning(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
