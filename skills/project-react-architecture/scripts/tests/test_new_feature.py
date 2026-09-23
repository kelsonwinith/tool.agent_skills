#!/usr/bin/env python3
"""Regression tests for the React feature scaffolder.

Run:  python scripts/tests/test_new_feature.py
Uses only the standard library (unittest + subprocess)."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent


def run(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPTS / "new_feature.py"), *args],
        capture_output=True,
        text=True,
    )


class NewFeatureTests(unittest.TestCase):
    def test_creates_expected_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run("userProfile", "--root", tmp)
            self.assertEqual(result.returncode, 0, result.stderr)
            base = Path(tmp) / "features/userProfile"
            self.assertTrue((base / "userProfile.feature.ts").exists())
            comp = base / "components/userProfile"
            for suffix in (".component.tsx", ".hook.ts", ".type.ts"):
                self.assertTrue((comp / f"userProfile{suffix}").exists(), suffix)
            self.assertNotIn("className", (comp / "userProfile.component.tsx").read_text())

    def test_normalizes_kebab_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            run("user-profile", "--root", tmp)
            self.assertTrue((Path(tmp) / "features/userProfile/userProfile.feature.ts").exists())

    def test_component_flag(self):
        with tempfile.TemporaryDirectory() as tmp:
            run("billing", "--component", "invoice-list", "--root", tmp)
            comp = Path(tmp) / "features/billing/components/invoiceList"
            self.assertTrue((comp / "invoiceList.component.tsx").exists())
            self.assertIn("InvoiceList", (comp / "invoiceList.type.ts").read_text())

    def test_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            run("userProfile", "--root", tmp)
            target = Path(tmp) / "features/userProfile/userProfile.feature.ts"
            target.write_text("// hand-edited\n")
            second = run("userProfile", "--root", tmp)
            self.assertEqual(second.returncode, 0)
            self.assertIn("SKIP", second.stdout)
            self.assertEqual(target.read_text(), "// hand-edited\n")


if __name__ == "__main__":
    unittest.main(verbosity=2)
