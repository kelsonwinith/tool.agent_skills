#!/usr/bin/env python3
"""Validate a canonical-context glossary (ubiquitous language).

Expected format (see SKILL.md):

    # <Project / Context Name>

    ## Language

    **Order**:
    A request from a customer to buy one or more items.
    _Avoid_: Purchase, transaction

Checks:
  1. A '## Language' section exists.
  2. Every term has a non-empty definition of one or two sentences.
  3. No duplicate terms.
  4. Optionally, with --scan, flags '_Avoid_' synonyms that still appear elsewhere.

Usage:
    python scripts/glossary_lint.py [glossary.md] [--scan PATH ...]

With no path, discovers docs/context/*.md (excluding *context-map*).
Exit code is 1 when any FAIL is reported, 0 otherwise.
"""

import argparse
import re
import sys
from pathlib import Path

TERM_RE = re.compile(r"^\*\*(.+?)\*\*:\s*(.*)$")
AVOID_RE = re.compile(r"^_Avoid_:\s*(.*)$", re.IGNORECASE)
LANGUAGE_RE = re.compile(r"^#{1,3}\s+Language\b", re.IGNORECASE | re.MULTILINE)
MAX_DEFINITION_CHARS = 300
SKIP_DIRS = {".git", "node_modules", ".next", "dist", "build", "vendor", "__pycache__"}


def parse_terms(text):
    """Return a list of (term, definition, [synonyms]) preserving order."""
    terms = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        match = TERM_RE.match(lines[i].strip())
        if not match:
            i += 1
            continue
        term = match.group(1).strip()
        definition = match.group(2).strip()
        synonyms = []
        j = i + 1
        while j < len(lines) and not TERM_RE.match(lines[j].strip()):
            stripped = lines[j].strip()
            avoid = AVOID_RE.match(stripped)
            if avoid:
                synonyms = [s.strip() for s in avoid.group(1).split(",") if s.strip()]
            elif stripped and not definition and not stripped.startswith("#"):
                definition = stripped
            j += 1
        terms.append((term, definition, synonyms))
        i = j
    return terms


def discover_glossary(explicit):
    if explicit:
        return [Path(explicit)]
    context_dir = Path("docs/context")
    if not context_dir.is_dir():
        return []
    return [p for p in sorted(context_dir.glob("*.md")) if "context-map" not in p.name.lower()]


def scan_for_synonyms(synonyms, scan_paths, glossary_path):
    hits = []
    lowered = {s.lower(): s for s in synonyms}
    if not lowered:
        return hits
    pattern = re.compile(r"\b(" + "|".join(re.escape(s) for s in lowered) + r")\b", re.IGNORECASE)
    for root in scan_paths:
        root_path = Path(root)
        files = [root_path] if root_path.is_file() else sorted(root_path.rglob("*"))
        for path in files:
            if not path.is_file() or path == glossary_path:
                continue
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            if path.suffix.lower() not in {".md", ".txt", ".ts", ".tsx", ".js", ".jsx", ".py", ".go", ".rs", ".java", ".rb"}:
                continue
            try:
                for lineno, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                    found = pattern.search(line)
                    if found:
                        hits.append((lowered[found.group(1).lower()], f"{path}:{lineno}"))
            except OSError:
                continue
    return hits


def lint(path: Path, scan_paths):
    failures = []
    warnings = []

    if not path.is_file():
        return [f"{path}: glossary not found"], []

    text = path.read_text(encoding="utf-8", errors="replace")

    if not LANGUAGE_RE.search(text):
        warnings.append(f"{path}: no '## Language' section found")

    terms = parse_terms(text)
    if not terms:
        warnings.append(f"{path}: no terms found")

    seen = {}
    all_synonyms = []
    for term, definition, synonyms in terms:
        key = term.lower()
        if key in seen:
            failures.append(f"{path}: duplicate term '{term}' (also defined as '{seen[key]}')")
        else:
            seen[key] = term
        if not definition:
            failures.append(f"{path}: term '{term}' has no definition")
        elif len(definition) > MAX_DEFINITION_CHARS:
            warnings.append(
                f"{path}: definition for '{term}' is {len(definition)} chars "
                f"(keep it to one or two sentences)"
            )
        all_synonyms.extend(synonyms)

    for synonym, location in scan_for_synonyms(all_synonyms, scan_paths, path):
        warnings.append(f"{location}: uses avoided synonym '{synonym}' — prefer the canonical term")

    return failures, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("glossary", nargs="?", help="path to the glossary markdown file")
    parser.add_argument("--scan", nargs="*", default=[], help="paths to scan for avoided synonyms")
    args = parser.parse_args()

    glossary_files = discover_glossary(args.glossary)
    if not glossary_files:
        print("WARN  no glossary found (looked for docs/context/*.md)")
        return 0

    all_failures = []
    all_warnings = []
    for path in glossary_files:
        failures, warnings = lint(path, [Path(p) for p in args.scan])
        all_failures.extend(failures)
        all_warnings.extend(warnings)

    for warning in all_warnings:
        print(f"WARN  {warning}")
    for failure in all_failures:
        print(f"FAIL  {failure}")

    if all_failures:
        print(f"\nFAIL: {len(all_failures)} error(s), {len(all_warnings)} warning(s)")
        return 1
    print(f"\nPASS: glossary is valid ({len(all_warnings)} warning(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
