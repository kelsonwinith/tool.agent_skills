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
            result = run("init_docs.py", "--docs", str(docs), "--project-name", "Orders")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((docs / "README.md").exists())
            self.assertTrue((docs / "context.md").exists())
            self.assertTrue((docs / "architecture.md").exists())
            self.assertTrue((docs / "features").is_dir())
            self.assertTrue((docs / "features/001-example-feature.md").exists())
            self.assertTrue((docs / "decisions").is_dir())
            gitignore = Path(tmp) / ".gitignore"
            self.assertTrue(gitignore.exists())
            self.assertIn("docs/SUMMARY.md", gitignore.read_text())

            lint = run("docs_lint.py", str(docs))
            self.assertEqual(lint.returncode, 0, lint.stdout + lint.stderr)

    def test_docs_lint_flags_unauthorized_root_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp) / "docs"
            docs.mkdir()
            (docs / "loose.md").write_text("# Loose\n")
            lint = run("docs_lint.py", str(docs))
            self.assertEqual(lint.returncode, 1)
            self.assertIn("unrecognized file directly under docs/", lint.stdout)

    def test_docs_lint_allows_standard_root_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp) / "docs"
            docs.mkdir()
            (docs / "README.md").write_text("# Readme\n")
            (docs / "context.md").write_text("# Context\n")
            (docs / "architecture.md").write_text("# Architecture\n")
            lint = run("docs_lint.py", str(docs))
            self.assertEqual(lint.returncode, 0, lint.stdout + lint.stderr)


class NewDocTests(unittest.TestCase):
    def test_allocates_sequential_numbers_for_features(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp) / "docs"
            run("init_docs.py", "--docs", str(docs))
            for name in ("auth", "checkout"):
                result = run("new_doc.py", "features", name, "--docs", str(docs))
                self.assertEqual(result.returncode, 0, result.stderr)
            feature_files = sorted(p.name for p in (docs / "features").glob("*.md"))
            # 001-example-feature.md was created by init_docs, followed by 002-auth, 003-checkout
            self.assertEqual(feature_files, ["001-example-feature.md", "002-auth.md", "003-checkout.md"])

            feature_text = (docs / "features/002-auth.md").read_text()
            self.assertIn("**Document Version**", feature_text)
            self.assertIn("```mermaid", feature_text)
            self.assertIn("Conflict & Overlap Check", feature_text)

    def test_rejects_bad_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run("new_doc.py", "features", "Bad_Name", "--docs", str(Path(tmp) / "docs"))
            self.assertEqual(result.returncode, 1)


class GlossaryLintTests(unittest.TestCase):
    def _write_root(self, tmp, body):
        path = Path(tmp) / "docs/context.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body)
        return path

    def test_valid_root_glossary_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write_root(
                tmp,
                "# C\n\n## Language\n\n| Term | Meaning | Avoid |\n| :--- | :--- | :--- |\n"
                "| Order | A request to buy. | Purchase |\n",
            )
            self.assertEqual(run("glossary_lint.py", str(path)).returncode, 0)

    def test_empty_table_warns_but_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write_root(tmp, "# C\n\n## Language\n\n| Term | Meaning | Avoid |\n| :--- | :--- | :--- |\n")
            result = run("glossary_lint.py", str(path))
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertIn("no rows yet", result.stdout)

    def test_duplicate_term_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write_root(
                tmp,
                "# C\n\n## Language\n\n| Term | Meaning | Avoid |\n| :--- | :--- | :--- |\n"
                "| Order | A. | |\n| Order | B. | |\n",
            )
            self.assertEqual(run("glossary_lint.py", str(path)).returncode, 1)

    def test_missing_meaning_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write_root(
                tmp,
                "# C\n\n## Language\n\n| Term | Meaning | Avoid |\n| :--- | :--- | :--- |\n"
                "| Order | | Purchase |\n",
            )
            result = run("glossary_lint.py", str(path))
            self.assertEqual(result.returncode, 1)
            self.assertIn("no meaning", result.stdout)


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
