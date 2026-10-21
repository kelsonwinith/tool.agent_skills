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
<title>Project Workflow — Full Loop Dashboard</title>
<style>
  :root {
    --background: 0 0% 100%;
    --foreground: 240 10% 3.9%;
    --card: 0 0% 100%;
    --card-foreground: 240 10% 3.9%;
    --popover: 0 0% 100%;
    --popover-foreground: 240 10% 3.9%;
    --primary: 240 5.9% 10%;
    --primary-foreground: 0 0% 98%;
    --secondary: 240 4.8% 95.9%;
    --secondary-foreground: 240 5.9% 10%;
    --muted: 240 4.8% 95.9%;
    --muted-foreground: 240 3.8% 46.1%;
    --accent: 240 4.8% 95.9%;
    --accent-foreground: 240 5.9% 10%;
    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 0 0% 98%;
    --border: 240 5.9% 90%;
    --input: 240 5.9% 90%;
    --ring: 240 5.9% 10%;
    --radius: 0.5rem;
    --success: 142.1 76.2% 36.3%;
    --success-foreground: 355.7 100% 97.3%;
    --warning: 38 92% 50%;
    --warning-foreground: 48 96% 89%;
    --info: 217.2 91.2% 59.8%;
  }

  .dark {
    --background: 240 10% 3.9%;
    --foreground: 0 0% 98%;
    --card: 240 10% 3.9%;
    --card-foreground: 0 0% 98%;
    --popover: 240 10% 3.9%;
    --popover-foreground: 0 0% 98%;
    --primary: 0 0% 98%;
    --primary-foreground: 240 5.9% 10%;
    --secondary: 240 3.7% 15.9%;
    --secondary-foreground: 0 0% 98%;
    --muted: 240 3.7% 15.9%;
    --muted-foreground: 240 5% 64.9%;
    --accent: 240 3.7% 15.9%;
    --accent-foreground: 0 0% 98%;
    --destructive: 0 62.8% 30.6%;
    --destructive-foreground: 0 0% 98%;
    --border: 240 3.7% 15.9%;
    --input: 240 3.7% 15.9%;
    --ring: 240 4.9% 83.9%;
    --success: 142.1 70.6% 45.3%;
    --success-foreground: 144.9 80.4% 10%;
    --warning: 48 96% 53%;
    --warning-foreground: 26 83% 14%;
    --info: 217.2 91.2% 59.8%;
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    background-color: hsl(var(--background));
    color: hsl(var(--foreground));
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    line-height: 1.5;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }

  /* Header */
  header {
    background-color: hsl(var(--card));
    border-bottom: 1px solid hsl(var(--border));
    padding: 12px 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 12px;
    position: sticky;
    top: 0;
    z-index: 50;
  }

  .brand-group {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .live-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background-color: hsl(var(--success));
    box-shadow: 0 0 0 2px hsl(var(--success) / 0.2);
    animation: livePulse 2s infinite ease-in-out;
  }

  @keyframes livePulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.6; transform: scale(0.85); }
  }

  .brand-title {
    font-size: 15px;
    font-weight: 600;
    letter-spacing: -0.015em;
    color: hsl(var(--foreground));
  }

  .badge-subtle {
    font-size: 11px;
    font-weight: 500;
    padding: 2px 8px;
    border-radius: 9999px;
    background-color: hsl(var(--secondary));
    color: hsl(var(--secondary-foreground));
    border: 1px solid hsl(var(--border));
  }

  .header-actions {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
  }

  /* Segmented Controls (shadcn Tabs style) */
  .segmented-control {
    display: inline-flex;
    align-items: center;
    background-color: hsl(var(--muted));
    padding: 3px;
    border-radius: var(--radius);
    gap: 2px;
    border: 1px solid hsl(var(--border));
  }

  .segmented-btn {
    appearance: none;
    background: transparent;
    border: none;
    color: hsl(var(--muted-foreground));
    padding: 4px 10px;
    font-size: 12px;
    font-weight: 500;
    border-radius: calc(var(--radius) - 2px);
    cursor: pointer;
    transition: all 0.15s ease;
    display: inline-flex;
    align-items: center;
    gap: 5px;
    white-space: nowrap;
  }

  .segmented-btn:hover {
    color: hsl(var(--foreground));
  }

  .segmented-btn.active {
    background-color: hsl(var(--card));
    color: hsl(var(--foreground));
    box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  }

  /* Buttons */
  .btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    font-size: 13px;
    font-weight: 500;
    padding: 6px 12px;
    border-radius: var(--radius);
    cursor: pointer;
    transition: all 0.15s ease;
    border: 1px solid transparent;
    text-decoration: none;
    line-height: 1;
  }

  .btn:focus-visible {
    outline: none;
    box-shadow: 0 0 0 2px hsl(var(--background)), 0 0 0 4px hsl(var(--ring));
  }

  .btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .btn-primary {
    background-color: hsl(var(--primary));
    color: hsl(var(--primary-foreground));
  }

  .btn-primary:hover:not(:disabled) {
    opacity: 0.92;
  }

  .btn-secondary {
    background-color: hsl(var(--secondary));
    color: hsl(var(--secondary-foreground));
    border-color: hsl(var(--border));
  }

  .btn-secondary:hover:not(:disabled) {
    background-color: hsl(var(--muted));
  }

  .btn-outline {
    background-color: transparent;
    color: hsl(var(--foreground));
    border-color: hsl(var(--border));
  }

  .btn-outline:hover:not(:disabled) {
    background-color: hsl(var(--secondary));
  }

  .btn-success {
    background-color: hsl(var(--success));
    color: #ffffff;
  }

  .btn-success:hover:not(:disabled) {
    opacity: 0.92;
  }

  .btn-sm {
    font-size: 12px;
    padding: 4px 8px;
    border-radius: calc(var(--radius) - 2px);
  }

  /* Goal / Banner Bar */
  .goal-bar {
    background-color: hsl(var(--card));
    border-bottom: 1px solid hsl(var(--border));
    padding: 10px 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 16px;
    font-size: 13px;
  }

  .goal-text-group {
    display: flex;
    align-items: center;
    gap: 8px;
    overflow: hidden;
  }

  .goal-label {
    font-weight: 600;
    color: hsl(var(--muted-foreground));
    text-transform: uppercase;
    font-size: 11px;
    letter-spacing: 0.05em;
  }

  .goal-value {
    font-weight: 500;
    color: hsl(var(--foreground));
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  /* Status Badges */
  .status-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 3px 10px;
    border-radius: 9999px;
    font-size: 12px;
    font-weight: 500;
    border: 1px solid transparent;
    white-space: nowrap;
  }

  .status-awaiting_prompt {
    background-color: hsl(var(--secondary));
    color: hsl(var(--secondary-foreground));
    border-color: hsl(var(--border));
  }

  .status-in_progress {
    background-color: hsl(var(--info) / 0.12);
    color: hsl(var(--info));
    border-color: hsl(var(--info) / 0.3);
  }

  .status-waiting_approval {
    background-color: hsl(var(--warning) / 0.15);
    color: hsl(var(--warning));
    border-color: hsl(var(--warning) / 0.3);
  }

  .status-completed {
    background-color: hsl(var(--success) / 0.15);
    color: hsl(var(--success));
    border-color: hsl(var(--success) / 0.3);
  }

  /* Stepper */
  .stepper-container {
    background-color: hsl(var(--background));
    border-bottom: 1px solid hsl(var(--border));
    padding: 14px 24px;
  }

  .stepper {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    max-width: 1200px;
    margin: 0 auto;
  }

  @media (max-width: 768px) {
    .stepper { grid-template-columns: 1fr; }
  }

  .step-card {
    background-color: hsl(var(--card));
    border: 1px solid hsl(var(--border));
    border-radius: var(--radius);
    padding: 12px 14px;
    display: flex;
    align-items: flex-start;
    gap: 12px;
    transition: all 0.15s ease;
  }

  .step-card.active {
    border-color: hsl(var(--ring));
    box-shadow: 0 0 0 1px hsl(var(--ring));
  }

  .step-card.completed {
    border-color: hsl(var(--success) / 0.5);
    background-color: hsl(var(--success) / 0.04);
  }

  .step-card.skipped {
    opacity: 0.45;
    background-color: hsl(var(--muted) / 0.3);
  }

  .step-badge-num {
    width: 24px;
    height: 24px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    font-weight: 600;
    flex-shrink: 0;
    background-color: hsl(var(--muted));
    color: hsl(var(--muted-foreground));
    border: 1px solid hsl(var(--border));
  }

  .step-card.active .step-badge-num {
    background-color: hsl(var(--primary));
    color: hsl(var(--primary-foreground));
    border-color: hsl(var(--primary));
  }

  .step-card.completed .step-badge-num {
    background-color: hsl(var(--success));
    color: #ffffff;
    border-color: hsl(var(--success));
  }

  .step-details {
    overflow: hidden;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .step-name {
    font-size: 13px;
    font-weight: 600;
    color: hsl(var(--foreground));
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .step-desc {
    font-size: 11px;
    color: hsl(var(--muted-foreground));
    line-height: 1.3;
  }

  /* Configuration bar */
  .config-section {
    background-color: hsl(var(--card));
    border-bottom: 1px solid hsl(var(--border));
    padding: 12px 24px;
  }

  .config-inner {
    max-width: 1200px;
    margin: 0 auto;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .config-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 12px;
    font-weight: 500;
    color: hsl(var(--muted-foreground));
  }

  .config-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
  }

  @media (max-width: 768px) {
    .config-grid { grid-template-columns: 1fr; }
  }

  .stage-config-card {
    background-color: hsl(var(--background));
    border: 1px solid hsl(var(--border));
    border-radius: var(--radius);
    padding: 10px 12px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .stage-config-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 12px;
    font-weight: 600;
  }

  .skill-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
  }

  .skill-chip {
    font-size: 10px;
    padding: 2px 6px;
    border-radius: calc(var(--radius) - 3px);
    background-color: hsl(var(--muted));
    border: 1px solid hsl(var(--border));
    color: hsl(var(--muted-foreground));
    font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  }

  .skill-chip.active {
    background-color: hsl(var(--primary) / 0.1);
    border-color: hsl(var(--primary) / 0.3);
    color: hsl(var(--foreground));
    font-weight: 500;
  }

  /* Main Container */
  main {
    flex: 1;
    max-width: 1200px;
    width: 100%;
    margin: 0 auto;
    padding: 24px;
    display: flex;
    flex-direction: column;
    gap: 20px;
  }

  /* Cards (shadcn Card style) */
  .shadcn-card {
    background-color: hsl(var(--card));
    border: 1px solid hsl(var(--border));
    border-radius: var(--radius);
    padding: 20px;
    box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.05);
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .card-header-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid hsl(var(--border));
    padding-bottom: 14px;
  }

  .card-headline {
    font-size: 16px;
    font-weight: 600;
    letter-spacing: -0.01em;
    color: hsl(var(--foreground));
  }

  .card-subtext {
    font-size: 13px;
    color: hsl(var(--muted-foreground));
    margin-top: 2px;
  }

  /* Textarea (shadcn Input style) */
  .shadcn-textarea {
    width: 100%;
    background-color: transparent;
    border: 1px solid hsl(var(--input));
    border-radius: var(--radius);
    padding: 12px 14px;
    font-family: inherit;
    font-size: 14px;
    line-height: 1.5;
    color: hsl(var(--foreground));
    outline: none;
    resize: vertical;
    transition: border-color 0.15s ease, box-shadow 0.15s ease;
  }

  .shadcn-textarea:focus {
    border-color: hsl(var(--ring));
    box-shadow: 0 0 0 2px hsl(var(--ring) / 0.15);
  }

  .shadcn-textarea::placeholder {
    color: hsl(var(--muted-foreground));
  }

  /* Artifact Viewer */
  .artifact-viewer {
    background-color: hsl(var(--muted) / 0.3);
    border: 1px solid hsl(var(--border));
    border-radius: var(--radius);
    padding: 16px;
    font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
    font-size: 13px;
    line-height: 1.6;
    color: hsl(var(--foreground));
    white-space: pre-wrap;
    overflow-x: auto;
    max-height: 460px;
    overflow-y: auto;
  }

  .badge-tag {
    display: inline-block;
    padding: 1px 6px;
    border-radius: 4px;
    font-weight: 600;
    font-size: 11px;
    margin-right: 4px;
    line-height: 1.4;
  }

  .tag-NEW { background: hsl(var(--success) / 0.15); color: hsl(var(--success)); border: 1px solid hsl(var(--success) / 0.3); }
  .tag-UPDATE { background: hsl(var(--info) / 0.15); color: hsl(var(--info)); border: 1px solid hsl(var(--info) / 0.3); }
  .tag-REUSE { background: hsl(var(--muted)); color: hsl(var(--muted-foreground)); border: 1px solid hsl(var(--border)); }
  .tag-PROMOTE { background: rgba(168, 85, 247, 0.15); color: rgb(168, 85, 247); border: 1px solid rgba(168, 85, 247, 0.3); }
  .tag-DELETE { background: hsl(var(--destructive) / 0.15); color: hsl(var(--destructive)); border: 1px solid hsl(var(--destructive) / 0.3); }

  /* Completion alert box */
  .completed-alert {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    padding: 14px 18px;
    border-radius: var(--radius);
    background-color: hsl(var(--success) / 0.08);
    border: 1px solid hsl(var(--success) / 0.3);
  }

  .completed-text {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .completed-title {
    font-size: 14px;
    font-weight: 600;
    color: hsl(var(--foreground));
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .completed-desc {
    font-size: 12px;
    color: hsl(var(--muted-foreground));
  }

  /* History list */
  .history-section {
    margin-top: 8px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .history-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
    padding: 8px 12px;
    background-color: hsl(var(--muted) / 0.4);
    border: 1px solid hsl(var(--border));
    border-radius: var(--radius);
    font-size: 13px;
  }

  .history-request {
    font-weight: 500;
    color: hsl(var(--foreground));
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .history-meta {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-shrink: 0;
    font-size: 11px;
    color: hsl(var(--muted-foreground));
  }

  /* Footer shortcuts */
  .footer-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
  }

  .shortcut-hint {
    font-size: 12px;
    color: hsl(var(--muted-foreground));
    display: inline-flex;
    align-items: center;
    gap: 4px;
  }

  kbd {
    background-color: hsl(var(--muted));
    border: 1px solid hsl(var(--border));
    border-radius: 4px;
    padding: 2px 5px;
    font-size: 11px;
    font-family: inherit;
    color: hsl(var(--foreground));
  }
</style>
</head>
<body>

<header>
  <div class="brand-group">
    <div class="live-dot" title="Server active"></div>
    <span class="brand-title">Project Workflow</span>
    <span class="badge-subtle">Full Loop</span>
  </div>

  <div class="header-actions">
    <!-- Architecture Stack Selector -->
    <div class="segmented-control" role="radiogroup" aria-label="Architecture Stack">
      <button type="button" class="segmented-btn" id="stack-react" onclick="selectStack('react')">React / Next</button>
      <button type="button" class="segmented-btn" id="stack-go" onclick="selectStack('go')">Go Hexagonal</button>
      <button type="button" class="segmented-btn" id="stack-none" onclick="selectStack('none')">Generic Clean</button>
    </div>

    <!-- Theme Switcher: Light / Dark / System -->
    <div class="segmented-control" role="radiogroup" aria-label="Theme">
      <button type="button" class="segmented-btn" id="theme-light" onclick="setTheme('light')" title="Light Theme">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/></svg>
        <span>Light</span>
      </button>
      <button type="button" class="segmented-btn" id="theme-dark" onclick="setTheme('dark')" title="Dark Theme">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/></svg>
        <span>Dark</span>
      </button>
      <button type="button" class="segmented-btn" id="theme-system" onclick="setTheme('system')" title="Follow System Theme">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="20" height="14" x="2" y="3" rx="2"/><line x1="8" x2="16" y1="21" y2="21"/><line x1="12" x2="12" y1="17" y2="21"/></svg>
        <span>System</span>
      </button>
    </div>

    <!-- New Task Button -->
    <button type="button" class="btn btn-outline btn-sm" onclick="resetWorkflow()" title="Reset and start another task">
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 5v14"/><path d="M5 12h14"/></svg>
      <span>New Task</span>
    </button>
  </div>
</header>

<div class="goal-bar">
  <div class="goal-text-group">
    <span class="goal-label">Goal</span>
    <span class="goal-value" id="requestText">Awaiting your prompt below...</span>
  </div>
  <div id="statusBadge" class="status-badge status-awaiting_prompt">Awaiting Prompt</div>
</div>

<div class="stepper-container">
  <div class="stepper" id="stepper"></div>
</div>

<div class="config-section">
  <div class="config-inner">
    <div class="config-header">
      <span>PIPELINE STAGES &amp; SKILLS CONFIGURATION</span>
      <span>Stages 1 &amp; 4 are locked 🔒 for workflow integrity</span>
    </div>
    <div class="config-grid" id="configGrid"></div>
  </div>
</div>

<main>
  <!-- Hero Card: When awaiting prompt -->
  <div id="heroCard" class="shadcn-card" style="display: none;">
    <div>
      <h2 class="card-headline">What would you like to build or modify?</h2>
      <p class="card-subtext">Type your request below to launch the workflow. Stages and architecture skills can be configured in the panel above.</p>
    </div>
    <textarea id="heroPromptInput" class="shadcn-textarea" rows="5" placeholder="E.g., Add order cancellation feature with refund policy and status badges..."></textarea>
    <div class="footer-row">
      <span class="shortcut-hint">Press <kbd>Cmd</kbd> or <kbd>Ctrl</kbd> + <kbd>Enter</kbd> to launch</span>
      <button type="button" class="btn btn-primary" onclick="submitInitialPrompt()">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"/></svg>
        <span>Start Workflow</span>
      </button>
    </div>

    <!-- Past runs in current session -->
    <div id="historyContainer" class="history-section" style="display: none;">
      <div class="config-header">
        <span>RECENT TASKS IN THIS SESSION</span>
      </div>
      <div id="historyList"></div>
    </div>
  </div>

  <!-- Stage Execution Card: When in progress, waiting approval, or completed -->
  <div id="stageCardContainer" style="display: none; flex-direction: column; gap: 16px;">
    <!-- Completed Notification Banner -->
    <div id="completedBanner" class="completed-alert" style="display: none;">
      <div class="completed-text">
        <div class="completed-title">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="hsl(var(--success))" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
          <span>Workflow Cycle Completed</span>
        </div>
        <span class="completed-desc">All stages finished successfully. The verified code and documentation are in place.</span>
      </div>
      <button type="button" class="btn btn-primary btn-sm" onclick="resetWorkflow()">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 5v14"/><path d="M5 12h14"/></svg>
        <span>Start New Task</span>
      </button>
    </div>

    <div class="shadcn-card">
      <div class="card-header-row">
        <div>
          <h2 class="card-headline" id="stageTitle">Stage Content</h2>
          <div class="card-subtext" id="timestamp"></div>
        </div>
        <button type="button" class="btn btn-outline btn-sm" id="btnCopy" onclick="copyArtifact()">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="14" height="14" x="8" y="8" rx="2" ry="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/></svg>
          <span id="copyBtnText">Copy Output</span>
        </button>
      </div>

      <div class="artifact-viewer" id="artifactBody">Waiting for agent stage output...</div>

      <div id="actionArea" style="display: flex; flex-direction: column; gap: 12px;">
        <textarea id="feedbackInput" class="shadcn-textarea" rows="3" placeholder="Optional: Type instructions, answers, or adjustments for this stage (Cmd/Ctrl + Enter to approve)..."></textarea>
        <div class="footer-row">
          <span class="shortcut-hint">Press <kbd>Cmd</kbd> or <kbd>Ctrl</kbd> + <kbd>Enter</kbd> to approve</span>
          <div style="display: flex; gap: 8px;">
            <button type="button" id="btnRevise" class="btn btn-outline" onclick="submitAction('revise')">Request Revisions</button>
            <button type="button" id="btnApprove" class="btn btn-success" onclick="submitAction('approve')">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
              <span>Approve &amp; Next Step</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</main>

<script>
  let currentState = null;

  /* Theme Management */
  function getSystemTheme() {
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }

  function applyTheme(theme) {
    localStorage.setItem("workflow-theme", theme);
    const effective = theme === "system" ? getSystemTheme() : theme;
    if (effective === "dark") {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }

    ["light", "dark", "system"].forEach(t => {
      const btn = document.getElementById("theme-" + t);
      if (btn) {
        if (t === theme) {
          btn.classList.add("active");
        } else {
          btn.classList.remove("active");
        }
      }
    });
  }

  function setTheme(theme) {
    applyTheme(theme);
  }

  function initTheme() {
    const saved = localStorage.getItem("workflow-theme") || "system";
    applyTheme(saved);
    window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
      if ((localStorage.getItem("workflow-theme") || "system") === "system") {
        applyTheme("system");
      }
    });
  }

  /* Stepper rendering */
  function renderStepper(stages, currentStage, status) {
    const el = document.getElementById("stepper");
    el.innerHTML = (stages || []).map(s => {
      let cardCls = "step-card";
      let isCompleted = false;
      let isActive = false;

      if (!s.enabled) {
        cardCls += " skipped";
      } else if (status === "awaiting_prompt") {
        if (s.id === 1) { cardCls += " active"; isActive = true; }
      } else if (s.id < currentStage || (s.id === currentStage && status === "completed")) {
        cardCls += " completed";
        isCompleted = true;
      } else if (s.id === currentStage) {
        cardCls += " active";
        isActive = true;
      }

      let badgeContent = s.id;
      if (!s.enabled) {
        badgeContent = "&mdash;";
      } else if (isCompleted) {
        badgeContent = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>`;
      }

      return `
        <div class="${cardCls}">
          <div class="step-badge-num">${badgeContent}</div>
          <div class="step-details">
            <div class="step-name">${s.name} ${s.locked ? "🔒" : ""} ${!s.enabled ? "(Skipped)" : ""}</div>
            <div class="step-desc">${s.desc}</div>
          </div>
        </div>
      `;
    }).join("");
  }

  /* Configuration Grid rendering */
  function renderConfigGrid(stages, selectedStack) {
    const grid = document.getElementById("configGrid");
    grid.innerHTML = (stages || []).map(s => {
      const toggleLabel = s.locked ? "🔒 Locked" : (s.enabled ? "✓ Enabled" : "Skipped");
      const toggleCls = s.locked ? "btn btn-outline btn-sm" : (s.enabled ? "btn btn-secondary btn-sm" : "btn btn-outline btn-sm");
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
          <div class="stage-config-header">
            <span>${s.name}</span>
            <button class="${toggleCls}" ${toggleDisabled} onclick="toggleStage(${s.id})">${toggleLabel}</button>
          </div>
          <div class="skill-chips">${skillChips || '<span class="skill-chip">No stack skill</span>'}</div>
        </div>
      `;
    }).join("");

    ["react", "go", "none"].forEach(st => {
      const btn = document.getElementById("stack-" + st);
      if (btn) {
        if (st === selectedStack) {
          btn.classList.add("active");
        } else {
          btn.classList.remove("active");
        }
      }
    });
  }

  function highlightArtifact(text) {
    if (!text) return "No content.";
    return text.replace(/\\[(NEW|UPDATE|REUSE|PROMOTE|DELETE)\\]/g, '<span class="badge-tag tag-$1">[$1]</span>');
  }

  function renderHistory(history) {
    const container = document.getElementById("historyContainer");
    const list = document.getElementById("historyList");
    if (!history || history.length === 0) {
      container.style.display = "none";
      return;
    }
    container.style.display = "flex";
    list.innerHTML = history.map(h => {
      const dt = h.completed_at ? new Date(h.completed_at).toLocaleTimeString() : "";
      const reqSafe = (h.request || "").replace(/"/g, '&quot;');
      return `
        <div class="history-item">
          <span class="history-request" title="${reqSafe}">${h.request || "Untitled task"}</span>
          <div class="history-meta">
            <span>${dt}</span>
            <button type="button" class="btn btn-outline btn-sm" onclick="reusePrompt('${reqSafe}')">Reuse</button>
          </div>
        </div>
      `;
    }).join("");
  }

  function reusePrompt(text) {
    const input = document.getElementById("heroPromptInput");
    input.value = text;
    input.focus();
  }

  function updateUI(state) {
    currentState = state;
    renderStepper(state.stages, state.current_stage || 1, state.status || "in_progress");
    renderConfigGrid(state.stages, state.selected_stack || "none");

    const heroCard = document.getElementById("heroCard");
    const stageContainer = document.getElementById("stageCardContainer");
    const statusBadge = document.getElementById("statusBadge");
    const completedBanner = document.getElementById("completedBanner");
    const actionArea = document.getElementById("actionArea");

    const status = state.status || "in_progress";
    statusBadge.className = "status-badge status-" + status;

    let statusLabel = status.replace("_", " ").toUpperCase();
    if (status === "waiting_approval") statusLabel = "Waiting for Your Approval";
    else if (status === "awaiting_prompt") statusLabel = "Awaiting Prompt";
    else if (status === "in_progress") statusLabel = "In Progress";
    else if (status === "completed") statusLabel = "Completed";
    statusBadge.textContent = statusLabel;

    if (status === "awaiting_prompt") {
      heroCard.style.display = "flex";
      stageContainer.style.display = "none";
      document.getElementById("requestText").textContent = "Enter your prompt below to start";
      renderHistory(state.history);
      return;
    }

    heroCard.style.display = "none";
    stageContainer.style.display = "flex";
    document.getElementById("requestText").textContent = state.request || "Running project-workflow";

    document.getElementById("stageTitle").textContent = state.stage_title || ("Stage " + state.current_stage);
    document.getElementById("timestamp").textContent = state.updated_at ? "Updated at " + new Date(state.updated_at).toLocaleTimeString() : "";

    const body = document.getElementById("artifactBody");
    body.innerHTML = highlightArtifact(state.content || "Waiting for agent output...");

    const isWaiting = status === "waiting_approval";
    const isCompleted = status === "completed";

    completedBanner.style.display = isCompleted ? "flex" : "none";
    actionArea.style.display = isCompleted ? "none" : "flex";

    document.getElementById("btnApprove").disabled = !isWaiting && status !== "in_progress";
    document.getElementById("btnRevise").disabled = !isWaiting && status !== "in_progress";
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
        input.value = "";
        const data = await res.json();
        updateUI(data);
      }
    } catch (e) {
      alert("Failed to start workflow: " + e.message);
    }
  }

  async function resetWorkflow() {
    try {
      const res = await fetch("/api/action", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "reset_workflow" })
      });
      if (res.ok) {
        const data = await res.json();
        updateUI(data);
      }
    } catch (e) {
      alert("Failed to reset workflow: " + e.message);
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

  function copyArtifact() {
    const body = document.getElementById("artifactBody");
    const text = body.innerText || body.textContent;
    navigator.clipboard.writeText(text).then(() => {
      const btnText = document.getElementById("copyBtnText");
      btnText.textContent = "Copied!";
      setTimeout(() => { btnText.textContent = "Copy Output"; }, 1500);
    }).catch(err => {
      console.error("Could not copy text: ", err);
    });
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

  initTheme();
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
            "history": [],
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if "history" not in data or not isinstance(data["history"], list):
            data["history"] = []
        return data
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

            if action_type in ("reset_workflow", "new_task"):
                if state.get("request"):
                    if "history" not in state or not isinstance(state["history"], list):
                        state["history"] = []
                    state["history"].insert(0, {
                        "request": state.get("request", ""),
                        "status": state.get("status", "completed"),
                        "stage": state.get("current_stage", 1),
                        "stage_title": state.get("stage_title", ""),
                        "completed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    })
                    state["history"] = state["history"][:20]
                state["status"] = "awaiting_prompt"
                state["request"] = ""
                state["current_stage"] = 1
                state["stage_title"] = "Stage 1 — Grill"
                state["content"] = ""
                state["pending_action"] = None
            elif action_type == "start_workflow":
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
        "history": [],
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
