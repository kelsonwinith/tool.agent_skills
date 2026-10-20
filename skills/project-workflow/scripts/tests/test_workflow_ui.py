#!/usr/bin/env python3
"""Unit tests for workflow_ui.py."""

from __future__ import annotations

import json
import pathlib
import sys
import tempfile
import time
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
            self.assertEqual(state["status"], "in_progress")

            state["current_stage"] = 2
            state["status"] = "waiting_approval"
            state["content"] = "### Agreed Design Summary\n- Done."
            wui.write_state(root, state)

            read_back = wui.read_state(root)
            self.assertEqual(read_back["current_stage"], 2)
            self.assertEqual(read_back["status"], "waiting_approval")
            self.assertIn("Agreed Design Summary", read_back["content"])

    def test_http_server_endpoints(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            server, port = wui.start_server(root, port=54321, open_browser=False)
            try:
                base_url = f"http://127.0.0.1:{port}"

                # Test GET /
                with urllib.request.urlopen(f"{base_url}/") as res:
                    self.assertEqual(res.status, 200)
                    html = res.read().decode("utf-8")
                    self.assertIn("Project Workflow", html)
                    self.assertIn("stepper", html)

                # Test GET /api/state
                with urllib.request.urlopen(f"{base_url}/api/state") as res:
                    self.assertEqual(res.status, 200)
                    data = json.loads(res.read().decode("utf-8"))
                    self.assertEqual(data.get("current_stage"), 1)

                # Test POST /api/action
                req = urllib.request.Request(
                    f"{base_url}/api/action",
                    data=json.dumps({"action": "approve", "text": "Looks good!"}).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req) as res:
                    self.assertEqual(res.status, 200)
                    data = json.loads(res.read().decode("utf-8"))
                    action = data.get("pending_action")
                    self.assertIsNotNone(action)
                    self.assertEqual(action.get("action"), "approve")
                    self.assertEqual(action.get("text"), "Looks good!")

                # Verify state persisted to disk
                saved = wui.read_state(root)
                self.assertEqual(saved["pending_action"]["action"], "approve")
            finally:
                server.shutdown()
                wui.stop_server(root)


if __name__ == "__main__":
    unittest.main()
