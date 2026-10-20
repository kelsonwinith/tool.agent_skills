# Changelog

## 1.8.0
- Aligned §0 Pre-Implementation File Tree Gate with `project-workflow`, `project-plan` (Stage 3), and `project-implement` (Stage 4) so Stage 1 (`/project-grill`) and Stage 2 (`/project-documentation`) can complete before the file tree gate runs, and Stage 4 can proceed immediately once Stage 3 is approved.
- Added `agents/openai.yaml` metadata.

## 1.7.0
- Modularized detailed topic guides and reference code into `references/` for progressive disclosure, reducing `SKILL.md` to a concise ~135-line architectural entrypoint:
  - `references/pre-implementation-plan.md` — 3-step Scan → Decide → Output `### Proposed File Tree` gate, decision matrix, and file tree template.
  - `references/layers-and-nextjs-routes.md` — Full code blueprints for `.ui.tsx`, `.layout.tsx`, `.component.tsx`, `.hook.ts`, `[feature].feature.ts`, and Next.js SSR routes (`page.tsx`/`layout.tsx`) with BAD vs. GOOD examples.
  - `references/ui-reuse-and-promotion.md` — Root vs. single-feature placement, Zero UI Duplication protocol, canonical `HttpBadge` case study, and the 3-level Promotion Scale.
  - `references/module-slicing.md` — Growing module slicing rules, semantic suffixes, directory trees, and entrypoint + submodule code examples.
  - `references/type-safety-and-comments.md` — Code hygiene & type-safety rules (4A–4M) and the 5-line `what`/`param`/`return` Lean Doc Block standard with BAD vs. GOOD examples.
- Added §0 "Pre-Implementation File Tree Gate (MANDATORY FIRST STEP)" and Rule 4M: before creating or modifying files, agents scan the codebase internally and output **ONLY** `### Proposed File Tree` (`[NEW]`, `[UPDATE]`, `[REUSE]`, `[PROMOTE]`, `[DELETE]` with a short inline comment on what each file does).
- Added §1E "Next.js Page & Router Components (`app/**/page.tsx`, `app/**/layout.tsx`, `pages/**`)" and Rule 4L: enforced that Next.js pages/layouts are always Server-Side Rendered (Server Components — never `'use client'`), have zero custom `className`, and only import `.ui.tsx`, `.layout.tsx`, and `[feature].feature.ts`.

## 1.6.0
- Added §0B "Scan before creating: single source of truth for UI primitives (Zero duplication)" with a strict Scan → Evaluate → Ask → Reuse protocol.
- Enforced scanning existing `/components/**` and `/layouts/**` before creating any UI component to eliminate duplicate components (e.g. separate badges across dropdowns and cards).
- Added requirement to ask the user first when an existing UI primitive partially matches (e.g. missing HTTP methods or size variants) before updating or creating, ensuring users confirm whether to extend the shared primitive or create a new one.
- Added canonical HTTP Method Badge case study showing a single `/components/badge/httpBadge.ui.tsx` primitive and `/constants/httpBadge.constant.ts` reused across display components and dropdown option selectors.
- Added Rule 4K (Zero UI Duplication) and updated Decision Checklist (§0).

## 1.5.0
- Growing-module slicing now explicitly applies to root `/utils` and `/hooks` (and every layer), not just feature folders. The public entrypoint keeps its flat-file path/depth (`utils/[utilName]/[utilName].util.ts`, `hooks/[hookName]/[hookName].hook.ts`) and re-exports the stable API; children are named `[main function name].[subfolder].ts`. Added root-scoped slicing examples and clarified entrypoint/child roles.

## 1.4.0
- Clarified file placement: code shared across features or used app-wide lives at the PROJECT ROOT (`/components`, `/layouts`, `/hooks`, `/types`, `/constants`, `/utils`), never inside a feature. Added root `hooks/` and `utils/` layers.
- Added §0A "Shared code lives at the project root" with a kind→location table, one-way import direction (`features/` → root), and the rule that UI primitives never live under a feature.
- Updated the decision checklist and promotion scale (Level 3 now lists all six root layers; promotion moves rather than copies).

## 1.3.0
- Function comments: added explicit rule that doc blocks live only above the function declaration, with no `//` comments on individual code lines (extract to a named helper instead).
- Expanded the §5 BAD example to show and call out inline code-line comment noise.

## 1.2.0
- Rewrote SKILL.md as a lean guideline: principles and rationale instead of a numbered, cross-referenced rulebook.

## 1.1.0
- Added `scripts/new_feature.py` to scaffold a feature module (folder, entrypoint, `.component`/`.hook`/`.type` stubs) with a regression test suite.
- Added accessibility and user-facing-text guidance.
- Removed third-party library assumptions from examples (self-contained UI primitive).
- Moved growing-module examples into `references/module-slicing.md`.

## 1.0.0
- Initial layered React/Next.js component and file architecture with zero inline styling.
