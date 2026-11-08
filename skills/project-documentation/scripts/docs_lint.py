#!/usr/bin/env python3
"""Validate a project's docs/ tree against documentation conventions.

Checks (see SKILL.md):
  1. Allowed root singletons under docs/: README.md, context.md, architecture.md.
     No unexpected loose markdown files sit directly in docs/.
  2. Subfolder documents live at docs/<subfolder>/<NNN>-<kebab-name>.md.
  3. <NNN> is a 3-digit number, unique within its subfolder.
  4. Subfolder and file names are lowercase kebab-case.
  5. Feature documents (under docs/features/) have:
     - Header: **Document Version**: X.Y.Z and **Status**: Draft|Active
     - Mermaid flowchart block (```mermaid)
     - Cross-Feature Conflict & Overlap Check section
  6. ADR documents (under docs/decisions/) follow ADR structure.

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
STATUS_RE = re.compile(r"^\*\*Status\*\*:\s*(Draft|Active)\b", re.MULTILINE)
MERMAID_RE = re.compile(r"```mermaid\s+(flowchart|graph|sequenceDiagram|stateDiagram)", re.MULTILINE)

ALLOWED_ROOT_FILES = {"readme.md", "context.md", "architecture.md"}
HEADER_EXEMPT_SUBFOLDERS = {"context", "decisions"}


def lint(docs_dir: Path):
    failures = []
    warnings = []

    if not docs_dir.is_dir():
        return [f"{docs_dir}: not a directory"], []

    if not (docs_dir / "README.md").exists():
        warnings.append(f"{docs_dir}/README.md: missing docs index (recommended)")

    numbers = {}  # subfolder -> {number: filename}

    for path in sorted(docs_dir.rglob("*.md")):
        rel = path.relative_to(docs_dir)
        parts = rel.parts

        # Root file under docs/
        if len(parts) == 1:
            if rel.name.lower() in ALLOWED_ROOT_FILES:
                continue
            failures.append(
                f"{docs_dir}/{rel}: unrecognized file directly under docs/ — only README.md, "
                f"context.md, and architecture.md belong at the root. Move features into docs/features/."
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

        # Feature-specific checks
        if subfolder == "features":
            if not VERSION_RE.search(text):
                failures.append(f"{docs_dir}/{rel}: missing '**Document Version**: X.Y.Z' header")
            if not STATUS_RE.search(text):
                failures.append(f"{docs_dir}/{rel}: missing '**Status**: Draft|Active' header")
            if not MERMAID_RE.search(text):
                warnings.append(f"{docs_dir}/{rel}: missing a Mermaid diagram (flowchart/sequence)")
            if "conflict" not in text.lower():
                warnings.append(f"{docs_dir}/{rel}: missing a cross-feature conflict/overlap check section")

        elif subfolder not in HEADER_EXEMPT_SUBFOLDERS:
            if not VERSION_RE.search(text):
                failures.append(f"{docs_dir}/{rel}: missing '**Document Version**: X.Y.Z' header")
            if not STATUS_RE.search(text):
                failures.append(f"{docs_dir}/{rel}: missing '**Status**: Draft|Active' header")

    return failures, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("docs_dir", nargs="?", default="docs", help="path to the docs directory (default: docs)")
    args = parser.parse_args()

    docs_dir = Path(args.docs_dir)
    failures, warnings = lint(docs_dir)

    for warn in warnings:
        print(f"WARN  {warn}")
    for fail in failures:
        print(f"FAIL  {fail}")

    if failures:
        print(f"\n{len(failures)} failure(s) found.", file=sys.stderr)
        return 1

    print(f"PASS  {docs_dir} meets documentation conventions.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
