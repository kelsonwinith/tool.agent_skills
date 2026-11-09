---
name: project-documentation
description: "Requirement-polishing and documentation guardian. ALWAYS use this skill whenever the user asks to implement, add, fix, change, refactor, or remove any feature, logic, flow, data model, or requirement — even if the user never mentions 'docs' or 'documentation'. Polishes raw user prompts against the existing codebase into clear specs with Mermaid flowcharts, verifies cross-feature conflicts, aligns domain terms, and confirms understanding via docs/requests/ before any code is written."
license: MIT
compatibility: "Requires Python 3 (standard library only) to run bundled helpers in scripts/."
metadata:
  version: 2.0.0
---

# Requirements First, Code Later

Polishes user requests against the codebase into clear specifications so user and AI share the exact same understanding before writing code. Docs describe what the system is right now.

## 1. Directory Structure

- `docs/context.md`: Canonical ubiquitous language & global invariants.
- `docs/architecture.md`: High-level tech stack, component diagram & data models.
- `docs/features/<NNN>-<kebab>.md`: Scalable feature specs (flowcharts, rules, conflict checks).
- `docs/decisions/<NNN>-<kebab>.md`: ADRs for irreversible decisions.
- `docs/requests/<NNN>-<kebab>.md`: Human request history (AI writes here, never reads).

Scaffold files via scripts only (templates are pre-bundled):
- Bootstrap tree: `python scripts/init_docs.py`
- New feature: `python scripts/new_doc.py features <name>`

## 2. Workflow

1. **Scan**: If `docs/` is missing, run `init_docs.py` (recommend documenting baseline if code already exists).
2. **Grill (if new/unclear)**: If the feature is undocumented or ambiguous, ask numbered questions with recommended defaults before proceeding.
3. **Spec & Diagram**: Create/update `docs/features/<NNN>-<name>.md` with a Mermaid flowchart, rules, and cross-feature conflict check.
4. **Sync Language**: Map terms in `docs/context.md`. The canonical term must match code identifiers (`Buyer` -> `buyerId`).
5. **Confirm via `docs/requests/<NNN>-<title>.md`**: Write the alignment summary to a new file in `docs/requests/` (never deleted, AI never reads) containing:
   - **Overview**: 1-2 sentence plain summary.
   - **Comparison Table**: `Area / Context` | `Before (Current)` | `After (Proposed)` | `Document Reference`.
   - **Flow Comparison**: Dual Mermaid blocks (`### Current Flow` vs `### Proposed Flow`). Highlight changes with `classDef added fill:#064e3b,stroke:#34d399,stroke-width:3px,color:#ffffff;` and `classDef changed fill:#78350f,stroke:#fbbf24,stroke-width:3px,color:#ffffff;` (no emoji in node text).
   - **Conflict Check**: Audit against existing feature docs.
   - **Confirmation Prompt**: Ask user to verify before code implementation.

Link the created request file in chat: *"I have prepared the alignment summary in `docs/requests/<NNN>-<title>.md`. Please review before we proceed."* **Wait for user confirmation before writing any code.**

## 3. Removals

When a feature is removed, delete its `docs/features/` file and prune all references from `docs/`.

## 4. Validators

- `python scripts/docs_lint.py`: Checks tree structure, required headers, and Mermaid diagrams.
- `python scripts/glossary_lint.py [--scan]`: Checks ubiquitous language table and code identifiers.
- `python scripts/adr_scan.py`: Validates ADR integrity.
