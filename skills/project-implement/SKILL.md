---
name: project-implement
description: "Stage 4 of the project workflow (/project-implement): execute the user-approved ### Proposed File Tree following the active stack architecture skill (project-react-architecture, project-go-architecture, or clean architecture) and canonical glossary terms, then run deterministic verification (tests, typecheck, build, and documentation linters). Use after /project-plan is approved or when the user invokes /project-implement."
license: MIT
metadata:
  version: 1.0.0
---

# Project Implement (Stage 4)

`project-implement` turns the approved `### Proposed File Tree` from Stage 3 (`/project-plan`) and the updated documentation from Stage 2 (`/project-documentation`) into working, verified production code.

> **Prerequisite Check**: If no `### Proposed File Tree` has been confirmed yet (and the user did not explicitly ask to skip planning), run **`project-plan`** first and wait for user approval before editing code files.

---

## 1. Execute the Approved File Tree Precisely

Follow the exact `[NEW]`, `[UPDATE]`, `[REUSE]`, `[PROMOTE]`, and `[DELETE]` entries from the approved `### Proposed File Tree`:

- **Promotions (`[PROMOTE]` + `[DELETE]`)**: Move shared code cleanly to its new root/shared location, update every import path, and delete the old feature-local copy so zero duplicates remain.
- **Deletions (`[DELETE]`)**: Delete obsolete or removed files completely and prune dead imports, exports, routes, and tests.
- **Scope discipline**: Do not silently invent extra unapproved files outside the confirmed tree. If implementation reveals an unavoidable file change, call it out clearly.

---

## 2. Enforce Canonical Glossary Names in Code

Every domain concept in code must use the exact canonical term from `docs/context/001-ubiquitous-language.md` (adjusted only for language casing conventions):

- `Buyer` in glossary → `buyer`, `Buyer`, `buyerId`, `BuyerCard`, `useBuyer`, `fetchBuyers` in code.
- Never introduce a synonym listed in the glossary's `Avoid` column into variable names, type names, DTO fields, route paths, or DB column names.
- If Stage 1–2 renamed a glossary term, complete the synchronized rename across every affected code identifier in this same implementation pass.

---

## 3. Apply the Active Stack Architecture Rules

Load and enforce the stack skill matching the repository:

1. **React / Next.js (`project-react-architecture`)**:
   - **Zero inline `className` or `style`** in `.component.tsx` feature views and Next.js `app/**/{page,layout}.tsx` route files; raw CSS/Tailwind lives only in `/components/[module]/[name].ui.tsx` and `/layouts/[category]/[name].layout.tsx`.
   - **Next.js routes are always SSR Server Components** (never `'use client'`) and import only `.ui.tsx`, `.layout.tsx`, and `[feature].feature.ts`.
   - **Strict TypeScript & Hygiene**: Use `T | null` (never declare `undefined`), no `any` / `as` / `!`, return `RequestState<T>` from services/stores, and place a max 5-line `what` / `param` / `return` doc block above every non-trivial exported function (with zero inline `//` comments inside function bodies).
2. **Go Hexagonal (`project-go-architecture`)**:
   - **Strict inward dependency flow**: `adapter/{in,out}` → `application` → `domain` (zero framework/GORM/Fiber imports in `domain`).
   - **3-segment file naming** (`<scope>_<layer>_<name>.go`), **6-section file banners** (`Constants`, `Variables`, `Types`, `Constructors`, `Methods`, `Functions`), and **explicit import aliases** in 3 grouped blocks.
   - **Module prefixing** on exported and unexported identifiers, and complete Swagger annotations on Fiber handlers.

---

## 4. Run End-to-End Verification

Before finishing Stage 4, run all applicable checks from the project root and fix any failures:

1. **Code Verification**:
   - **React / Next.js / Node**: Run configured typecheck, linter, unit test, and build scripts (`npm run typecheck`, `npm run lint`, `npm test`, `npm run build`).
   - **Go Hexagonal**: Run `make fmt`, `make swagger` (if DTOs/handlers changed), `make test`, and `make build`.
   - **Other stacks**: Run the repository's standard test and build suite.
2. **Documentation & Glossary Verification**:
   - If `docs/` exists, run `docs_lint.py`, `glossary_lint.py`, and `adr_scan.py` from `project-documentation/scripts/` to guarantee docs and code stayed 100% synchronized.

---

## 5. Stage 4 Output (Final Sign-Off)

Present a concise implementation and verification summary:
- Files created, updated, promoted, and deleted.
- Verification commands run and their pass status.
- Pause for the user's final sign-off (or any follow-up adjustments).
