---
name: project-workflow
description: "End-to-end gated project workflow orchestrator (/project-workflow) with an interactive local Web UI dashboard, stage toggles (forced vs. skippable stages), and stack switching. Auto-installs missing companion workflow and stack skills on first run, launches a local browser dashboard (or operates in dual-mode with terminal chat), and guides any feature addition, modification, removal, or refactor through the configured stages: Stage 1 (/project-grill: 🔒 forced), Stage 2 (/project-documentation: toggleable), Stage 3 (/project-plan: toggleable), and Stage 4 (/project-implement: 🔒 forced). Use whenever the user invokes /project-workflow or asks to run the full project workflow loop."
license: MIT
compatibility: "Requires Python 3 (standard library only) and Node/npx (for auto-installing missing companion skills via the skills CLI)."
metadata:
  version: 1.3.0
---

# Project Workflow

`project-workflow` is the master entrypoint for building, modifying, refactoring, or removing features in any repository. Installing this single skill automatically bootstraps the rest of the workflow suite, launches an interactive local Web UI dashboard, and runs every request through a predictable, approval-gated pipeline.

```text
/project-workflow "<request>"
   │
   ├─► Stage 0: Bootstrap & Web UI (auto-detect stack, launch dashboard at http://localhost:4321)
   │
   ├─► Stage 1: /project-grill     (🔒 FORCED: design-tree interview + conflict check)  ──► [PAUSE FOR APPROVAL]
   ├─► Stage 2: /project-documentation (TOGGLEABLE: sync docs/, flows, ADRs + linters)  ──► [PAUSE FOR APPROVAL]
   ├─► Stage 3: /project-plan      (TOGGLEABLE: scan layers + ONLY ### Proposed File Tree)──► [PAUSE FOR APPROVAL]
   └─► Stage 4: /project-implement (🔒 FORCED: code implementation & verification)      ──► [FINAL SIGN-OFF]
```

---

## Stage Toggling & Skill Inspection

Inside the Web UI dashboard (and `.workflow/state.json`), users can inspect and configure active stages and attached skills:

1. **Forced vs. Skippable Stages**:
   - **Stage 1 (Grill) & Stage 4 (Implement)**: **`🔒 Locked (Forced)`**. These guarantee that requirements are settled before work begins and code is verified before completion.
   - **Stage 2 (Docs) & Stage 3 (Plan)**: **`Toggleable (Skippable)`**. Users can toggle Stage 2 off if building a quick prototype without docs, or toggle Stage 3 off to move directly from Grill to Implementation.
2. **Stack Architecture Selector**:
   - Allows switching between `React / Next.js` (`project-react-architecture`), `Go Hexagonal` (`project-go-architecture`), and `Generic Clean` on the fly.
3. **Automatic Stage Skipping**:
   - When advancing from a stage, check the next enabled stage:
     ```bash
     python3 <path-to-project-workflow>/scripts/workflow_ui.py --next-stage <current_stage>
     ```
   - If a stage is disabled (`enabled: false`), the workflow skips it and advances directly to the next enabled stage.

---

## Dual-Mode: Interactive Web UI & Terminal Chat

When `/project-workflow` runs, it starts a lightweight local server and opens your browser:

```bash
python3 <path-to-project-workflow>/scripts/workflow_ui.py --start --request "<request>"
```

### What You See in the Browser:
- **Visual Stepper**: Track progress across Stage 1 (Grill) → Stage 2 (Docs) → Stage 3 (Plan) → Stage 4 (Implement), with skipped stages struck through.
- **Pipeline & Skills Config Grid**: View attached skills for each stage, toggle optional stages on/off, and select the active architecture stack.
- **Artifact & Diff Viewer**: Formatted view of grilling Q&A, documentation changes, colored file tree badges (`[NEW]`, `[UPDATE]`, `[REUSE]`, `[PROMOTE]`, `[DELETE]`), and verification results.
- **Interactive Action Bar**: Type customized instructions or answers in the text box and click **`Approve & Next Step`** (shortcut `Cmd/Ctrl + Enter`) or **`Request Revisions`**.

