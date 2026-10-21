#!/usr/bin/env python3
"""Unit tests for workflow_ui.py."""

from __future__ import annotations

import json
import pathlib
import sys
import tempfile
import unittest
import urllib.request

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPT_DIR))

import workflow_ui as wui  # noqa: E402


class WorkflowUITests(unittest.TestCase):
    def test_read_and_write_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            state = wui.read_state(root)
            self.assertEqual(state["current_stage"], 1)
            self.assertEqual(state["status"], "awaiting_prompt")
            self.assertEqual(len(state["stages"]), 4)

            # Check locked vs skippable default flags
            self.assertTrue(state["stages"][0]["locked"])  # Stage 1 Grill
            self.assertFalse(state["stages"][1]["locked"]) # Stage 2 Docs
            self.assertFalse(state["stages"][2]["locked"]) # Stage 3 Plan
            self.assertTrue(state["stages"][3]["locked"])  # Stage 4 Implement

            state["current_stage"] = 2
            state["status"] = "waiting_approval"
            state["content"] = "### Agreed Design Summary\n- Done."
            wui.write_state(root, state)

            read_back = wui.read_state(root)
            self.assertEqual(read_back["current_stage"], 2)
            self.assertEqual(read_back["status"], "waiting_approval")
            self.assertIn("Agreed Design Summary", read_back["content"])

    def test_next_enabled_stage_skips_disabled_stages(self) -> None:
        stages = wui.default_stages()
        state = {"stages": stages}

        # With all enabled: next after 1 is 2
        self.assertEqual(wui.get_next_enabled_stage(state, 1), 2)

        # Disable stage 2 (Docs)
        stages[1]["enabled"] = False
        self.assertEqual(wui.get_next_enabled_stage(state, 1), 3)

        # Disable stage 3 (Plan) too -> skips to stage 4
        stages[2]["enabled"] = False
        self.assertEqual(wui.get_next_enabled_stage(state, 1), 4)

    def test_http_server_endpoints_and_web_prompting(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            server, port = wui.start_server(root, port=54323, open_browser=False)
            try:
                base_url = f"http://127.0.0.1:{port}"

                # Test GET /
                with urllib.request.urlopen(f"{base_url}/") as res:
                    self.assertEqual(res.status, 200)
                    html = res.read().decode("utf-8")
                    self.assertIn("Project Workflow", html)
                    self.assertIn("heroCard", html)

                # Test GET /api/state: starts in awaiting_prompt
                with urllib.request.urlopen(f"{base_url}/api/state") as res:
                    self.assertEqual(res.status, 200)
                    data = json.loads(res.read().decode("utf-8"))
                    self.assertEqual(data.get("status"), "awaiting_prompt")

                # Test POST /api/action: start_workflow from web UI
                req_start = urllib.request.Request(
                    f"{base_url}/api/action",
                    data=json.dumps({"action": "start_workflow", "text": "Build user auth"}).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req_start) as res:
                    self.assertEqual(res.status, 200)
                    data = json.loads(res.read().decode("utf-8"))
                    self.assertEqual(data.get("status"), "in_progress")
                    self.assertEqual(data.get("request"), "Build user auth")
                    self.assertEqual(data["pending_action"]["action"], "start_workflow")
                    self.assertEqual(data["pending_action"]["text"], "Build user auth")

                # Test POST /api/config: Toggle Stage 2 (Docs)
                req_cfg = urllib.request.Request(
                    f"{base_url}/api/config",
                    data=json.dumps({"toggle_stage": 2}).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req_cfg) as res:
                    self.assertEqual(res.status, 200)
                    data = json.loads(res.read().decode("utf-8"))
                    stage_2 = [s for s in data["stages"] if s["id"] == 2][0]
                    self.assertFalse(stage_2["enabled"])

                # Test POST /api/action: approve
                req_act = urllib.request.Request(
                    f"{base_url}/api/action",
                    data=json.dumps({"action": "approve", "text": "Looks good!"}).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req_act) as res:
                    self.assertEqual(res.status, 200)
                    data = json.loads(res.read().decode("utf-8"))
                    action = data.get("pending_action")
                    self.assertIsNotNone(action)
                    self.assertEqual(action.get("action"), "approve")

                # Test POST /api/action: reset_workflow (full loop cycle)
                req_reset = urllib.request.Request(
                    f"{base_url}/api/action",
                    data=json.dumps({"action": "reset_workflow"}).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req_reset) as res:
                    self.assertEqual(res.status, 200)
                    data = json.loads(res.read().decode("utf-8"))
                    self.assertEqual(data.get("status"), "awaiting_prompt")
                    self.assertEqual(data.get("request"), "")
                    self.assertEqual(data.get("current_stage"), 1)
                    self.assertIsNone(data.get("pending_action"))
                    # History should record previous run
                    history = data.get("history", [])
                    self.assertEqual(len(history), 1)
                    self.assertEqual(history[0]["request"], "Build user auth")

                # Test Starting Second Workflow in the same session (full loop continuation)
                req_start2 = urllib.request.Request(
                    f"{base_url}/api/action",
                    data=json.dumps({"action": "start_workflow", "text": "Add billing portal"}).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req_start2) as res:
                    self.assertEqual(res.status, 200)
                    data = json.loads(res.read().decode("utf-8"))
                    self.assertEqual(data.get("status"), "in_progress")
                    self.assertEqual(data.get("request"), "Add billing portal")
                    self.assertEqual(data["pending_action"]["text"], "Add billing portal")

            finally:
                server.shutdown()
                wui.stop_server(root)

    def test_html_template_contains_shadcn_and_theme_tokens(self) -> None:
        html = wui.HTML_TEMPLATE
        # Check shadcn HSL CSS variables
        self.assertIn("--background:", html)
        self.assertIn("--foreground:", html)
        self.assertIn("--card:", html)
        self.assertIn("--primary:", html)
        self.assertIn("--border:", html)
        self.assertIn(".dark {", html)

        # Check theme switcher elements
        self.assertIn("theme-light", html)
        self.assertIn("theme-dark", html)
        self.assertIn("theme-system", html)
        self.assertIn("workflow-theme", html)
        self.assertIn("prefers-color-scheme: dark", html)

        # Check full loop reset and copy elements
        self.assertIn("resetWorkflow()", html)
        self.assertIn("copyArtifact()", html)
        self.assertIn("Full Loop", html)


if __name__ == "__main__":
    unittest.main()
