#!/usr/bin/env python3
"""Validate a project's docs/ tree against the flat-singleton + numbered-collection layout.

Expected structure (see SKILL.md):
  docs/
  ├── README.md                              # Index
  ├── ubiquitous-language.md                 # Single-context glossary (or docs/context/*.md for multi-context)
  ├── product.md                             # Core product overview & global business rules
  ├── architecture.md                        # System architecture, code structure, data model & APIs
  ├── development.md                         # Setup, build, test, and verification commands
  ├── flows/
  │   └── <NNN>-<kebab-name>.md              # Numbered flows (with required sections)
  └── decisions/
      └── <NNN>-<kebab-name>.md              # Numbered ADRs (one file per ADR)

Checks:
  1. Only allowed singleton markdown files sit directly under docs/ (unnumbered):
     README.md, ubiquitous-language.md, product.md, architecture.md, development.md.
  2. Singleton docs product.md, architecture.md, and development.md carry the header:
     **Document Version**: X.Y.Z and **Status**: Draft|Active.
  3. Only allowed subfolders exist under docs/: `flows/`, `decisions/`, and optional `context/` (multi-context).
  4. Files in `flows/` and `decisions/` follow `<NNN>-<kebab-name>.md` with unique 3-digit numbers per folder.
  5. Every flow in `flows/<NNN>-<kebab-name>.md` has the version/status header and the 4 flow sections:
     `## Overview & Actor`, `## Business Rules`, `## Flow Steps`, `## Edge Cases & Errors`.
  6. Files in `context/` (multi-context mode) are unnumbered lowercase kebab-case (`<context-name>.md`).

Usage:
    python scripts/docs_lint.py [docs_dir]   # docs_dir defaults to "docs"

Exit code is 1 when any FAIL is reported, 0 otherwise.
"""

import argparse
import re
import sys
from pathlib import Path

NUMBERED_FILENAME_RE = re.compile(r"^(\d{3})-([a-z0-9]+(?:-[a-z0-9]+)*)\.md$")
UNNUMBERED_FILENAME_RE = re.compile(r"^([a-z0-9]+(?:-[a-z0-9]+)*)\.md$")
VERSION_RE = re.compile(r"^\*\*Document Version\*\*:\s*\S+", re.MULTILINE)
STATUS_RE = re.compile(r"^\*\*Status\*\*:\s*(Draft|Active)\b", re.MULTILINE)

ALLOWED_ROOT_FILES = {
    "README.md",
    "ubiquitous-language.md",
    "product.md",
    "architecture.md",
    "development.md",
}
HEADER_REQUIRED_ROOT_FILES = {"product.md", "architecture.md", "development.md"}

ALLOWED_SUBFOLDERS = {"flows", "decisions", "context"}
NUMBERED_SUBFOLDERS = {"flows", "decisions"}

REQUIRED_FLOW_SECTIONS = (
    "Overview & Actor",
    "Business Rules",
    "Flow Steps",
    "Edge Cases & Errors",
)


def check_version_header(text: str, rel_label: str, failures: list) -> None:
    if not VERSION_RE.search(text):
        failures.append(f"{rel_label}: missing '**Document Version**: X.Y.Z' header")
    if not STATUS_RE.search(text):
        failures.append(f"{rel_label}: missing '**Status**: Draft|Active' header")


def check_flow_sections(text: str, rel_label: str, failures: list) -> None:
    for section in REQUIRED_FLOW_SECTIONS:
        pattern = re.compile(rf"^##\s+{re.escape(section)}\s*$", re.MULTILINE)
        if not pattern.search(text):
            failures.append(f"{rel_label}: flow document missing '## {section}' section")


def lint(docs_dir: Path):
    failures = []
    warnings = []

    if not docs_dir.is_dir():
        return [f"{docs_dir}: not a directory"], []

    if not (docs_dir / "README.md").exists():
        warnings.append(f"{docs_dir}/README.md: missing docs index (optional but recommended)")

    has_root_glossary = (docs_dir / "ubiquitous-language.md").is_file()
    has_multi_context = (docs_dir / "context").is_dir() and any((docs_dir / "context").glob("*.md"))
    if not has_root_glossary and not has_multi_context:
        warnings.append(
            f"{docs_dir}: missing canonical glossary (expected docs/ubiquitous-language.md "
            f"or docs/context/<context>.md)"
        )
    elif has_root_glossary and has_multi_context:
        warnings.append(
            f"{docs_dir}: both docs/ubiquitous-language.md and docs/context/*.md exist — "
            f"use flat ubiquitous-language.md for single-context or docs/context/ for multi-context, not both"
        )

    numbers = {}  # subfolder -> {number: filename}

    for path in sorted(docs_dir.rglob("*.md")):
        rel = path.relative_to(docs_dir)
        parts = rel.parts
        rel_label = f"{docs_dir}/{rel}"
        text = path.read_text(encoding="utf-8", errors="replace")

        if len(parts) == 1:
            filename = parts[0]
            if filename not in ALLOWED_ROOT_FILES:
                failures.append(
                    f"{rel_label}: unexpected root file '{filename}' — allowed root files are "
                    f"{', '.join(sorted(ALLOWED_ROOT_FILES))}; flows belong in docs/flows/<NNN>-<name>.md "
                    f"and ADRs in docs/decisions/<NNN>-<name>.md"
                )
                continue
            if filename in HEADER_REQUIRED_ROOT_FILES:
                check_version_header(text, rel_label, failures)
            continue

        if len(parts) != 2:
            failures.append(f"{rel_label}: nested too deeply — expected docs/<file>.md or docs/<subfolder>/<file>.md")
            continue

        subfolder, filename = parts[0], parts[1]

        if subfolder not in ALLOWED_SUBFOLDERS:
            failures.append(
                f"{rel_label}: unknown subfolder '{subfolder}/' — allowed subfolders are "
                f"flows/, decisions/, and (for multi-context repos) context/"
            )
            continue

        if subfolder in NUMBERED_SUBFOLDERS:
            match = NUMBERED_FILENAME_RE.match(filename)
            if not match:
                failures.append(
                    f"{rel_label}: filename in '{subfolder}/' must be <NNN>-<kebab-name>.md "
                    f"(3-digit running number, lowercase kebab-case)"
                )
                continue

            number = match.group(1)
            numbers.setdefault(subfolder, {})
            if number in numbers[subfolder]:
                failures.append(
                    f"{rel_label}: number {number} already used by "
                    f"{numbers[subfolder][number]} in '{subfolder}/'"
                )
            else:
                numbers[subfolder][number] = filename

            if subfolder == "flows":
                check_version_header(text, rel_label, failures)
                check_flow_sections(text, rel_label, failures)

        elif subfolder == "context":
            if NUMBERED_FILENAME_RE.match(filename):
                failures.append(
                    f"{rel_label}: multi-context files in 'context/' must not use running numbers "
                    f"(use context-map.md and <context-name>.md)"
                )
            elif not UNNUMBERED_FILENAME_RE.match(filename):
                failures.append(
                    f"{rel_label}: filename in 'context/' must be lowercase kebab-case (<context-name>.md)"
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
