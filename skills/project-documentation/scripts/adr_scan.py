#!/usr/bin/env python3
"""Validate Architecture Decision Records under a decisions directory.

Checks (see SKILL.md):
  1. ADR headings follow '# ADR-<NNN>: <title>'.
  2. ADR IDs are unique and sequential (ADR-001, ADR-002, ...); gaps are flagged.
  3. Each ADR has Status, Context, Decision, and Consequences sections.
  4. Status is one of Proposed | Accepted | Deprecated | Superseded.

Usage:
    python scripts/adr_scan.py [decisions_dir]   # defaults to docs/decisions

Exit code is 1 when any FAIL is reported, 0 otherwise.
"""

import argparse
import re
import sys
from pathlib import Path

ADR_RE = re.compile(r"^#\s+ADR-(\d+):\s*(.*)$")
SECTION_RE = re.compile(r"^##\s+(.+?)\s*$")
REQUIRED_SECTIONS = ["status", "context", "decision", "consequences"]
VALID_STATUS = ("proposed", "accepted", "deprecated", "superseded")


def parse_adrs(path: Path):
    """Yield (adr_id, title, block_lines, line_number) for each ADR in a file."""
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    starts = []
    for idx, line in enumerate(lines):
        match = ADR_RE.match(line.strip())
        if match:
            starts.append((idx, int(match.group(1)), match.group(2).strip()))
    for pos, (idx, adr_id, title) in enumerate(starts):
        end = starts[pos + 1][0] if pos + 1 < len(starts) else len(lines)
        yield adr_id, title, lines[idx:end], idx + 1


def lint(decisions_dir: Path):
    failures = []
    warnings = []

    if not decisions_dir.is_dir():
        return [], [f"{decisions_dir}: directory not found (no ADRs recorded yet)"]

    found = []  # (adr_id, file, line)
    for path in sorted(decisions_dir.rglob("*.md")):
        for adr_id, title, block, line_number in parse_adrs(path):
            found.append((adr_id, path, line_number))
            if not title:
                warnings.append(f"{path}:{line_number}: ADR-{adr_id:03d} has no title")

            sections = {}
            for offset, raw in enumerate(block[1:], start=1):
                match = SECTION_RE.match(raw)
                if match:
                    sections[match.group(1).strip().lower()] = offset

            for required in REQUIRED_SECTIONS:
                if required not in sections:
                    failures.append(
                        f"{path}:{line_number}: ADR-{adr_id:03d} is missing a '## {required.title()}' section"
                    )

            status_index = sections.get("status")
            if status_index is not None:
                for raw in block[status_index + 1:]:
                    value = raw.strip()
                    if not value:
                        continue
                    if not value.lower().startswith(VALID_STATUS):
                        warnings.append(
                            f"{path}:{line_number}: ADR-{adr_id:03d} status '{value}' is not one of "
                            f"{', '.join(s.title() for s in VALID_STATUS)}"
                        )
                    break

    if not found:
        warnings.append(f"{decisions_dir}: no ADRs found")
        return failures, warnings

    seen = {}
    for adr_id, path, line_number in found:
        if adr_id in seen:
            failures.append(
                f"{path}:{line_number}: duplicate ADR-{adr_id:03d} "
                f"(already used in {seen[adr_id]})"
            )
        else:
            seen[adr_id] = f"{path}:{line_number}"

    expected = 1
    for adr_id in sorted(seen):
        if adr_id < expected:
            continue
        if adr_id != expected:
            warnings.append(
                f"ADR numbering gap: expected ADR-{expected:03d}, next found ADR-{adr_id:03d}"
            )
        expected = adr_id + 1

    return failures, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("decisions_dir", nargs="?", default="docs/decisions", help="path to the decisions directory (default: docs/decisions)")
    args = parser.parse_args()

    failures, warnings = lint(Path(args.decisions_dir))

    for warning in warnings:
        print(f"WARN  {warning}")
    for failure in failures:
        print(f"FAIL  {failure}")

    if failures:
        print(f"\nFAIL: {len(failures)} error(s), {len(warnings)} warning(s)")
        return 1
    print(f"\nPASS: ADRs are valid ({len(warnings)} warning(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
