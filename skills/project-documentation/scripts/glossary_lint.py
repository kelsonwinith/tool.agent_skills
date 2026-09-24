#!/usr/bin/env python3
"""Validate a canonical-context glossary (ubiquitous language).

Expected format (see SKILL.md):

    # <Project / Context Name>

    ## Language

    | Term | Meaning | Avoid |
    | :--- | :--- | :--- |
    | Order | A request from a customer to buy one or more items. | Purchase, transaction |

Checks:
  1. A '## Language' section with a Term/Meaning/Avoid table exists.
  2. Every term has a non-empty meaning of one or two sentences.
  3. No duplicate terms.
  4. Optionally, with --scan, flags 'Avoid' synonyms that still appear elsewhere.

Usage:
    python scripts/glossary_lint.py [glossary.md] [--scan PATH ...]

With no path, discovers docs/context/*.md (excluding *context-map*).
Exit code is 1 when any FAIL is reported, 0 otherwise.
"""

import argparse
import re
import sys
from pathlib import Path

LANGUAGE_RE = re.compile(r"^#{1,3}\s+Language\b", re.IGNORECASE | re.MULTILINE)
MAX_MEANING_CHARS = 300
SKIP_DIRS = {".git", "node_modules", ".next", "dist", "build", "vendor", "__pycache__"}
TEXT_SUFFIXES = {".md", ".txt", ".ts", ".tsx", ".js", ".jsx", ".py", ".go", ".rs", ".java", ".rb"}


def split_row(line):
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def is_separator(cells):
    return bool(cells) and all(re.fullmatch(r":?-{2,}:?", cell) for cell in cells if cell != "")


def parse_terms(text):
    """Return a list of (term, meaning, [synonyms]) from the Language table."""
    terms = []
    columns = None  # {"term": i, "meaning": i, "avoid": i}

    for raw in text.splitlines():
        line = raw.strip()
        if not line.startswith("|"):
            continue
        cells = split_row(line)
        if is_separator(cells):
            continue
        lowered = [c.lower() for c in cells]
        if columns is None and "meaning" in lowered and ("term" in lowered or "language" in lowered):
            term_key = "term" if "term" in lowered else "language"
            columns = {
                "term": lowered.index(term_key),
                "meaning": lowered.index("meaning"),
                "avoid": lowered.index("avoid") if "avoid" in lowered else None,
            }
            continue
        if columns is None:
            continue
        def cell(key):
            idx = columns.get(key)
            return cells[idx] if idx is not None and idx < len(cells) else ""
        term = cell("term")
        meaning = cell("meaning")
        avoid = cell("avoid")
        synonyms = [s.strip() for s in avoid.split(",") if s.strip()]
        if term or meaning:
            terms.append((term, meaning, synonyms))

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
            if path.suffix.lower() not in TEXT_SUFFIXES:
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
        if re.search(r"\|\s*(term|language)\s*\|[^\n]*meaning", text, re.IGNORECASE):
            warnings.append(f"{path}: term table has no rows yet")
        else:
            failures.append(
                f"{path}: no term table found — expected a '| Term | Meaning | Avoid |' table under '## Language'"
            )

    seen = {}
    all_synonyms = []
    for term, meaning, synonyms in terms:
        key = term.lower()
        if key in seen:
            failures.append(f"{path}: duplicate term '{term}' (also defined as '{seen[key]}')")
        else:
            seen[key] = term
        if not meaning:
            failures.append(f"{path}: term '{term}' has no meaning")
        elif len(meaning) > MAX_MEANING_CHARS:
            warnings.append(
                f"{path}: meaning for '{term}' is {len(meaning)} chars (keep it to one or two sentences)"
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
