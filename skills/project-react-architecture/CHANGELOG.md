# Changelog

## 1.7.0
- Added §1E "Next.js Page & Router Components (`app/**/page.tsx`, `app/**/layout.tsx`, `pages/**`)" and Rule 4L.
- Enforced that Next.js page and router components are always Server-Side Rendered (Server Components — never `'use client'`) and act like feature component views with zero custom `className` or inline `style` attributes.
- Enforced strict import boundaries for page/router files: may only import `.ui.tsx` primitives (`/components/[module]/[name].ui.tsx`), `.layout.tsx` containers (`/layouts/[category]/[name].layout.tsx`), and public feature components exported from `features/[feature]/[feature].feature.ts` (never deep-importing internal `features/[feature]/components/**` files).
- Updated §1D (`'use client'` placement) and §2 (The No-Inline-`className` Rule) with BAD vs. GOOD Next.js SSR `page.tsx` examples and updated the Decision Checklist (§0).

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
