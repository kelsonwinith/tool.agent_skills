#!/usr/bin/env python3
"""Interactive local Web UI companion for project-workflow.

Starts a zero-dependency local HTTP server serving a single-page stepper
dashboard. Persists synchronized workflow state to .workflow/state.json and
allows the user to review stage artifacts, type instructions, and click
'Approve & Next Step' or 'Request Revisions'.

Usage (CLI):
    python scripts/workflow_ui.py --start [--port 4321] [--request "Add cancellation"]
    python scripts/workflow_ui.py --update --stage 1 --status waiting_approval --content "..."
    python scripts/workflow_ui.py --wait [--timeout 600]
    python scripts/workflow_ui.py --stop
"""

from __future__ import annotations

import argparse
import http.server
import json
import os
import pathlib
import signal
import socket
import socketserver
import sys
import threading
import time
import urllib.parse
import webbrowser
from typing import Any, Dict, Optional, Tuple

DEFAULT_PORT = 4321
WORKFLOW_DIR_NAME = ".workflow"
STATE_FILE_NAME = "state.json"

STAGES = [
    {"id": 1, "name": "Grill", "command": "/project-grill", "desc": "Design-tree interview & conflict check"},
    {"id": 2, "name": "Docs", "command": "/project-documentation", "desc": "Ubiquitous language, flows & ADRs"},
    {"id": 3, "name": "Plan", "command": "/project-plan", "desc": "Layer scan & Proposed File Tree"},
    {"id": 4, "name": "Implement", "command": "/project-implement", "desc": "Code implementation & verification"},
]

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Project Workflow Dashboard</title>
<style>
  :root {
    --bg: #0d1117;
    --card: #161b22;
    --border: #30363d;
    --text: #c9d1d9;
    --text-bright: #f0f6fc;
    --text-dim: #8b949e;
    --accent: #58a6ff;
    --accent-glow: rgba(88, 166, 255, 0.15);
    --green: #2ea043;
    --green-bright: #3fb950;
    --amber: #d29922;
    --red: #f85149;
    --purple: #bc8cff;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }
  header {
    background: var(--card);
    border-bottom: 1px solid var(--border);
    padding: 16px 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .brand {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .brand h1 {
    font-size: 18px;
    font-weight: 600;
    color: var(--text-bright);
    letter-spacing: -0.2px;
  }
  .brand .tag {
    background: var(--accent-glow);
    color: var(--accent);
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 600;
    border: 1px solid rgba(88, 166, 255, 0.3);
  }
  .request-banner {
    background: #090d13;
    border-bottom: 1px solid var(--border);
    padding: 12px 24px;
    font-size: 13px;
    color: var(--text-dim);
    display: flex;
    gap: 8px;
    align-items: center;
  }
  .request-banner strong { color: var(--text-bright); }
  .stepper {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    background: var(--card);
    border-bottom: 1px solid var(--border);
    padding: 0;
  }
  .step {
    padding: 14px 16px;
    border-right: 1px solid var(--border);
    display: flex;
    align-items: center;
    gap: 12px;
    cursor: default;
    transition: background 0.15s ease;
  }
  .step:last-child { border-right: none; }
  .step-num {
    width: 28px;
    height: 28px;
    border-radius: 50%;
    background: var(--border);
    color: var(--text-dim);
    font-size: 12px;
    font-weight: 700;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }
  .step-info { overflow: hidden; }
  .step-title {
    font-size: 13px;
    font-weight: 600;
    color: var(--text);
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .step-desc { font-size: 11px; color: var(--text-dim); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .step.active { background: rgba(88, 166, 255, 0.08); }
  .step.active .step-num { background: var(--accent); color: #0d1117; }
  .step.active .step-title { color: var(--accent); }
  .step.completed .step-num { background: var(--green); color: #fff; }
  .step.completed .step-title { color: var(--text-bright); }
  main {
    flex: 1;
    display: flex;
    flex-direction: column;
    padding: 24px;
    max-width: 1200px;
    width: 100%;
    margin: 0 auto;
    gap: 20px;
  }
  .status-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 12px;
    border-radius: 16px;
    font-size: 12px;
    font-weight: 600;
    align-self: flex-start;
  }
  .status-waiting_approval { background: rgba(210, 153, 34, 0.15); color: var(--amber); border: 1px solid rgba(210, 153, 34, 0.4); }
  .status-in_progress { background: var(--accent-glow); color: var(--accent); border: 1px solid rgba(88, 166, 255, 0.4); }
  .status-completed { background: rgba(46, 160, 67, 0.15); color: var(--green-bright); border: 1px solid rgba(46, 160, 67, 0.4); }
  .card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid var(--border);
    padding-bottom: 12px;
  }
  .card-title { font-size: 15px; font-weight: 600; color: var(--text-bright); }
  .artifact-content {
    background: #090d13;
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 16px;
    font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
    font-size: 13px;
    line-height: 1.6;
    color: var(--text-bright);
    white-space: pre-wrap;
    overflow-x: auto;
    max-height: 480px;
    overflow-y: auto;
  }
  .badge-tag {
    display: inline-block;
    padding: 1px 6px;
    border-radius: 4px;
    font-weight: 700;
    font-size: 11px;
    margin-right: 4px;
  }
  .tag-NEW { background: rgba(46, 160, 67, 0.25); color: var(--green-bright); }
  .tag-UPDATE { background: rgba(88, 166, 255, 0.25); color: var(--accent); }
  .tag-REUSE { background: rgba(139, 148, 158, 0.25); color: var(--text-dim); }
  .tag-PROMOTE { background: rgba(188, 140, 255, 0.25); color: var(--purple); }
  .tag-DELETE { background: rgba(248, 81, 73, 0.25); color: var(--red); }
  .action-panel {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  .action-panel textarea {
    background: #090d13;
    border: 1px solid var(--border);
    border-radius: 6px;
    color: var(--text-bright);
    padding: 12px;
    font-family: inherit;
    font-size: 13px;
    resize: vertical;
    min-height: 70px;
    outline: none;
    transition: border-color 0.15s ease;
  }
  .action-panel textarea:focus { border-color: var(--accent); }
  .button-group {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
    align-items: center;
  }
  button {
    font-family: inherit;
    font-size: 13px;
    font-weight: 600;
    padding: 8px 16px;
    border-radius: 6px;
    cursor: pointer;
    border: none;
    transition: opacity 0.15s ease, background 0.15s ease;
    display: inline-flex;
    align-items: center;
    gap: 6px;
  }
  button:hover { opacity: 0.9; }
  button:disabled { opacity: 0.4; cursor: not-allowed; }
  .btn-approve { background: var(--green); color: #fff; }
  .btn-revise { background: var(--card); color: var(--text-bright); border: 1px solid var(--border); }
  .hint { font-size: 11px; color: var(--text-dim); }
  .live-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--green-bright);
    animation: pulse 2s infinite;
  }
  @keyframes pulse {
    0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(63, 185, 80, 0.7); }
    70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(63, 185, 80, 0); }
    100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(63, 185, 80, 0); }
  }
</style>
</head>
<body>
<header>
  <div class="brand">
    <div class="live-dot"></div>
    <h1>Project Workflow</h1>
    <span class="tag">Dual-Mode UI</span>
  </div>
  <div class="hint">Synced with agent terminal</div>
</header>

<div class="request-banner">
  <span>Goal:</span>
  <strong id="requestText">Loading request...</strong>
</div>

<div class="stepper" id="stepper"></div>

<main>
  <div id="statusPill" class="status-pill status-in_progress">Connecting...</div>

  <div class="card">
    <div class="card-header">
      <div class="card-title" id="stageTitle">Stage Content</div>
      <div class="hint" id="timestamp"></div>
    </div>
    <div class="artifact-content" id="artifactBody">Waiting for agent stage output...</div>

    <div class="action-panel">
      <textarea id="feedbackInput" placeholder="Optional: Type instructions, answers, or adjustments for this stage (Cmd/Ctrl + Enter to approve)..."></textarea>
      <div class="button-group">
        <span class="hint">Shortcut: Cmd/Ctrl + Enter</span>
        <button id="btnRevise" class="btn-revise" onclick="submitAction('revise')">Request Revisions</button>
        <button id="btnApprove" class="btn-approve" onclick="submitAction('approve')">&#10003; Approve &amp; Next Step</button>
      </div>
    </div>
  </div>
</main>

<script>
  const STAGES = [
    { id: 1, name: "Stage 1 — Grill", cmd: "/project-grill", desc: "Design-tree interview" },
    { id: 2, name: "Stage 2 — Docs", cmd: "/project-documentation", desc: "Sync glossary, flows & ADRs" },
    { id: 3, name: "Stage 3 — Plan", cmd: "/project-plan", desc: "### Proposed File Tree" },
    { id: 4, name: "Stage 4 — Implement", cmd: "/project-implement", desc: "Code & verification" }
  ];

  let currentState = null;

  function renderStepper(currentStage, status) {
    const el = document.getElementById("stepper");
    el.innerHTML = STAGES.map(s => {
      let cls = "step";
      if (s.id < currentStage || (s.id === currentStage && status === "completed")) {
        cls += " completed";
      } else if (s.id === currentStage) {
        cls += " active";
      }
      return `
        <div class="${cls}">
          <div class="step-num">${s.id < currentStage || (s.id === currentStage && status === "completed") ? "&#10003;" : s.id}</div>
          <div class="step-info">
            <div class="step-title">${s.name}</div>
            <div class="step-desc">${s.desc}</div>
          </div>
        </div>
      `;
    }).join("");
  }

  function highlightArtifact(text) {
    if (!text) return "No content.";
    // Highlight file tree action tags
    return text
      .replace(/\\[(NEW|UPDATE|REUSE|PROMOTE|DELETE)\\]/g, '<span class="badge-tag tag-$1">[$1]</span>');
  }

  function updateUI(state) {
    currentState = state;
    document.getElementById("requestText").textContent = state.request || "Running project-workflow";
    renderStepper(state.current_stage || 1, state.status || "in_progress");

    const pill = document.getElementById("statusPill");
    const label = (state.status || "in_progress").replace("_", " ").toUpperCase();
    pill.className = "status-pill status-" + (state.status || "in_progress");
    pill.textContent = label === "WAITING APPROVAL" ? "Waiting for Your Approval" : label;

    document.getElementById("stageTitle").textContent = state.stage_title || ("Stage " + state.current_stage);
    document.getElementById("timestamp").textContent = state.updated_at ? new Date(state.updated_at).toLocaleTimeString() : "";

    const body = document.getElementById("artifactBody");
    body.innerHTML = highlightArtifact(state.content || "Waiting for agent output...");

    const isWaiting = state.status === "waiting_approval";
    document.getElementById("btnApprove").disabled = !isWaiting && state.status !== "in_progress";
    document.getElementById("btnRevise").disabled = !isWaiting && state.status !== "in_progress";
  }

  async function pollState() {
    try {
      const res = await fetch("/api/state");
      if (res.ok) {
        const data = await res.json();
        updateUI(data);
      }
    } catch (e) {
      console.error("Poll error", e);
    }
  }

  async function submitAction(actionType) {
    const input = document.getElementById("feedbackInput");
    const text = input.value.trim();
    const btnApprove = document.getElementById("btnApprove");
    const btnRevise = document.getElementById("btnRevise");
    btnApprove.disabled = true;
    btnRevise.disabled = true;

    try {
      const res = await fetch("/api/action", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: actionType, text: text })
      });
      if (res.ok) {
        input.value = "";
        const data = await res.json();
        updateUI(data);
      }
    } catch (e) {
      alert("Failed to send action: " + e.message);
    } finally {
      btnApprove.disabled = false;
      btnRevise.disabled = false;
    }
  }

  document.getElementById("feedbackInput").addEventListener("keydown", function(e) {
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
      submitAction("approve");
    }
  });

  setInterval(pollState, 1000);
  pollState();
