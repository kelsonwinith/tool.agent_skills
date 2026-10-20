#!/usr/bin/env python3
"""Unit tests for bootstrap_workflow.py."""

from __future__ import annotations

import json
import pathlib
import sys
import tempfile
import unittest

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPT_DIR))

import bootstrap_workflow as bw  # noqa: E402


class BootstrapWorkflowTests(unittest.TestCase):
    def test_detects_react_and_go_stacks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            self.assertEqual(bw.detect_stacks(root), [])

            (root / "package.json").write_text(
                json.dumps({"dependencies": {"next": "15.0.0", "react": "19.0.0"}}),
                encoding="utf-8",
            )
            self.assertEqual(bw.detect_stacks(root), ["react"])

            (root / "go.mod").write_text("module example.com/app\n\ngo 1.23\n", encoding="utf-8")
            self.assertEqual(bw.detect_stacks(root), ["react", "go"])

    def test_required_skills_include_stack_specific_skills(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / "package.json").write_text(
                json.dumps({"dependencies": {"react": "^19.0.0"}}),
                encoding="utf-8",
            )
            required, stacks = bw.required_skills_for_project(root)
            self.assertEqual(stacks, ["react"])
            self.assertIn("project-workflow", required)
            self.assertIn("project-grill", required)
            self.assertIn("project-documentation", required)
            self.assertIn("project-plan", required)
            self.assertIn("project-implement", required)
            self.assertIn("project-react-architecture", required)
            self.assertNotIn("project-go-architecture", required)

    def test_dry_run_reports_missing_skills_and_install_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as fake_home:
            root = pathlib.Path(tmp)
            home = pathlib.Path(fake_home)
            (root / "go.mod").write_text("module example.com/api\n", encoding="utf-8")

            # Simulate only project-workflow installed so far
            wf_dir = root / ".agents" / "skills" / "project-workflow"
            wf_dir.mkdir(parents=True)
            (wf_dir / "SKILL.md").write_text("---\nname: project-workflow\n---\n", encoding="utf-8")

            result = bw.bootstrap(
                project_root=root,
                dry_run=True,
                home_dir=home,
            )
            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["detected_stacks"], ["go"])
            self.assertIn("project-workflow", result["installed_skills"])
            self.assertEqual(
                result["missing_skills"],
                [
                    "project-grill",
                    "project-documentation",
                    "project-plan",
                    "project-implement",
                    "project-go-architecture",
                ],
            )
            self.assertEqual(
                result["install_command"],
                "npx skills add kelsonwinith/tool.agent_skills --skill "
                "project-grill project-documentation project-plan project-implement "
                "project-go-architecture -y",
            )


if __name__ == "__main__":
    unittest.main()
