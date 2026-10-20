---
name: project-grill
description: "Stage 1 of the project workflow (/project-grill): pre-implementation design-tree interview, canonical glossary terminology check, and documented requirement mismatch detector. Use before writing docs or code whenever a user asks to add, modify, remove, or refactor a feature, or invokes /project-grill directly. Silently inspects existing code and docs/ first, flags any terminology or requirement conflicts, asks numbered frontier questions with (Recommended) answers until zero assumptions remain, and emits an Agreed Design Summary for user approval."
license: MIT
metadata:
  version: 1.0.0
---

# Project Grill (Stage 1)

A request is rarely complete on the first message, and its unstated edge cases are exactly where implementations drift from what the user actually wanted. `project-grill` settles every ambiguity, terminology clash, and requirement conflict **before** a single line of documentation or code is touched.

---

## 1. Silent Discovery First (Never Ask What the Repo Already Knows)

Before asking the user anything, silently inspect the repository yourself:
- **Canonical Context**: Read `docs/context/001-ubiquitous-language.md` (and `001-context-map.md` if present) to learn the project's established vocabulary.
- **Documented Requirements & Architecture**: Read `docs/README.md`, `docs/product/`, `docs/architecture/`, and `docs/decisions/` if `docs/` exists.
- **Codebase Reality**: Locate the existing modules, components, routes, models, and configs touched by the request.

Facts that can be verified from files, types, routes, or configs never go to the user—only genuine product, domain, or trade-off decisions do.

---

## 2. Reconcile Terminology & Requirements

Compare the user's request against what is already documented and implemented:

1. **Terminology Check (`docs/context/001-ubiquitous-language.md`)**:
   - **New domain term**: Propose a crisp 1–2 sentence definition (*what it is*, not *what it does*) and its `Avoid` synonyms as part of your grilling round.
   - **Conflicting or renamed term**: Remember that a glossary term is also the canonical identifier name in code (`Buyer` → `buyer`, `BuyerId`, `useBuyer`). If the user uses an `Avoid` synonym or shifts a term's meaning, emit the **Terminology Mismatch** block from [references/mismatch-and-summary-formats.md](references/mismatch-and-summary-formats.md), listing the affected code identifiers, and ask how they want to resolve it.
2. **Requirement Check (`docs/product/*`)**:
   - If the request contradicts or alters an existing documented business rule or product requirement, emit the **Requirement Mismatch** block from [references/mismatch-and-summary-formats.md](references/mismatch-and-summary-formats.md) and ask for explicit confirmation.

---

## 3. Conduct the Design-Tree Interview

Treat the request as a dependency tree of decisions:

- **Ask only the current frontier**: Group the questions whose prerequisites are already settled into a single round, then wait for the user's answers. If an answer unlocks a deeper branch, ask that follow-up in the next round.
- **Number every question and lead with `(Recommended)`**: A concrete recommendation with a 1-sentence rationale is much faster for the user to confirm or override than an open-ended question.
- **Cover the real failure modes**:
  - Data & state lifecycle (creation defaults, validation boundaries, permissions/ownership, empty/error states, deletion/archival behavior).
  - Cross-feature impact (what existing routes, APIs, DB tables, or UI primitives are affected or pruned).
  - Whether any choice qualifies for an ADR (hard to reverse, surprising without context, real trade-off).
- **Stop as soon as nothing is left assumed**: If the user's initial prompt is already completely unambiguous and has zero conflicts with `docs/`, skip straight to the Agreed Design Summary.

---

## 4. Gate Output: Agreed Design Summary (Pause for Approval)

Once all questions, terminology, and requirement conflicts are settled, output the **Agreed Design Summary** using the template in [references/mismatch-and-summary-formats.md](references/mismatch-and-summary-formats.md) and **pause for explicit user approval**:

- When running inside `/project-workflow`, end with:
  > *"Stage 1 (Grill) complete. Reply **approve** to proceed to Stage 2 (`/project-documentation`), or tell me what to adjust."*
- When invoked standalone as `/project-grill`, ask the user to confirm the summary before taking any next action.
