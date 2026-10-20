---
name: project-workflow
description: "End-to-end gated project workflow orchestrator (/project-workflow) with an interactive local Web UI dashboard. Auto-installs missing companion workflow and stack skills on first run, launches a local browser dashboard (or operates in dual-mode with terminal chat), and guides any feature addition, modification, removal, or refactor through 4 strict approval-gated stages: Stage 1 (/project-grill: design-tree interview & conflict check), Stage 2 (/project-documentation: canonical glossary, flat singletons, numbered flows/ and decisions/ sync & linter validation), Stage 3 (/project-plan: codebase scan & annotated ### Proposed File Tree), and Stage 4 (/project-implement: stack-compliant implementation & verification). Use whenever the user invokes /project-workflow or asks to run the full project workflow loop."
license: MIT
compatibility: "Requires Python 3 (standard library only) and Node/npx (for auto-installing missing companion skills via the skills CLI)."
metadata:
  version: 1.2.0
---

# Project Workflow

`project-workflow` is the master entrypoint for building, modifying, refactoring, or removing features in any repository. Installing this single skill automatically bootstraps the rest of the workflow suite, launches an interactive local Web UI dashboard, and runs every request through a predictable, four-stage loop with an explicit user approval gate at the end of every stage.

```text
/project-workflow "<request>"
   │
   ├─► Stage 0: Bootstrap & Web UI (auto-detect stack, launch local browser dashboard at http://localhost:4321)
   │
   ├─► Stage 1: /project-grill     (design-tree interview + glossary/requirement check) ──► [PAUSE FOR APPROVAL]
   ├─► Stage 2: /project-documentation (sync docs/ singletons, flows, ADRs + run linters)──► [PAUSE FOR APPROVAL]
   ├─► Stage 3: /project-plan      (scan layers + output ONLY ### Proposed File Tree)   ──► [PAUSE FOR APPROVAL]
   └─► Stage 4: /project-implement (write code per stack architecture + run checks)     ──► [FINAL SIGN-OFF]
```

---

## Dual-Mode: Interactive Web UI & Terminal Chat

When `/project-workflow` runs, it starts a lightweight local server and opens your browser:

```bash
python3 <path-to-project-workflow>/scripts/workflow_ui.py --start --request "<request>"
```

### What You See in the Browser:
- **Visual Stepper**: Track progress across Stage 1 (Grill), Stage 2 (Docs), Stage 3 (Plan), and Stage 4 (Implement).
- **Artifact & Diff Viewer**: Formatted view of grilling Q&A, documentation changes, colored file tree badges (`[NEW]`, `[UPDATE]`, `[REUSE]`, `[PROMOTE]`, `[DELETE]`), and verification results.
- **Interactive Action Bar**: Type customized instructions or answers in the text box and click **`Approve & Next Step`** (shortcut `Cmd/Ctrl + Enter`) or **`Request Revisions`**.

Both interfaces stay 100% in sync: you can reply or approve either directly inside the browser or in your chat conversation!

---

## Core Rule: Pause After Every Stage

Never chain two stages in a single turn without the user's explicit confirmation. At the end of Stage 1, Stage 2, and Stage 3, present that stage's artifact, update the Web UI status, and **wait for the user to approve** (via browser button or chat) before advancing to the next stage.

If the user replies with adjustments instead of approval, stay in the current stage, revise its output, and ask for confirmation again.

---

## Stage 0 — Auto-Bootstrap & UI Startup

Before starting Stage 1, ensure the required companion skills are installed and launch the Web UI:

```bash
# 1. Bootstrap companion skills
python3 <path-to-project-workflow>/scripts/bootstrap_workflow.py

# 2. Start local dashboard (opens browser automatically)
python3 <path-to-project-workflow>/scripts/workflow_ui.py --start --request "<request>"
```

What `bootstrap_workflow.py` does automatically:
1. Checks whether core workflow skills (`project-grill`, `project-documentation`, `project-plan`, `project-implement`) are already installed.
2. Inspects the project root to detect the tech stack:
   - `package.json` containing `"react"` or `"next"` → requires `project-react-architecture`
   - `go.mod` → requires `project-go-architecture`
3. If any required skill is missing, runs `npx skills add kelsonwinith/tool.agent_skills --skill <missing-skills...> -y`.

---

## Stage 1 — Grill the Request (`/project-grill`)

Load and follow the **`project-grill`** skill (`SKILL.md`) with the user's request:

1. **Silent Discovery**: Read relevant code and `docs/` (`docs/ubiquitous-language.md`, `docs/product.md`, `docs/architecture.md`, `docs/flows/`, `docs/decisions/`) yourself. Never ask the user for facts already present in the repository.
2. **Terminology & Requirement Check**:
   - Reconcile every domain word in the request against `docs/ubiquitous-language.md`. Emit a **Terminology Mismatch** block if a term conflicts or changes meaning (noting all code identifiers that must rename with it).
   - Check the request against documented requirements in `docs/product.md` and `docs/flows/`. Emit a **Requirement Mismatch** block if it contradicts an existing rule or flow.