Both interfaces stay 100% in sync: you can reply or approve either directly inside the browser or in your chat conversation!

---

## Core Rule: Pause After Every Enabled Stage

Never chain two stages in a single turn without the user's explicit confirmation. At the end of every active stage, present that stage's artifact, update the Web UI status to `waiting_approval`, and **wait for the user to approve** (via browser button or chat) before advancing to the next enabled stage.

---

## Stage 0 — Auto-Bootstrap & UI Startup

```bash
# 1. Bootstrap companion skills
python3 <path-to-project-workflow>/scripts/bootstrap_workflow.py

# 2. Start local dashboard (opens browser automatically)
python3 <path-to-project-workflow>/scripts/workflow_ui.py --start --request "<request>"
```

---

## Stage 1 — Grill the Request (`/project-grill` — 🔒 FORCED)

Load and follow **`project-grill`**:

1. **Silent Discovery**: Read existing code and `docs/` yourself.
2. **Terminology & Requirement Check**: Check `docs/ubiquitous-language.md` and `docs/product.md` / `docs/flows/`.
3. **Design-Tree Interview**: Ask numbered questions with `(Recommended)` default proposals.
4. **Stage 1 Gate Output**: Present the **Agreed Design Summary**, update the Web UI, and ask:
   ```bash
   python3 <path-to-project-workflow>/scripts/workflow_ui.py --update --stage 1 --status waiting_approval --title "Agreed Design Summary" --content "<summary-text>"
   ```
   > *"Stage 1 (Grill) complete. Click **Approve & Next Step** in the browser dashboard or reply **approve** in chat to proceed."*

**STOP and wait for user approval.**

---

## Stage 2 — Synchronize Documentation (`/project-documentation` — Toggleable)

*Skip this stage if toggled off in the Web UI.*

If enabled, load and follow **`project-documentation`**:
1. Update `docs/ubiquitous-language.md`, `docs/product.md`, `docs/architecture.md`, `docs/flows/<NNN>-<name>.md`, or `docs/decisions/<NNN>-<name>.md`.
2. Run `docs_lint.py`, `glossary_lint.py`, and `adr_scan.py`.
3. Update the Web UI with the docs summary and ask:
   ```bash
   python3 <path-to-project-workflow>/scripts/workflow_ui.py --update --stage 2 --status waiting_approval --title "Documentation Validated" --content "<docs-summary>"
   ```
   > *"Stage 2 (Documentation) complete and validated. Click **Approve & Next Step** in the browser or reply **approve** in chat to proceed."*

**STOP and wait for user approval.**

---

## Stage 3 — Architecture & File Tree Plan (`/project-plan` — Toggleable)

*Skip this stage if toggled off in the Web UI.*

If enabled, load **`project-plan`** and the active stack architecture skill (`project-react-architecture`, `project-go-architecture`, or clean architecture):
1. Scan existing layers and include any glossary-driven code renames.
2. Output **ONLY** `### Proposed File Tree` with inline `# [TAG] — what it does` comments.
3. Update the Web UI and ask:
   ```bash
   python3 <path-to-project-workflow>/scripts/workflow_ui.py --update --stage 3 --status waiting_approval --title "Proposed File Tree" --content "<file-tree>"
   ```
   > *"Stage 3 (File Tree Plan) ready. Click **Approve & Next Step** in the browser or reply **approve** in chat to proceed to Stage 4 (`/project-implement`)."*

**STOP and wait for user approval. Do not create or edit source code files during Stage 3.**

---

## Stage 4 — Implement & Verify (`/project-implement` — 🔒 FORCED)

Load and follow **`project-implement`** and the active stack skill:
1. Execute the approved file tree precisely.
2. Enforce canonical glossary names and stack architecture invariants.
3. Run project verification (tests, linters, build + doc linters).
4. Update the Web UI to completed, stop the server, and present the final summary:
   ```bash
   python3 <path-to-project-workflow>/scripts/workflow_ui.py --update --stage 4 --status completed --title "Implementation Complete" --content "<results>"
   python3 <path-to-project-workflow>/scripts/workflow_ui.py --stop
   ```
