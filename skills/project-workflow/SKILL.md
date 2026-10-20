---
name: project-workflow
description: "End-to-end gated project workflow orchestrator (/project-workflow). Auto-installs missing companion workflow and stack skills on first run, then guides any feature addition, modification, removal, or refactor through 4 strict approval-gated stages: Stage 1 (/project-grill: design-tree interview & glossary/requirement conflict check), Stage 2 (/project-documentation: canonical glossary, numbered docs/ tree, ADR sync & linter validation), Stage 3 (/project-plan: codebase scan & annotated ### Proposed File Tree), and Stage 4 (/project-implement: stack-compliant implementation & verification). Use whenever the user invokes /project-workflow or asks to run the full project workflow loop."
license: MIT
compatibility: "Requires Python 3 (standard library only) and Node/npx (for auto-installing missing companion skills via the skills CLI)."
metadata:
  version: 1.0.0
---

# Project Workflow

`project-workflow` is the master entrypoint for building, modifying, refactoring, or removing features in any repository. Installing this single skill automatically bootstraps the rest of the workflow suite and runs every request through a predictable, four-stage loop with an explicit user approval gate at the end of every stage.

```text
/project-workflow "<request>"
   │
   ├─► Stage 0: Bootstrap        (auto-detect stack & install missing companion skills)
   ├─► Stage 1: /project-grill   (design-tree interview + glossary/requirement check) ──► [PAUSE FOR APPROVAL]
   ├─► Stage 2: /project-documentation (sync docs/, glossary, ADRs + run doc linters) ──► [PAUSE FOR APPROVAL]
   ├─► Stage 3: /project-plan    (scan layers + output ONLY ### Proposed File Tree)   ──► [PAUSE FOR APPROVAL]
   └─► Stage 4: /project-implement (write code per stack architecture + run checks)   ──► [FINAL SIGN-OFF]
```

---

## Core Rule: Pause After Every Stage

Never chain two stages in a single turn without the user's explicit confirmation. At the end of Stage 1, Stage 2, and Stage 3, present that stage's artifact and **wait for the user to approve** before advancing to the next stage.

If the user replies with adjustments instead of approval, stay in the current stage, revise its output, and ask for confirmation again.

---

## Stage 0 — Auto-Bootstrap Companion Skills

Before starting Stage 1, ensure the required companion skills are installed in the workspace by running the bundled bootstrap helper from the project root:

```bash
python3 <path-to-project-workflow>/scripts/bootstrap_workflow.py
```

What `bootstrap_workflow.py` does automatically:
1. Checks whether core workflow skills (`project-grill`, `project-documentation`, `project-plan`, `project-implement`) are already installed.
2. Inspects the project root to detect the tech stack:
   - `package.json` containing `"react"` or `"next"` → requires `project-react-architecture`
   - `go.mod` → requires `project-go-architecture`
3. If any required skill is missing, runs:
   ```bash
   npx skills add kelsonwinith/tool.agent_skills --skill <missing-skills...> -y
   ```
4. Outputs a JSON summary of installed and newly added skills so you know which stack architecture skill is active for Stages 3 and 4.

---

## Stage 1 — Grill the Request (`/project-grill`)

Load and follow the **`project-grill`** skill (`SKILL.md`) with the user's request:

1. **Silent Discovery**: Read relevant code and `docs/` (`docs/context/001-ubiquitous-language.md`, `docs/product/`, `docs/architecture/`, `docs/decisions/`) yourself. Never ask the user for facts already present in the repository.
2. **Terminology & Requirement Check**:
   - Reconcile every domain word in the request against `docs/context/001-ubiquitous-language.md`. Emit a **Terminology Mismatch** block if a term conflicts or changes meaning (noting all code identifiers that must rename with it).
   - Check the request against documented requirements in `docs/product/`. Emit a **Requirement Mismatch** block if it contradicts an existing rule.
