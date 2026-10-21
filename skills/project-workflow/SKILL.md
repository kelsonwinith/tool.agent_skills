---
name: project-workflow
description: "End-to-end gated project workflow orchestrator (/project-workflow). Calling /project-workflow immediately launches a local browser website where you enter your prompt directly, configure stages and architecture stacks, review artifacts, and approve each step. Auto-installs missing companion workflow and stack skills on first run, and guides any feature addition, modification, removal, or refactor through the configured stages: Stage 1 (/project-grill: 🔒 forced), Stage 2 (/project-documentation: toggleable), Stage 3 (/project-plan: toggleable), and Stage 4 (/project-implement: 🔒 forced). Use whenever the user invokes /project-workflow."
license: MIT
compatibility: "Requires Python 3 (standard library only) and Node/npx (for auto-installing missing companion skills via the skills CLI)."
metadata:
  version: 1.4.0
---

# Project Workflow

`project-workflow` is the master entrypoint for building, modifying, refactoring, or removing features in any repository. Calling `/project-workflow` **immediately launches a local browser dashboard** where the prompt happens directly on the website, letting you enter requests, configure pipeline stages and architecture stacks, review stage artifacts, and click through approval gates.

```text
/project-workflow
   │
   ├─► Step 0: Directly launches website at http://localhost:4321
   │          (User enters prompt & configures stages directly on the website)
   │
   ├─► Stage 1: /project-grill     (🔒 FORCED: design-tree interview + conflict check)  ──► [WEB APPROVAL]
   ├─► Stage 2: /project-documentation (TOGGLEABLE: sync docs/, flows, ADRs + linters)  ──► [WEB APPROVAL]
   ├─► Stage 3: /project-plan      (TOGGLEABLE: scan layers + ONLY ### Proposed File Tree)──► [WEB APPROVAL]
   └─► Stage 4: /project-implement (🔒 FORCED: code implementation & verification)      ──► [COMPLETED]
```

---

## Direct Web Launch & Web-First Prompting

When the user calls `/project-workflow`:

```bash
# 1. Bootstrap companion skills if missing
python3 <path-to-project-workflow>/scripts/bootstrap_workflow.py

# 2. Launch the local website directly (opens browser automatically)
python3 <path-to-project-workflow>/scripts/workflow_ui.py --start
```

### Initial Prompt on the Website
1. If the user invoked `/project-workflow` without a prompt, the website displays the **Prompt Hero Card**:
   - Headline: *"What would you like to build or modify?"*
   - Textarea to enter feature requests, bug fixes, or refactors.
   - Stage toggles (enable/disable Stage 2 Docs or Stage 3 Plan) and Stack Selector (`React`, `Go`, `Generic Clean`).
   - Button: **`🚀 Start Workflow`** (or `Cmd/Ctrl + Enter`).
2. Tell the user in chat:
   > *"I've launched the Project Workflow website at [http://localhost:4321](http://localhost:4321). Please enter what you want to build or modify directly on the website."*
3. Wait for the user to submit their prompt from the website:
   ```bash
   python3 <path-to-project-workflow>/scripts/workflow_ui.py --wait
   ```
   This returns JSON with the submitted prompt: `{"action": "start_workflow", "text": "<user-prompt>"}`.
4. If the user passed a prompt directly in chat (e.g. `/project-workflow "add cancellation"`), start the server with `--request "<request>"` and proceed directly to Stage 1.

---

## Interactive Stages via the Website

After receiving the prompt, execute each stage and post the output to the website, waiting for the user to approve on the website:

### Stage 1 — Grill the Request (`/project-grill` — 🔒 FORCED)
1. Read existing code and `docs/` silently; check terminology against `docs/ubiquitous-language.md` and requirements against `docs/product.md` / `docs/flows/`.
2. Conduct the design-tree interview and formulate the **Agreed Design Summary**.
3. Update the website and wait for the user to answer or click **Approve & Next Step**:
   ```bash
   python3 <path-to-project-workflow>/scripts/workflow_ui.py --update --stage 1 --status waiting_approval --title "Agreed Design Summary" --content "<summary-text>"
   python3 <path-to-project-workflow>/scripts/workflow_ui.py --wait
   ```

### Check Next Enabled Stage
Before entering Stage 2 or 3, check whether the user toggled the stage on or off:
```bash
python3 <path-to-project-workflow>/scripts/workflow_ui.py --next-stage <current_stage>
```
If a stage is skipped (`enabled: false`), advance directly to the next enabled stage.

### Stage 2 — Synchronize Documentation (`/project-documentation` — Toggleable)
*(Skip if disabled in Web UI)*
1. Update `docs/ubiquitous-language.md`, `docs/product.md`, `docs/architecture.md`, `docs/flows/<NNN>-<name>.md`, or `docs/decisions/<NNN>-<name>.md`.
2. Run `docs_lint.py`, `glossary_lint.py`, and `adr_scan.py`.
3. Update the website and wait for approval:
   ```bash
   python3 <path-to-project-workflow>/scripts/workflow_ui.py --update --stage 2 --status waiting_approval --title "Documentation Validated" --content "<docs-summary>"
   python3 <path-to-project-workflow>/scripts/workflow_ui.py --wait
   ```

### Stage 3 — Architecture & File Tree Plan (`/project-plan` — Toggleable)
*(Skip if disabled in Web UI)*
1. Scan layers according to the active stack skill (`selected_stack` from state: `project-react-architecture` or `project-go-architecture`).
2. Output **ONLY** `### Proposed File Tree` with `# [NEW] | [UPDATE] | [REUSE] | [PROMOTE] | [DELETE]` tags.
3. Update the website and wait for approval:
   ```bash
   python3 <path-to-project-workflow>/scripts/workflow_ui.py --update --stage 3 --status waiting_approval --title "Proposed File Tree" --content "<file-tree>"
   python3 <path-to-project-workflow>/scripts/workflow_ui.py --wait
   ```

### Stage 4 — Implement & Verify (`/project-implement` — 🔒 FORCED)
1. Execute the approved file tree precisely.
2. Enforce canonical glossary names and stack architecture invariants.
3. Run project verification (tests, linters, build + doc linters).
4. Update the website to `completed` (the server remains active in a full-loop cycle; do NOT stop the server):
   ```bash
   python3 <path-to-project-workflow>/scripts/workflow_ui.py --update --stage 4 --status completed --title "Implementation Complete" --content "<results>"
   ```
5. Report completion to the user:
   > *"Workflow cycle completed! The verified implementation and tests are in place. The dashboard remains open at [http://localhost:4321](http://localhost:4321) where you can review results or click **Start New Task** to run another workflow."*

---

## Full Loop Cycle & Server Lifecycle

- **Persistent Connection**: The server maintains an open connection across task cycles. It does not terminate when a task completes.
- **Starting Another Task**: The user can click **"New Task"** or **"Start New Task"** in the Web UI anytime. This resets the dashboard to the prompt input while archiving past completed tasks into the session history.
- **Next Loop Waiting**: If orchestrating continuous workflows, wait for the next user task with:
  ```bash
  python3 <path-to-project-workflow>/scripts/workflow_ui.py --wait
  ```
- **Stopping Server**: To explicitly terminate the background server and clean up `.workflow/`:
  ```bash
  python3 <path-to-project-workflow>/scripts/workflow_ui.py --stop
  ```