3. **Design-Tree Interview**: Ask only the frontier questions whose prerequisites are settled, numbered, each with a `(Recommended)` default proposal. Wait for answers and repeat until zero assumptions remain.
4. **Stage 1 Gate Output**: Once aligned, update the Web UI and present the **Agreed Design Summary**:
   ```bash
   python3 <path-to-project-workflow>/scripts/workflow_ui.py --update --stage 1 --status waiting_approval --title "Agreed Design Summary" --content "<summary-text>"
   ```
   Then prompt:
   > *"Stage 1 (Grill) complete. Click **Approve & Next Step** in the browser dashboard or reply **approve** in chat to proceed to Stage 2 (`/project-documentation`)."*

**STOP and wait for user approval.**

---

## Stage 2 — Synchronize Documentation (`/project-documentation`)

Once the user approves Stage 1, load and follow the **`project-documentation`** skill (`SKILL.md`):

1. **Bootstrap if needed**: If `docs/` does not exist yet, run `scripts/init_docs.py` from `project-documentation` to scaffold the flat singletons (`ubiquitous-language.md`, `product.md`, `architecture.md`, `development.md`) and empty `flows/` and `decisions/` folders.
2. **Update Current-State Docs**:
   - Update `docs/ubiquitous-language.md` for any new, updated, or renamed canonical terms.
   - Update `docs/product.md`, `docs/architecture.md`, and allocate or update numbered flows under `docs/flows/<NNN>-<name>.md` (using `scripts/new_doc.py flows <name>`).
   - Prune documentation and references for any removed features or obsolete flows so `docs/` describes only the current system.
   - Allocate an ADR in `docs/decisions/<NNN>-<name>.md` (using `scripts/new_doc.py decisions <name>`) only if a hard-to-reverse trade-off decision was made.
3. **Run Deterministic Validators**:
   Run `docs_lint.py`, `glossary_lint.py`, and `adr_scan.py` from `project-documentation/scripts/`. Fix any reported errors before continuing.
4. **Stage 2 Gate Output**: Update the Web UI with the docs summary and ask:
   ```bash
   python3 <path-to-project-workflow>/scripts/workflow_ui.py --update --stage 2 --status waiting_approval --title "Documentation Validated" --content "<docs-summary>"
   ```
   > *"Stage 2 (Documentation) complete and validated. Click **Approve & Next Step** in the browser or reply **approve** in chat to proceed to Stage 3 (`/project-plan`)."*

**STOP and wait for user approval.**

---

## Stage 3 — Architecture & File Tree Plan (`/project-plan`)

Once the user approves Stage 2, load and follow the **`project-plan`** skill (`SKILL.md`) along with any detected stack architecture skill (`project-react-architecture` or `project-go-architecture`):

1. **Scan Existing Codebase Internally**: Inspect existing layers, shared primitives, modules, routes, and any code identifiers affected by a glossary term rename.
2. **Decide Layer & Action Tags**: Classify every touched file as `[NEW]`, `[UPDATE]`, `[REUSE]`, `[PROMOTE]`, or `[DELETE]` according to the active stack architecture rules.
3. **Stage 3 Gate Output**: Update the Web UI with the file tree and ask:
   ```bash
   python3 <path-to-project-workflow>/scripts/workflow_ui.py --update --stage 3 --status waiting_approval --title "Proposed File Tree" --content "<file-tree>"
   ```
   Output **ONLY** the `### Proposed File Tree` in chat, followed by the prompt:
   > *"Stage 3 (File Tree Plan) ready. Click **Approve & Next Step** in the browser or reply **approve** in chat to proceed to Stage 4 (`/project-implement`)."*

**STOP and wait for user approval. Do not create or edit source code files during Stage 3.**

---

## Stage 4 — Implement & Verify (`/project-implement`)

Once the user approves Stage 3, load and follow the **`project-implement`** skill (`SKILL.md`) and the active stack architecture skill (`project-react-architecture` or `project-go-architecture`):

1. **Execute Approved File Tree**: Create, update, promote, and delete the exact files approved in Stage 3.
2. **Enforce Stack & Glossary Invariants**:
   - Use canonical glossary terms from `docs/ubiquitous-language.md` for all code identifiers. If a glossary term was renamed, rename every matching code identifier in the same change.
   - Apply all code hygiene, layering, and formatting rules from the active stack architecture skill.
3. **Run Verification**:
   - Run the project's test, linter, typecheck, and build commands (e.g., `npm test`, `npm run build`, `make fmt`, `make swagger`, `make test`, `make build`).
   - Re-run `docs_lint.py`, `glossary_lint.py`, and `adr_scan.py` to confirm documentation and code remain in sync.
4. **Stage 4 Completion & Cleanup**: Update the Web UI to completed, stop the server, and present the final summary:
   ```bash
   python3 <path-to-project-workflow>/scripts/workflow_ui.py --update --stage 4 --status completed --title "Implementation Complete" --content "<results>"
   python3 <path-to-project-workflow>/scripts/workflow_ui.py --stop
   ```
