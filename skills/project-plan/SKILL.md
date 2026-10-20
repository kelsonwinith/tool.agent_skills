---
name: project-plan
description: "Stage 3 of the project workflow (/project-plan): pre-implementation codebase scan and annotated ### Proposed File Tree gate. Use after documentation sync (/project-documentation) or whenever planning file additions, updates, reuse, promotions, or deletions before writing code. Scans existing layers to prevent duplicate primitives/modules, schedules glossary-driven identifier renames across files, applies stack-specific architecture rules (project-react-architecture, project-go-architecture, or clean architecture), outputs ONLY ### Proposed File Tree ([NEW], [UPDATE], [REUSE], [PROMOTE], [DELETE]), and pauses for user approval before implementation."
license: MIT
metadata:
  version: 1.0.0
---

# Project Plan — Proposed File Tree Gate (Stage 3)

Before creating, modifying, promoting, or deleting any source code file, `project-plan` maps the agreed design and documentation onto the exact files in the repository and pauses for user confirmation.

---

## 1. Step 1 — Silently Scan the Existing Codebase & Glossary

Inspect the workspace before proposing any file paths:

1. **Detect Active Stack Architecture Skill**:
   - **React / Next.js (`package.json` with `react`/`next`)**: Load `project-react-architecture` and apply its layer rules (`/components`, `/layouts`, `/hooks`, `/types`, `/constants`, `/utils`, `features/[feature]/`, `app/**`).
   - **Go Hexagonal (`go.mod`)**: Load `project-go-architecture` and apply its 3-segment `<scope>_<layer>_<name>.go` rules across `internal/modules/<module>/{domain,application,adapter}`, `internal/infrastructure/`, `internal/shared/`, and `internal/bootstrap/`.
   - **Other Stacks**: Follow the repository's established module boundaries, separating shared primitives/utilities from single-domain modules.
2. **Eliminate Duplication**: Search existing shared primitives, layouts, helpers, ports, and domain models so nothing is duplicated when an existing file can be `[REUSE]`d, `[UPDATE]`d, or `[PROMOTE]`d.
3. **Include Glossary Identifier Renames**: Check `docs/context/001-ubiquitous-language.md`. If a canonical term was renamed or reconciled in Stages 1–2, find every code file carrying the old term (`client` → `buyer`, `ClientCard` → `BuyerCard`, etc.) and include those files in the tree as `[UPDATE]` or `[PROMOTE]`/`[DELETE]`.

---

## 2. Step 2 — Classify Every File with an Action Tag

Assign one of the five canonical tags to every touched or referenced file (full stack decision tables are in [references/decision-matrices.md](references/decision-matrices.md)):

- **`[NEW]`** — Brand-new file that does not exist yet and has no existing counterpart to extend.
- **`[UPDATE]`** — Existing file being modified (adding a variant/field/route, updating logic, or renaming identifiers to match the canonical glossary).
- **`[REUSE]`** — Existing primitive, layout, port, or shared utility used as-is without modification.
- **`[PROMOTE]`** — Moving a single-feature file up to project-wide shared scope because ≥2 features now use it (always paired with `[DELETE]` on its old feature-local path).
- **`[DELETE]`** — Removing an obsolete, duplicate, or promoted file, or pruning code for a removed feature.

---

## 3. Step 3 — Output ONLY `### Proposed File Tree` (Pause for Approval)

Do **not** write extra prose essays or questionnaires during Stage 3, and do **not** create or edit code files yet. Output **only** the `### Proposed File Tree` section with a concise `# [TAG] — what it does` comment per file, followed by the approval gate prompt:

```markdown
### Proposed File Tree

```text
[project]/
├── app/orders/
│   └── page.tsx                                           # [NEW] SSR Server Component page shell (zero className)
├── components/
│   └── badge/statusBadge.ui.tsx                           # [REUSE] Canonical status badge primitive
├── layouts/
│   └── page/pageLayout.layout.tsx                         # [REUSE] Page structural wrapper
└── features/
    └── orderCancellation/
        ├── orderCancellation.feature.ts                   # [NEW] Public feature entrypoint exporting CancelOrderDialog
        └── components/
            └── cancelOrderDialog/
                ├── cancelOrderDialog.component.tsx        # [NEW] Pure JSX view (zero className)
                ├── cancelOrderDialog.hook.ts              # [NEW] Cancellation state & confirmation handler
                └── cancelOrderDialog.type.ts              # [NEW] Props & dialog state types
```
```

End with the gate prompt:
- When running inside `/project-workflow`:
  > *"Stage 3 (File Tree Plan) ready. Reply **approve** to proceed to Stage 4 (`/project-implement`), or tell me what to adjust."*
- When invoked standalone as `/project-plan`:
  > *"Reply **approve** to implement this file tree, or tell me what to adjust."*

**STOP and wait for user approval.**