</script>
</body>
</html>
"""


def get_state_path(project_root: pathlib.Path) -> pathlib.Path:
    return project_root / WORKFLOW_DIR_NAME / STATE_FILE_NAME


def read_state(project_root: pathlib.Path) -> Dict[str, Any]:
    path = get_state_path(project_root)
    if not path.is_file():
        return {
            "current_stage": 1,
            "status": "in_progress",
            "request": "",
            "stage_title": "Stage 1 — Grill",
            "content": "",
            "pending_action": None,
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def write_state(project_root: pathlib.Path, state: Dict[str, Any]) -> None:
    path = get_state_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    state["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")


def find_free_port(start_port: int = DEFAULT_PORT) -> int:
    port = start_port
    while port < start_port + 100:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
            port += 1
    return start_port


class WorkflowHTTPHandler(http.server.BaseHTTPRequestHandler):
    project_root: pathlib.Path = pathlib.Path(".")
    server_instance: Optional[socketserver.TCPServer] = None

    def log_message(self, format: str, *args: Any) -> None:
        return  # Silence server stdout logs

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/" or parsed.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode("utf-8"))
        elif parsed.path == "/api/state":
            state = read_state(self.project_root)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(state).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/action":
            length = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            state = read_state(self.project_root)
            state["pending_action"] = {
                "action": payload.get("action", "approve"),
                "text": payload.get("text", "").strip(),
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
            state["status"] = "in_progress"
            write_state(self.project_root, state)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(state).encode("utf-8"))
        elif parsed.path == "/api/stop":
            self.send_response(200)
            self.end_headers()
            if self.server_instance:
                threading.Thread(target=self.server_instance.shutdown).start()
        else:
            self.send_response(404)
            self.end_headers()


def start_server(
    project_root: pathlib.Path, port: int = DEFAULT_PORT, open_browser: bool = True
) -> Tuple[socketserver.TCPServer, int]:
    port = find_free_port(port)
    WorkflowHTTPHandler.project_root = project_root

    class ThreadedServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
        allow_reuse_address = True

    server = ThreadedServer(("127.0.0.1", port), WorkflowHTTPHandler)
    WorkflowHTTPHandler.server_instance = server

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    url = f"http://127.0.0.1:{port}"
    if open_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass

    return server, port


def stop_server(project_root: pathlib.Path) -> None:
    state_file = get_state_path(project_root)
    pid_file = project_root / WORKFLOW_DIR_NAME / "server.pid"

    if pid_file.is_file():
        try:
            pid = int(pid_file.read_text(encoding="utf-8").strip())
            os.kill(pid, signal.SIGTERM)
        except Exception:
            pass
        pid_file.unlink(missing_ok=True)

    if state_file.is_file():
        state_file.unlink(missing_ok=True)


def cmd_start(args: argparse.Namespace) -> int:
    root = pathlib.Path(args.root).resolve()
    port = find_free_port(args.port)
    initial_state = {
        "current_stage": 1,
        "status": "in_progress",
        "request": args.request or "",
        "stage_title": "Stage 1 — Grill",
        "content": "Starting Stage 1 (/project-grill)... Inspecting repository and checking terminology.",
        "pending_action": None,
        "port": port,
    }
    write_state(root, initial_state)

    pid_file = root / WORKFLOW_DIR_NAME / "server.pid"
    pid_file.write_text(str(os.getpid()), encoding="utf-8")

    server, actual_port = start_server(root, port=port, open_browser=not args.no_browser)
    url = f"http://127.0.0.1:{actual_port}"
    print(json.dumps({"status": "running", "url": url, "port": actual_port, "state_file": str(get_state_path(root))}))

    if args.daemon:
        # Run server until terminated
        try:
            while True:
                time.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            server.shutdown()
            stop_server(root)
    return 0


def cmd_update(args: argparse.Namespace) -> int:
    root = pathlib.Path(args.root).resolve()
    state = read_state(root)

    if args.stage is not None:
        state["current_stage"] = args.stage
    if args.status:
        state["status"] = args.status
    if args.title:
        state["stage_title"] = args.title
    if args.request:
        state["request"] = args.request

    if args.content_file:
        content_path = pathlib.Path(args.content_file)
        if content_path.is_file():
            state["content"] = content_path.read_text(encoding="utf-8")
    elif args.content is not None:
        state["content"] = args.content

    state["pending_action"] = None
    write_state(root, state)
    print(json.dumps({"status": "updated", "stage": state["current_stage"], "stage_status": state["status"]}))
    return 0


def cmd_wait(args: argparse.Namespace) -> int:
    root = pathlib.Path(args.root).resolve()
    start_time = time.time()
    timeout = args.timeout

    while True:
        state = read_state(root)
        action = state.get("pending_action")
        if action:
            # Clear pending action after reading
            state["pending_action"] = None
            write_state(root, state)
            print(json.dumps(action))
            return 0

        if timeout and (time.time() - start_time) > timeout:
            print(json.dumps({"error": "timeout"}))
            return 1
        time.sleep(0.5)


def cmd_stop(args: argparse.Namespace) -> int:
    root = pathlib.Path(args.root).resolve()
    stop_server(root)
    print(json.dumps({"status": "stopped"}))
    return 0


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", default=".", help="Project root directory (default: .)")

    sub = parser.add_mutually_exclusive_group(required=True)
    sub.add_argument("--start", action="store_true", help="Start the workflow Web UI server")
    sub.add_argument("--update", action="store_true", help="Update the stage content and status")
    sub.add_argument("--wait", action="store_true", help="Wait for user action from the Web UI")
    sub.add_argument("--stop", action="store_true", help="Stop server and clean up .workflow/")

    # Start options
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"Server port (default: {DEFAULT_PORT})")
    parser.add_argument("--no-browser", action="store_true", help="Do not open browser automatically")
    parser.add_argument("--daemon", action="store_true", help="Keep running in foreground")

    # Update options
    parser.add_argument("--stage", type=int, choices=[1, 2, 3, 4], help="Workflow stage number (1-4)")
    parser.add_argument("--status", choices=["in_progress", "waiting_approval", "completed"], help="Stage status")
    parser.add_argument("--title", help="Stage card title")
    parser.add_argument("--request", help="Initial user request prompt")
    parser.add_argument("--content", help="Stage artifact text or diff")
    parser.add_argument("--content-file", help="Path to file containing stage artifact text")

    # Wait options
    parser.add_argument("--timeout", type=int, default=600, help="Wait timeout in seconds (default: 600)")

    args = parser.parse_args(argv)

    if args.start:
        return cmd_start(args)
    if args.update:
        return cmd_update(args)
    if args.wait:
        return cmd_wait(args)
    if args.stop:
        return cmd_stop(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
