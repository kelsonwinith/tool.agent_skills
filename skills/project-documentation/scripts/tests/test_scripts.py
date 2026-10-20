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
    def test_init_creates_flat_singletons_and_numbered_folders_and_lint_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp) / "docs"
            result = run("init_docs.py", "--docs", str(docs), "--context-name", "Orders")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((docs / "README.md").exists())
            self.assertTrue((docs / "ubiquitous-language.md").exists())
            self.assertTrue((docs / "product.md").exists())
            self.assertTrue((docs / "architecture.md").exists())
            self.assertTrue((docs / "development.md").exists())
            for sub in ("flows", "decisions"):
                self.assertTrue((docs / sub).is_dir())

            lint = run("docs_lint.py", str(docs))
            self.assertEqual(lint.returncode, 0, lint.stdout + lint.stderr)

    def test_docs_lint_flags_unknown_root_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp) / "docs"
            run("init_docs.py", "--docs", str(docs))
            (docs / "loose.md").write_text("# Loose\n")
            lint = run("docs_lint.py", str(docs))
            self.assertEqual(lint.returncode, 1)
            self.assertIn("unexpected root file 'loose.md'", lint.stdout)

    def test_docs_lint_flags_numbered_context_file_in_multi_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp) / "docs"
            run("init_docs.py", "--docs", str(docs))
            (docs / "ubiquitous-language.md").unlink()
            ctx = docs / "context"
            ctx.mkdir()
            (ctx / "001-orders.md").write_text("# Orders\n\n## Language\n")
            lint = run("docs_lint.py", str(docs))
            self.assertEqual(lint.returncode, 1)
            self.assertIn("must not use running numbers", lint.stdout)

    def test_docs_lint_accepts_unnumbered_multi_context_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp) / "docs"
            run("init_docs.py", "--docs", str(docs))
            (docs / "ubiquitous-language.md").unlink()
            ctx = docs / "context"
            ctx.mkdir()
            (ctx / "context-map.md").write_text("# Context Map\n")
            (ctx / "orders.md").write_text(
                "# Orders\n\n## Language\n\n| Term | Meaning | Avoid |\n| :--- | :--- | :--- |\n| Order | Request to buy. | |\n"
            )
            lint = run("docs_lint.py", str(docs))
            self.assertEqual(lint.returncode, 0, lint.stdout + lint.stderr)
            g_lint = run("glossary_lint.py", str(docs))
            self.assertEqual(g_lint.returncode, 0, g_lint.stdout + g_lint.stderr)


class NewDocTests(unittest.TestCase):
    def test_allocates_sequential_flow_and_decision_numbers_and_passes_lint(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp) / "docs"
            run("init_docs.py", "--docs", str(docs))
            for name in ("create-order", "cancel-order", "refund-order"):
                result = run("new_doc.py", "flows", name, "--docs", str(docs))
                self.assertEqual(result.returncode, 0, result.stderr)
            names = sorted(p.name for p in (docs / "flows").glob("*.md"))
            self.assertEqual(names, ["001-create-order.md", "002-cancel-order.md", "003-refund-order.md"])
            flow_text = (docs / "flows/001-create-order.md").read_text()
            self.assertIn("**Document Version**", flow_text)
            self.assertIn("## Overview & Actor", flow_text)
            self.assertIn("## Business Rules", flow_text)
            self.assertIn("## Flow Steps", flow_text)
            self.assertIn("## Edge Cases & Errors", flow_text)

            adr_res = run("new_doc.py", "decisions", "store-orders-in-memory", "--docs", str(docs))
            self.assertEqual(adr_res.returncode, 0, adr_res.stderr)
            self.assertTrue((docs / "decisions/001-store-orders-in-memory.md").exists())

            lint = run("docs_lint.py", str(docs))
            self.assertEqual(lint.returncode, 0, lint.stdout + lint.stderr)
            adr_lint = run("adr_scan.py", str(docs / "decisions"))
            self.assertEqual(adr_lint.returncode, 0, adr_lint.stdout + adr_lint.stderr)

    def test_rejects_bad_subfolder_or_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp) / "docs"
            self.assertEqual(run("new_doc.py", "product", "alpha", "--docs", str(docs)).returncode, 1)
            self.assertEqual(run("new_doc.py", "flows", "Bad_Name", "--docs", str(docs)).returncode, 1)

    def test_flow_missing_required_section_fails_lint(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp) / "docs"
            run("init_docs.py", "--docs", str(docs))
            (docs / "flows/001-incomplete.md").write_text(
                "# Incomplete\n\n**Document Version**: 0.1.0\n**Status**: Draft\n\n## Overview & Actor\nx\n"
            )
            lint = run("docs_lint.py", str(docs))
            self.assertEqual(lint.returncode, 1)
            self.assertIn("missing '## Business Rules' section", lint.stdout)


class GlossaryLintTests(unittest.TestCase):
    def _write(self, tmp, body):
        path = Path(tmp) / "docs/ubiquitous-language.md"
        path.parent.mkdir(parents=True)
        path.write_text(body)
        return path

    def test_valid_glossary_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(
                tmp,
                "# C\n\n## Language\n\n| Term | Meaning | Avoid |\n| :--- | :--- | :--- |\n"
                "| Order | A request to buy. | Purchase |\n",
            )
            self.assertEqual(run("glossary_lint.py", str(path)).returncode, 0)

    def test_empty_table_warns_but_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(tmp, "# C\n\n## Language\n\n| Term | Meaning | Avoid |\n| :--- | :--- | :--- |\n")
            result = run("glossary_lint.py", str(path))
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertIn("no rows yet", result.stdout)

    def test_duplicate_term_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(
                tmp,
                "# C\n\n## Language\n\n| Term | Meaning | Avoid |\n| :--- | :--- | :--- |\n"
                "| Order | A. | |\n| Order | B. | |\n",
            )
            self.assertEqual(run("glossary_lint.py", str(path)).returncode, 1)

    def test_missing_meaning_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(
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
            (decisions / "001-x.md").write_text(
                "# ADR-001: X\n\n## Status\nAccepted\n\n## Context\nc\n\n## Decision\nd\n"
            )
            result = run("adr_scan.py", str(decisions))
            self.assertEqual(result.returncode, 1)
            self.assertIn("Consequences", result.stdout)

    def test_mismatched_filename_and_adr_id_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            decisions = Path(tmp) / "docs/decisions"
            decisions.mkdir(parents=True)
            (decisions / "002-x.md").write_text(
                "# ADR-001: X\n\n## Status\nAccepted\n\n## Context\nc\n\n## Decision\nd\n\n## Consequences\ne\n"
            )
            result = run("adr_scan.py", str(decisions))
            self.assertEqual(result.returncode, 1)
            self.assertIn("does not match file prefix 002", result.stdout)

    def test_valid_adr_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            decisions = Path(tmp) / "docs/decisions"
            decisions.mkdir(parents=True)
            (decisions / "001-x.md").write_text(
                "# ADR-001: X\n\n## Status\nAccepted\n\n## Context\nc\n\n## Decision\nd\n\n## Consequences\ne\n"
            )
            self.assertEqual(run("adr_scan.py", str(decisions)).returncode, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