3. **Design-Tree Interview**: Ask only the frontier questions whose prerequisites are settled, numbered, each with a `(Recommended)` default proposal. Wait for answers and repeat until zero assumptions remain.
4. **Stage 1 Gate Output**: Once aligned, output the **Agreed Design Summary** (Scope, Terminology Updates & Code Renames, Requirement Changes, Architectural Decisions / ADR check) and ask:
   > *"Stage 1 (Grill) complete. Reply **approve** to proceed to Stage 2 (`/project-documentation`), or tell me what to adjust."*

**STOP and wait for user approval.**

---

## Stage 2 — Synchronize Documentation (`/project-documentation`)

Once the user approves Stage 1, load and follow the **`project-documentation`** skill (`SKILL.md`):

1. **Bootstrap if needed**: If `docs/` does not exist yet, run `scripts/init_docs.py` from `project-documentation` to scaffold the numbered `docs/` tree and glossary.
2. **Update Current-State Docs**:
   - Update `docs/context/001-ubiquitous-language.md` for any new, updated, or renamed canonical terms.
   - Create or update affected files under `docs/product/`, `docs/architecture/`, and `docs/development/` (using `scripts/new_doc.py` when allocating a new numbered file).
   - Prune documentation and references for any removed features, endpoints, or rules so `docs/` describes only the current system.
   - Append an ADR to `docs/decisions/001-decisions.md` only if a hard-to-reverse trade-off decision was made.
3. **Run Deterministic Validators**:
   Run `docs_lint.py`, `glossary_lint.py`, and `adr_scan.py` from `project-documentation/scripts/`. Fix any reported errors before continuing.
4. **Stage 2 Gate Output**: List the created/updated/deleted `docs/` files and validator results, then ask:
   > *"Stage 2 (Documentation) complete and validated. Reply **approve** to proceed to Stage 3 (`/project-plan`), or tell me what to adjust."*

**STOP and wait for user approval.**

---

## Stage 3 — Architecture & File Tree Plan (`/project-plan`)

Once the user approves Stage 2, load and follow the **`project-plan`** skill (`SKILL.md`) along with any detected stack architecture skill (`project-react-architecture` or `project-go-architecture`):

1. **Scan Existing Codebase Internally**: Inspect existing layers, shared primitives, modules, routes, and any code identifiers affected by a glossary term rename.
2. **Decide Layer & Action Tags**: Classify every touched file as `[NEW]`, `[UPDATE]`, `[REUSE]`, `[PROMOTE]`, or `[DELETE]` according to the active stack architecture rules.
3. **Stage 3 Gate Output**: Output **ONLY** the `### Proposed File Tree` code block with inline `# [TAG] — what it does` comments, followed by the gate prompt:
   > *"Stage 3 (File Tree Plan) ready. Reply **approve** to proceed to Stage 4 (`/project-implement`), or tell me what to adjust."*

**STOP and wait for user approval. Do not create or edit source code files during Stage 3.**

---

## Stage 4 — Implement & Verify (`/project-implement`)

Once the user approves Stage 3, load and follow the **`project-implement`** skill (`SKILL.md`) and the active stack architecture skill (`project-react-architecture` or `project-go-architecture`):

1. **Execute Approved File Tree**: Create, update, promote, and delete the exact files approved in Stage 3.
2. **Enforce Stack & Glossary Invariants**:
   - Use canonical glossary terms from `docs/context/001-ubiquitous-language.md` for all code identifiers (variables, types, functions, DTOs, routes, DB columns). If a glossary term was renamed, rename every matching code identifier in the same change.
   - Apply all code hygiene, layering, and formatting rules from `project-react-architecture` (SSR pages, zero inline `className` in views/pages, `RequestState<T>`, 5-line function doc blocks) or `project-go-architecture` (6-section banners, explicit import aliases, 3-segment filenames, inward dependency flow).
3. **Run Verification**:
   - Run the project's test, linter, typecheck, and build commands (e.g., `npm test`, `npm run build`, `make fmt`, `make swagger`, `make test`, `make build`).
   - Re-run `docs_lint.py`, `glossary_lint.py`, and `adr_scan.py` to confirm documentation and code remain in sync.
4. **Stage 4 Final Output**: Report the completed changes and verification results, and pause for the user's final sign-off.
