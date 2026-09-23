#!/usr/bin/env python3
"""Regression tests for the bundled documentation scripts.

Run:  python scripts/tests/test_scripts.py
Uses only the standard library (unittest + subprocess)."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent


def run(script, *args):
    return subprocess.run(
        [sys.executable, str(SCRIPTS / script), *args],
        capture_output=True,
        text=True,
    )


class InitAndLintTests(unittest.TestCase):
    def test_init_creates_tree_and_lint_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp) / "docs"
            result = run("init_docs.py", "--docs", str(docs), "--context-name", "Orders")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((docs / "README.md").exists())
            self.assertTrue((docs / "context/001-ubiquitous-language.md").exists())
            for sub in ("product", "architecture", "decisions", "development"):
                self.assertTrue((docs / sub).is_dir())

            lint = run("docs_lint.py", str(docs))
            self.assertEqual(lint.returncode, 0, lint.stdout + lint.stderr)

    def test_docs_lint_flags_root_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp) / "docs"
            docs.mkdir()
            (docs / "loose.md").write_text("# Loose\n")
            lint = run("docs_lint.py", str(docs))
            self.assertEqual(lint.returncode, 1)
            self.assertIn("directly under docs/", lint.stdout)


class NewDocTests(unittest.TestCase):
    def test_allocates_sequential_numbers(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp) / "docs"
            run("init_docs.py", "--docs", str(docs))
            for name in ("001-alpha", "002-beta", "003-gamma"):
                result = run("new_doc.py", "product", name, "--docs", str(docs))
                self.assertEqual(result.returncode, 0, result.stderr)
            names = sorted(p.name for p in (docs / "product").glob("*.md"))
            self.assertEqual(names, ["001-alpha.md", "002-beta.md", "003-gamma.md"])
            self.assertIn("**Document Version**", (docs / "product/001-alpha.md").read_text())

    def test_rejects_bad_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run("new_doc.py", "product", "Bad_Name", "--docs", str(Path(tmp) / "docs"))
            self.assertEqual(result.returncode, 1)


class GlossaryLintTests(unittest.TestCase):
    def _write(self, tmp, body):
        path = Path(tmp) / "docs/context/001-ubiquitous-language.md"
        path.parent.mkdir(parents=True)
        path.write_text(body)
        return path

    def test_valid_glossary_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(tmp, "# C\n\n## Language\n\n**Order**:\nA request to buy.\n_Avoid_: Purchase\n")
            self.assertEqual(run("glossary_lint.py", str(path)).returncode, 0)

    def test_duplicate_term_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(tmp, "# C\n\n## Language\n\n**Order**:\nA.\n\n**Order**:\nB.\n")
            self.assertEqual(run("glossary_lint.py", str(path)).returncode, 1)

    def test_missing_definition_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(tmp, "# C\n\n## Language\n\n**Order**:\n\n**Invoice**:\nA bill.\n")
            result = run("glossary_lint.py", str(path))
            self.assertEqual(result.returncode, 1)
            self.assertIn("no definition", result.stdout)


class AdrScanTests(unittest.TestCase):
    def test_missing_section_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            decisions = Path(tmp) / "docs/decisions"
            decisions.mkdir(parents=True)
            (decisions / "001-decisions.md").write_text(
                "# ADR-001: X\n\n## Status\nAccepted\n\n## Context\nc\n\n## Decision\nd\n"
            )
            result = run("adr_scan.py", str(decisions))
            self.assertEqual(result.returncode, 1)
            self.assertIn("Consequences", result.stdout)

    def test_valid_adr_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            decisions = Path(tmp) / "docs/decisions"
            decisions.mkdir(parents=True)
            (decisions / "001-decisions.md").write_text(
                "# ADR-001: X\n\n## Status\nAccepted\n\n## Context\nc\n\n## Decision\nd\n\n## Consequences\ne\n"
            )
            self.assertEqual(run("adr_scan.py", str(decisions)).returncode, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
