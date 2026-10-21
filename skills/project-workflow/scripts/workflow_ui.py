#!/usr/bin/env python3
"""Interactive local Web UI companion for project-workflow.

Starts a zero-dependency local HTTP server serving a single-page stepper
dashboard. Persists synchronized workflow state to .workflow/state.json,
shows attached skills per stage, allows toggling optional stages (Docs, Plan)
while enforcing locked stages (Grill, Implement), allows switching stack
architecture skills, and allows users to enter initial prompts, review stage
artifacts, type instructions, and click 'Approve & Next Step' directly on
the website.

Usage (CLI):
    python scripts/workflow_ui.py --start [--port 4321] [--request "Add cancellation"]
    python scripts/workflow_ui.py --update --stage 1 --status waiting_approval --content "..."
    python scripts/workflow_ui.py --next-stage 1   # Prints next enabled stage number (skipping disabled stages)
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
import subprocess
import sys
import threading
import time
import urllib.parse
import urllib.request
import webbrowser
from typing import Any, Dict, List, Optional, Tuple

DEFAULT_PORT = 4321
WORKFLOW_DIR_NAME = ".workflow"
STATE_FILE_NAME = "state.json"


def detect_project_stack(project_root: pathlib.Path) -> str:
    pkg = project_root / "package.json"
    if pkg.is_file():
        try:
            data = json.loads(pkg.read_text(encoding="utf-8"))
            deps: Dict[str, Any] = {}
            for k in ("dependencies", "devDependencies", "peerDependencies"):
                sec = data.get(k)
                if isinstance(sec, dict):
                    deps.update(sec)
            if any(p in deps for p in ("react", "react-dom", "next")):
                return "react"
        except Exception:
            pass

    if (project_root / "go.mod").is_file():
        return "go"

    return "none"


def default_stages(selected_stack: str = "none") -> List[Dict[str, Any]]:
    react_enabled = selected_stack == "react"
    go_enabled = selected_stack == "go"

    return [
        {
            "id": 1,
            "name": "Stage 1 — Grill",
            "command": "/project-grill",
            "enabled": True,
            "locked": True,
            "desc": "Design-tree interview & conflict check",
            "skills": [
                {"name": "project-grill", "role": "Required", "locked": True, "enabled": True}
            ],
        },
        {
            "id": 2,
            "name": "Stage 2 — Docs",
            "command": "/project-documentation",
            "enabled": True,
            "locked": False,
            "desc": "Ubiquitous language, flows & ADRs",
            "skills": [
                {"name": "project-documentation", "role": "Docs Guardian", "locked": False, "enabled": True}
            ],
        },
        {
            "id": 3,
            "name": "Stage 3 — Plan",
            "command": "/project-plan",
            "enabled": True,
            "locked": False,
            "desc": "Layer scan & Proposed File Tree",
            "skills": [
                {"name": "project-plan", "role": "File Tree Planner", "locked": True, "enabled": True},
                {"name": "project-react-architecture", "role": "React Stack", "locked": False, "enabled": react_enabled, "group": "stack"},
                {"name": "project-go-architecture", "role": "Go Stack", "locked": False, "enabled": go_enabled, "group": "stack"},
            ],
        },
        {
            "id": 4,
            "name": "Stage 4 — Implement",
            "command": "/project-implement",
            "enabled": True,
            "locked": True,
            "desc": "Code implementation & verification",
            "skills": [
                {"name": "project-implement", "role": "Code & Verification", "locked": True, "enabled": True},
                {"name": "project-react-architecture", "role": "React Stack", "locked": False, "enabled": react_enabled, "group": "stack"},
                {"name": "project-go-architecture", "role": "Go Stack", "locked": False, "enabled": go_enabled, "group": "stack"},
            ],
        },
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
    padding: 14px 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .brand { display: flex; align-items: center; gap: 12px; }
  .brand h1 { font-size: 17px; font-weight: 600; color: var(--text-bright); }
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
    padding: 10px 24px;
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
  }
  .step {
    padding: 12px 16px;
    border-right: 1px solid var(--border);
    display: flex;
    align-items: center;
    gap: 12px;
    transition: background 0.15s ease;
  }
  .step:last-child { border-right: none; }
  .step-num {
    width: 26px;
    height: 26px;
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
  .step.skipped { opacity: 0.45; }
  .step.skipped .step-title { text-decoration: line-through; }

  /* Config / Skill Bar */
  .config-section {
    background: #090d13;
    border-bottom: 1px solid var(--border);
    padding: 12px 24px;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }
  .config-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 12px;
    font-weight: 600;
    color: var(--text-dim);
  }
  .config-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
  }
  .stage-config-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 10px 12px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  .stage-config-title {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 12px;
    font-weight: 600;
    color: var(--text-bright);
  }
  .stage-toggle {
    cursor: pointer;
    font-size: 11px;
    padding: 2px 8px;
    border-radius: 10px;
    border: 1px solid var(--border);
    background: transparent;
    color: var(--text-dim);
    transition: all 0.15s ease;
  }
  .stage-toggle.enabled { background: rgba(46, 160, 67, 0.15); color: var(--green-bright); border-color: rgba(46, 160, 67, 0.4); }
  .stage-toggle.locked { opacity: 0.8; cursor: not-allowed; background: var(--accent-glow); color: var(--accent); border-color: rgba(88, 166, 255, 0.3); }
  .skill-chips { display: flex; flex-wrap: wrap; gap: 4px; }
  .skill-chip {
    font-size: 10px;
    padding: 2px 6px;
    border-radius: 4px;
    background: #0d1117;
    border: 1px solid var(--border);
    color: var(--text);
  }
  .skill-chip.active { border-color: var(--accent); color: var(--accent); }

  /* Stack selector */
  .stack-selector {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 12px;
    color: var(--text-dim);
  }
  .stack-btn {
    background: var(--card);
    border: 1px solid var(--border);
    color: var(--text);
    padding: 3px 10px;
    border-radius: 12px;
    font-size: 11px;
    cursor: pointer;
    transition: all 0.15s ease;
  }
  .stack-btn.selected {
    background: var(--accent);
    color: #0d1117;
    font-weight: 600;
    border-color: var(--accent);
  }

  main {
    flex: 1;
    display: flex;
    flex-direction: column;
    padding: 20px 24px;
    max-width: 1200px;
    width: 100%;
    margin: 0 auto;
    gap: 16px;
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
  .status-awaiting_prompt { background: rgba(88, 166, 255, 0.15); color: var(--accent); border: 1px solid rgba(88, 166, 255, 0.4); }
  .status-waiting_approval { background: rgba(210, 153, 34, 0.15); color: var(--amber); border: 1px solid rgba(210, 153, 34, 0.4); }
  .status-in_progress { background: var(--accent-glow); color: var(--accent); border: 1px solid rgba(88, 166, 255, 0.4); }
  .status-completed { background: rgba(46, 160, 67, 0.15); color: var(--green-bright); border: 1px solid rgba(46, 160, 67, 0.4); }

  /* Initial Prompt Hero Card */
  .hero-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 24px;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }
  .hero-title {
    font-size: 18px;
    font-weight: 600;
    color: var(--text-bright);
  }
  .hero-subtitle {
    font-size: 13px;
    color: var(--text-dim);
    line-height: 1.5;
  }
  .hero-textarea {
    background: #090d13;
    border: 1px solid var(--border);
    border-radius: 6px;
    color: var(--text-bright);
    padding: 14px;
    font-family: inherit;
    font-size: 14px;
    line-height: 1.5;
    resize: vertical;
    min-height: 120px;
    outline: none;
    transition: border-color 0.15s ease;
  }
  .hero-textarea:focus { border-color: var(--accent); }

  .card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 18px;
    display: flex;
    flex-direction: column;
    gap: 14px;
  }
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid var(--border);
    padding-bottom: 10px;
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
    max-height: 440px;
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
    transition: opacity 0.15s ease;
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
  <div class="stack-selector">
    <span>Architecture Stack:</span>
    <button class="stack-btn" id="stack-react" onclick="selectStack('react')">React / Next.js</button>
    <button class="stack-btn" id="stack-go" onclick="selectStack('go')">Go Hexagonal</button>
    <button class="stack-btn" id="stack-none" onclick="selectStack('none')">Generic Clean</button>
  </div>
</header>

<div class="request-banner" id="requestBanner">
  <span>Goal:</span>
  <strong id="requestText">Awaiting your prompt below...</strong>
</div>

<div class="stepper" id="stepper"></div>

<div class="config-section">
  <div class="config-header">
    <span>PIPELINE STAGES &amp; SKILLS CONFIGURATION</span>
    <span class="hint">Stages 1 &amp; 4 are locked 🔒 for flow integrity</span>
  </div>
  <div class="config-grid" id="configGrid"></div>
</div>

<main>
  <!-- Hero section for entering prompt on website -->
  <div id="heroCard" class="hero-card" style="display: none;">
    <div class="hero-title">What would you like to build or modify?</div>
    <div class="hero-subtitle">
      Type your request directly below to launch the workflow. You can also configure the pipeline stages and architecture stack above.
    </div>
    <textarea id="heroPromptInput" class="hero-textarea" placeholder="E.g., Add order cancellation feature with refund policy and status badges..."></textarea>
    <div class="button-group">
      <span class="hint">Shortcut: Cmd/Ctrl + Enter</span>
      <button class="btn-approve" onclick="submitInitialPrompt()">&#128640; Start Workflow</button>
    </div>
  </div>

  <!-- Stage execution section -->
  <div id="stageCardContainer" style="display: none; flex-direction: column; gap: 16px;">
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
  </div>
</main>

<script>
  let currentState = null;

  function renderStepper(stages, currentStage, status) {
    const el = document.getElementById("stepper");
    el.innerHTML = (stages || []).map(s => {
      let cls = "step";
      if (!s.enabled) {
        cls += " skipped";
      } else if (status === "awaiting_prompt") {
        if (s.id === 1) cls += " active";
      } else if (s.id < currentStage || (s.id === currentStage && status === "completed")) {
        cls += " completed";
      } else if (s.id === currentStage) {
        cls += " active";
      }
      const numContent = !s.enabled ? "&#8212;" : (status !== "awaiting_prompt" && (s.id < currentStage || (s.id === currentStage && status === "completed")) ? "&#10003;" : s.id);
      return `
        <div class="${cls}">
          <div class="step-num">${numContent}</div>
          <div class="step-info">
            <div class="step-title">${s.name} ${s.locked ? "🔒" : ""} ${!s.enabled ? "(Skipped)" : ""}</div>
            <div class="step-desc">${s.desc}</div>
          </div>
        </div>
      `;
    }).join("");
  }

  function renderConfigGrid(stages, selectedStack) {
    const grid = document.getElementById("configGrid");
    grid.innerHTML = (stages || []).map(s => {
      const toggleLabel = s.locked ? "🔒 Locked" : (s.enabled ? "&#10003; Enabled" : "Skipped");
      const toggleCls = s.locked ? "stage-toggle locked" : (s.enabled ? "stage-toggle enabled" : "stage-toggle");
      const toggleDisabled = s.locked ? "disabled" : "";

      const skillChips = (s.skills || []).map(sk => {
        let isVis = sk.enabled;
        if (sk.group === "stack") {
          isVis = (sk.name === "project-react-architecture" && selectedStack === "react") ||
                  (sk.name === "project-go-architecture" && selectedStack === "go");
        }
        if (!isVis && sk.group === "stack") return "";
        return `<span class="skill-chip ${isVis ? 'active' : ''}">${sk.name}</span>`;
      }).filter(Boolean).join("");

      return `
        <div class="stage-config-card">
          <div class="stage-config-title">
            <span>${s.name}</span>
            <button class="${toggleCls}" ${toggleDisabled} onclick="toggleStage(${s.id})">${toggleLabel}</button>
          </div>
          <div class="skill-chips">${skillChips || '<span class="hint">No stack skill</span>'}</div>
        </div>
      `;
    }).join("");

    ["react", "go", "none"].forEach(st => {
      const btn = document.getElementById("stack-" + st);
      if (btn) btn.className = st === selectedStack ? "stack-btn selected" : "stack-btn";
    });
  }

  function highlightArtifact(text) {
    if (!text) return "No content.";
    return text.replace(/\\[(NEW|UPDATE|REUSE|PROMOTE|DELETE)\\]/g, '<span class="badge-tag tag-$1">[$1]</span>');
  }

  function updateUI(state) {
    currentState = state;
    renderStepper(state.stages, state.current_stage || 1, state.status || "in_progress");
    renderConfigGrid(state.stages, state.selected_stack || "none");

    const heroCard = document.getElementById("heroCard");
    const stageContainer = document.getElementById("stageCardContainer");

    if (state.status === "awaiting_prompt") {
      heroCard.style.display = "flex";
      stageContainer.style.display = "none";
      document.getElementById("requestText").textContent = "Enter your prompt below to start";
      setTimeout(() => document.getElementById("heroPromptInput").focus(), 100);
      return;
    }

    heroCard.style.display = "none";
    stageContainer.style.display = "flex";

    document.getElementById("requestText").textContent = state.request || "Running project-workflow";

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

  async function submitInitialPrompt() {
    const input = document.getElementById("heroPromptInput");
    const text = input.value.trim();
    if (!text) {
      alert("Please enter what you want to build or modify.");
      input.focus();
      return;
    }

    try {
      const res = await fetch("/api/action", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "start_workflow", text: text })
      });
      if (res.ok) {
        const data = await res.json();
        updateUI(data);
      }
    } catch (e) {
      alert("Failed to start workflow: " + e.message);
    }
  }

  async function toggleStage(stageId) {
    try {
      const res = await fetch("/api/config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ toggle_stage: stageId })
      });
      if (res.ok) {
        const data = await res.json();
        updateUI(data);
      }
    } catch (e) {
      alert("Failed to toggle stage: " + e.message);
    }
  }

  async function selectStack(stackName) {
    try {
      const res = await fetch("/api/config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ selected_stack: stackName })
      });
      if (res.ok) {
        const data = await res.json();
        updateUI(data);
      }
    } catch (e) {
      alert("Failed to set stack: " + e.message);
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

  document.getElementById("heroPromptInput").addEventListener("keydown", function(e) {
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
      submitInitialPrompt();
    }
  });

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
        detected = detect_project_stack(project_root)
        return {
            "current_stage": 1,
            "status": "awaiting_prompt",
            "request": "",
            "stage_title": "Stage 1 — Grill",
            "content": "",
            "selected_stack": detected,
            "stages": default_stages(detected),
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


def get_next_enabled_stage(state: Dict[str, Any], current_stage: int) -> Optional[int]:
    stages = state.get("stages", [])
    for s in stages:
        if s.get("id", 0) > current_stage and s.get("enabled", True):
            return s.get("id")
    return None


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
        return

    def do_HEAD(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()

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
        length = int(self.headers.get("Content-Length", 0))
        payload = json.loads(self.rfile.read(length).decode("utf-8")) if length > 0 else {}
        state = read_state(self.project_root)

        if parsed.path == "/api/action":
            action_type = payload.get("action", "approve")
            text = payload.get("text", "").strip()

            if action_type == "start_workflow":
                state["request"] = text
                state["status"] = "in_progress"
                state["current_stage"] = 1
                state["stage_title"] = "Stage 1 — Grill"
                state["content"] = f"Workflow started for: '{text}'. Inspecting repository and checking terminology..."
                state["pending_action"] = {
                    "action": "start_workflow",
                    "text": text,
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                }
            else:
                state["pending_action"] = {
                    "action": action_type,
                    "text": text,
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                }
                state["status"] = "in_progress"

            write_state(self.project_root, state)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(state).encode("utf-8"))

        elif parsed.path == "/api/config":
            if "toggle_stage" in payload:
                target_id = payload["toggle_stage"]
                for s in state.get("stages", []):
                    if s.get("id") == target_id and not s.get("locked"):
                        s["enabled"] = not s.get("enabled", True)

            if "selected_stack" in payload:
                new_stack = payload["selected_stack"]
                state["selected_stack"] = new_stack
                for s in state.get("stages", []):
                    for sk in s.get("skills", []):
                        if sk.get("group") == "stack":
                            sk["enabled"] = (sk["name"] == "project-react-architecture" and new_stack == "react") or \
                                            (sk["name"] == "project-go-architecture" and new_stack == "go")

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

    server = ThreadedServer(("0.0.0.0", port), WorkflowHTTPHandler)
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
            time.sleep(0.2)
            try:
                os.kill(pid, signal.SIGKILL)
            except OSError:
                pass
        except Exception:
            pass
        pid_file.unlink(missing_ok=True)

    if state_file.is_file():
        state_file.unlink(missing_ok=True)


def cmd_serve(args: argparse.Namespace) -> int:
    """Run server in foreground (used by detached background worker)."""
    root = pathlib.Path(args.root).resolve()
    port = args.port
    WorkflowHTTPHandler.project_root = root

    class ThreadedServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
        allow_reuse_address = True

    try:
        server = ThreadedServer(("0.0.0.0", port), WorkflowHTTPHandler)
    except OSError:
        server = ThreadedServer(("127.0.0.1", port), WorkflowHTTPHandler)

    WorkflowHTTPHandler.server_instance = server
    try:
        server.serve_forever()
    except (KeyboardInterrupt, SystemExit):
        server.shutdown()
    return 0


def cmd_start(args: argparse.Namespace) -> int:
    root = pathlib.Path(args.root).resolve()
    state_file = get_state_path(root)
    pid_file = root / WORKFLOW_DIR_NAME / "server.pid"
    log_file = root / WORKFLOW_DIR_NAME / "server.log"
    root_wf = root / WORKFLOW_DIR_NAME
    root_wf.mkdir(parents=True, exist_ok=True)

    # Check if already running
    if pid_file.is_file():
        try:
            pid = int(pid_file.read_text(encoding="utf-8").strip())
            os.kill(pid, 0)
            state = read_state(root)
            port = state.get("port", DEFAULT_PORT)
            url = f"http://127.0.0.1:{port}"
            if not args.no_browser:
                try:
                    webbrowser.open(url)
                except Exception:
                    pass
            print(json.dumps({"status": "already_running", "url": url, "port": port, "pid": pid}))
            return 0
        except OSError:
            pid_file.unlink(missing_ok=True)

    port = find_free_port(args.port)
    detected = detect_project_stack(root)
    req = args.request or ""
    status = "in_progress" if req else "awaiting_prompt"
    initial_state = {
        "current_stage": 1,
        "status": status,
        "request": req,
        "stage_title": "Stage 1 — Grill",
        "content": "Starting Stage 1 (/project-grill)... Inspecting repository and checking terminology." if req else "",
        "selected_stack": detected,
        "stages": default_stages(detected),
        "pending_action": None,
        "port": port,
    }
    write_state(root, initial_state)

    # Spawn background daemon process
    cmd = [
        sys.executable,
        str(pathlib.Path(__file__).resolve()),
        "--serve",
        "--root", str(root),
        "--port", str(port),
    ]

    log_fp = open(log_file, "a", encoding="utf-8")
    proc = subprocess.Popen(
        cmd,
        stdout=log_fp,
        stderr=log_fp,
        start_new_session=True,
    )
    pid_file.write_text(str(proc.pid), encoding="utf-8")

    # Poll until server responds with 200 OK
    url = f"http://127.0.0.1:{port}"
    server_ready = False
    for _ in range(40):
        try:
            with urllib.request.urlopen(f"{url}/api/state", timeout=0.2) as resp:
                if resp.status == 200:
                    server_ready = True
                    break
        except Exception:
            time.sleep(0.1)

    if not server_ready:
        print(json.dumps({"status": "failed_to_start", "port": port, "log": str(log_file)}))
        return 1

    if not args.no_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass

    print(json.dumps({"status": "running", "url": url, "port": port, "pid": proc.pid, "state_file": str(state_file)}))
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


def cmd_next_stage(args: argparse.Namespace) -> int:
    root = pathlib.Path(args.root).resolve()
    state = read_state(root)
    next_stage = get_next_enabled_stage(state, args.from_stage)
    print(json.dumps({"from_stage": args.from_stage, "next_enabled_stage": next_stage}))
    return 0


def cmd_wait(args: argparse.Namespace) -> int:
    root = pathlib.Path(args.root).resolve()
    start_time = time.time()
    timeout = args.timeout

    while True:
        state = read_state(root)
        action = state.get("pending_action")
        if action:
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
    sub.add_argument("--serve", action="store_true", help="Internal daemon server process")
    sub.add_argument("--update", action="store_true", help="Update the stage content and status")
    sub.add_argument("--next-stage", dest="from_stage", type=int, help="Get next enabled stage skipping disabled stages")
    sub.add_argument("--wait", action="store_true", help="Wait for user action from the Web UI")
    sub.add_argument("--stop", action="store_true", help="Stop server and clean up .workflow/")

    # Start options
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"Server port (default: {DEFAULT_PORT})")
    parser.add_argument("--no-browser", action="store_true", help="Do not open browser automatically")

    # Update options
    parser.add_argument("--stage", type=int, choices=[1, 2, 3, 4], help="Workflow stage number (1-4)")
    parser.add_argument("--status", choices=["awaiting_prompt", "in_progress", "waiting_approval", "completed"], help="Stage status")
    parser.add_argument("--title", help="Stage card title")
    parser.add_argument("--request", help="Initial user request prompt")
    parser.add_argument("--content", help="Stage artifact text or diff")
    parser.add_argument("--content-file", help="Path to file containing stage artifact text")

    # Wait options
    parser.add_argument("--timeout", type=int, default=600, help="Wait timeout in seconds (default: 600)")

    args = parser.parse_args(argv)

    if args.serve:
        return cmd_serve(args)
    if args.start:
        return cmd_start(args)
    if args.update:
        return cmd_update(args)
    if args.from_stage is not None:
        return cmd_next_stage(args)
    if args.wait:
        return cmd_wait(args)
    if args.stop:
        return cmd_stop(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
