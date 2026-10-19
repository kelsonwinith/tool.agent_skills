---
name: project-react-architecture
description: "Use whenever building or editing ANY React/Next.js UI or route — pages, layouts, routers, cards, forms, dropdowns, dashboards, modals, buttons, tables, badges — even if the user doesn't say 'component,' 'layout,' or name a file type. Also use when refactoring existing components/pages, splitting a growing module into semantic submodules, or deciding where a shared type/constant/hook/util/UI primitive should live. Enforces: BEFORE writing or editing any code, scan existing project files, make explicit layer/scope placement decisions, output an annotated File Tree Plan (`[NEW]`, `[UPDATE]`, `[REUSE]`, `[PROMOTE]`), and confirm with the user first that the implementation plan is valid; scan `/components/**` and `/layouts/**` to eliminate duplicate UI components; code shared across features or used app-wide lives at the PROJECT ROOT (`/components/[module]/[name].ui.tsx`, `/layouts/[category]/[name].layout.tsx`, `/hooks/[name].hook.ts`, `/types/[name].type.ts`, `/constants/[name].constant.ts`, `/utils/[name].util.ts`), never inside a feature; only single-feature code lives under `features/[feature]/`; both feature components (`features/[feature]/components/[name]/`) and Next.js page/router components (`app/**/page.tsx`, `app/**/layout.tsx`, `pages/**`) use zero inline className styling; Next.js pages are always Server-Side Rendered (Server Components — never `'use client'`); page/router files only import `.ui.tsx` primitives, `.layout.tsx` containers, and public components from `[feature].feature.ts` (never deep-importing internal feature files); and every exported non-trivial function carries a fixed comment block."
---

# React Clean Component Architecture

Every UI and code element belongs to exactly one layer. The project root holds everything **shared across features or used app-wide**; `features/` holds only what belongs to a single domain; and Next.js route/page files act purely as Server-Side Rendered (SSR), zero-`className` composition shells:

```text
[project]/
├── app/**/{page,layout,loading}.tsx       # Next.js SSR Routes (Server Components, ZERO inline className; imports only .ui, .layout, & [feature].feature)
├── components/[module]/[name].ui.tsx      # Global UI System Primitives (ONLY place raw CSS lives)
├── layouts/[category]/[name].layout.tsx   # Pure Structural Containers (categorized)
├── hooks/[name].hook.ts                   # App-wide hooks used by ≥2 features
├── types/[name].type.ts                   # App-wide Shared Types & Interfaces
├── constants/[name].constant.ts           # App-wide Shared Constants & Config
├── utils/[name].util.ts                   # App-wide shared helpers used by ≥2 features
└── features/[feature]/                    # Domain Feature Modules (single-feature only)
    ├── components/[name]/                 # 1 folder per component (ZERO inline className)
    ├── hooks/                             # Feature-scoped hooks & store slices
    ├── types/                             # Feature-scoped domain types
    ├── constants/                         # Feature-scoped constants
    ├── utils/                             # Feature-scoped helpers
    └── [feature].feature.ts               # Public feature entrypoint (only path pages/features may import)
```

## Topic Reference Guides (Read as Needed)

Each topic has a dedicated reference file with complete code templates and `❌ BAD` vs. `✅ GOOD` examples. Load the relevant file before implementing that part of the task:

| Topic & Reference File | When to Read |
| :--- | :--- |
| **[references/pre-implementation-plan.md](references/pre-implementation-plan.md)** | **Read FIRST before any implementation or refactor.** Full 3-step Scan → Decide → Plan Tree & Confirm protocol, decision matrix, and user confirmation templates. |
| **[references/layers-and-nextjs-routes.md](references/layers-and-nextjs-routes.md)** | **Read when building/editing `.ui.tsx`, `.layout.tsx`, feature components, or Next.js routes.** Full code blueprints, `'use client'`/`'use server'` placement, SSR `page.tsx` rules, and zero-`className` BAD vs. GOOD examples. |
| **[references/ui-reuse-and-promotion.md](references/ui-reuse-and-promotion.md)** | **Read when adding visual elements (badges, buttons, tags, inputs) or sharing code across features.** Zero UI duplication protocol, canonical `HttpBadge` case study, root vs. feature placement table, and the 3-level Promotion Scale. |
| **[references/module-slicing.md](references/module-slicing.md)** | **Read when splitting a growing component, hook, utility, or service.** Semantic subfolder rules (`.rule.ts`, `.geometry.ts`, `.factory.ts`, `.mapper.ts`, `.parser.ts`, `.format.ts`, `.export.ts`, `.slice.ts`, `.selector.ts`, `.provider.ts`) and code examples. |
| **[references/type-safety-and-comments.md](references/type-safety-and-comments.md)** | **Read before writing TypeScript logic, hooks, services, or doc comments.** Rules 4A–4M (`RequestState<T>`, `null` over `undefined`, no `any`/`as`/`!`, hook defaults, action handlers) and the 5-line `what`/`param`/`return` doc block standard. |

---

## 0. Pre-Implementation File Tree & Confirmation Gate (MANDATORY FIRST STEP)

Whenever the user asks to add, build, update, or refactor any feature, component, or page (e.g. *"add X..."*, *"build a Y page..."*), **DO NOT jump straight to writing or modifying files**, and **DO NOT write a multi-section prose essay**. Follow this 3-step workflow first (details in [references/pre-implementation-plan.md](references/pre-implementation-plan.md)):

1. **Step 1 — Scan Existing Codebase Internally**: Inspect `/components/**`, `/layouts/**`, `/constants/**`, `/types/**`, `/hooks/**`, `/utils/**`, `features/**`, and `app/**` to see what already exists.
2. **Step 2 — Decide Layer & Scope Internally**:
   - **UI Primitive / Layout Match?** → Exact match: **`[REUSE]`**. Partial match (e.g. missing variant/size/method): **`[UPDATE]`** (ask the user in `### Confirmation`). None exists: **`[NEW]`** at `/components/[module]/[name].ui.tsx` or `/layouts/[category]/[name].layout.tsx`.
   - **Root vs. Feature Scope?** → Used by **≥2 features or app-wide**: project root (`/types`, `/constants`, `/hooks`, `/utils`), or **`[PROMOTE]`** if moving up from 1 feature. Used by **1 feature only**: `features/[feature]/`.
   - **Feature Component?** → `features/[feature]/components/[name]/` with `.component.tsx` (zero `className`), `.hook.ts`, `.type.ts`, exported via `[feature].feature.ts`.
   - **Next.js Page / Route (`app/**/page.tsx`, `app/**/layout.tsx`, `pages/**`)?** → **Server-Side Rendered (SSR / Server Component — never `'use client'`)**, zero custom `className`, importing **only** `.ui.tsx`, `.layout.tsx`, and `[feature].feature.ts`.
3. **Step 3 — Output ONLY `### Proposed File Tree` and `### Confirmation`**:
   Before touching code files (unless the user explicitly says *"skip confirmation"*), output **only** these two sections:
   - **`### Proposed File Tree`**: An ASCII tree of affected/reused files with a short `# [NEW] | [UPDATE] | [REUSE] | [PROMOTE]` inline comment stating what each file does.
   - **`### Confirmation`**: Numbered questions (`1.`, `2.`, `3.`...) for any decisions/clarifications needed and for confirming the implementation. Format every question with lettered options (`a.`, `b.`, `c.`...), mark the recommended choice with `(Recommended)`, and **always make the final option `[last letter]. Type your own answer`**.

```markdown
### Proposed File Tree

```text
[project]/
├── app/api-playground/page.tsx                            # [NEW] SSR Server Component page shell (zero className)
├── components/badge/httpBadge.ui.tsx                      # [UPDATE] Add compact size="sm" variant
├── constants/httpBadge.constant.ts                        # [UPDATE] Add PUT/PATCH/DELETE styles & HTTP_BADGE_SIZE_MAP
├── layouts/page/pageLayout.layout.tsx                     # [REUSE] Page structural wrapper
└── features/apiTester/
    ├── apiTester.feature.ts                               # [NEW] Public feature entrypoint exporting MethodDropdown
    └── components/methodDropdown/
        ├── methodDropdown.component.tsx                   # [NEW] Pure JSX view (zero className)
        ├── methodDropdown.hook.ts                         # [NEW] Dropdown selection state & handlers
        └── methodDropdown.type.ts                         # [NEW] Props & dropdown types
```

### Confirmation

1. `httpBadge.ui.tsx` currently only supports `GET` and `POST`. How should we handle `PUT`, `PATCH`, `DELETE`, and the compact dropdown size?
   a. Update existing `/components/badge/httpBadge.ui.tsx` and `/constants/httpBadge.constant.ts` with `PUT`/`PATCH`/`DELETE` and `size="sm"` (Recommended)
   b. Create a separate badge primitive for the dropdown
   c. Type your own answer

2. Proceed with implementing this file tree?
   a. Yes, proceed with implementation (Recommended)
   b. Type your own answer
```

---

## 1. Core Architecture Layers & Next.js SSR Routes

Full code examples for every layer live in [references/layers-and-nextjs-routes.md](references/layers-and-nextjs-routes.md).

- **A. UI System Components (`/components/[module]/[name].ui.tsx`)**: Presentational building blocks (`button/`, `text/`, `badge/`, `input/`). 1 file per component (`default` export). Only place (alongside `.layout.tsx`) where raw Tailwind/CSS classes live. Context-neutral and server-renderable by default.
- **B. Layout Containers (`/layouts/[category]/[name].layout.tsx`)**: Pure structural containers grouped by category (`page/`, `card/`, `flex/`, `grid/`, `dialog/`, `panel/`). Accepts `children`/slots; variant class maps live in `/constants/layout.constant.ts`.
- **C. App-Wide Shared Code (Root `/hooks`, `/types`, `/constants`, `/utils`)**: Anything used by **≥2 features** lives at the project root. Direct file imports only (no `index.ts` barrels). One-way import direction: `features/` → root, never root → `features/`.
- **D. Feature Components (`features/[feature]/components/[name]/`)**: 1 folder per component containing `[name].component.tsx` (`default` export, zero `className`), `[name].hook.ts` (named export), `[name].type.ts` (named export), and optional `.constant.ts`, `.util.ts`, `.service.ts`. Public feature APIs are exported via `[feature].feature.ts` (never `index.ts`).
- **E. Next.js Page & Router Components (`app/**/page.tsx`, `app/**/layout.tsx`, `pages/**`)**:
  - **Always Server-Side Rendered (Server Components — NEVER `'use client'`)**: Client state/interactivity stays inside leaf `.component.tsx` feature components.
  - **Zero custom `className` or inline `style`**: No `<main className="...">` or raw styled HTML in route files.
  - **Strict Import Allowlist**: Route files may **only** import `@/components/[module]/[name].ui`, `@/layouts/[category]/[name].layout`, and `@/features/[feature]/[feature].feature` — **never** deep-import `features/[feature]/components/**`.
- **F. Growing Module Slicing**: When a module outgrows one file, slice it into a named folder with one public entrypoint at the same path depth (`[name]/[name].util.ts`, `[name]/[name].hook.ts`) and semantic child files (`.rule.ts`, `.geometry.ts`, `.factory.ts`, `.mapper.ts`, `.parser.ts`, `.format.ts`, `.export.ts`, `.slice.ts`, `.selector.ts`, `.provider.ts`). Never use `helper.ts`, `common.ts`, or `index.ts`. See [references/module-slicing.md](references/module-slicing.md).

---

## 2. The No-Inline-`className` Rule & UI Reuse

Both `.component.tsx` views and Next.js `page.tsx`/`layout.tsx` files must contain **zero `className` and zero `style` attributes**. See [references/layers-and-nextjs-routes.md](references/layers-and-nextjs-routes.md) and [references/ui-reuse-and-promotion.md](references/ui-reuse-and-promotion.md) for side-by-side `❌ BAD` vs. `✅ GOOD` code.

- **Single Source of Truth for Visuals**: Never create duplicate UI primitives for different placements (e.g. separate HTTP badges for cards and dropdowns). Reuse one canonical `/components/[module]/[name].ui.tsx` primitive with size/variant props backed by `/constants/[name].constant.ts`.
- **1:1 Nesting & 3-Level Promotion Scale**:
  - **Level 1** (1 parent only): `features/[feature]/components/[parent]/components/[child]/` (no sibling or external imports).
  - **Level 2** (≥2 components in 1 feature): `features/[feature]/components/[child]/` (or `features/[feature]/hooks|types|constants|utils/`).
  - **Level 3** (≥2 features / app-wide): Promote (move, never copy) to root `/components/`, `/layouts/`, `/hooks/`, `/types/`, `/constants/`, or `/utils/`.

---

## 3. Code Hygiene, Type-Safety & Function Comments

Full code examples and patterns are in [references/type-safety-and-comments.md](references/type-safety-and-comments.md).

- **4A. Never declare `undefined`**: Use `T | null` with explicit `null` initializers. `?` is only allowed on outer `Props` interfaces.
- **4B–4C. Strict types**: No `any`, no `@ts-ignore`/`@ts-expect-error`, no `as` casts (use type guards in `.util.ts`), and no non-null assertions (`!`).
- **4D–4E. Hook boundary**: Resolve all optional props to concrete defaults inside `.hook.ts`; never spread `{...props}` to children.
- **4F–4G. Naming & constants**: Prefix booleans with `is`/`has`/`can`/`should`. Extract magic literals and class maps to `.constant.ts` (`SCREAMING_SNAKE_CASE`).
- **4H. Explicit async state**: `.service.ts` functions and store slices return `RequestState<T>` (`{ status: "idle" | "loading" | "success" | "error", data: T | null, error: string | null }`) and never throw past their boundary.
- **4I–4J. Clean interfaces**: Zero unused declarations. Name prop handlers as domain actions (`onDeleteUser(userId)`), never DOM events (`onClick(e)`).
- **4K–4M. Architectural gates**: Zero duplicate UI primitives (§0B), SSR + zero-`className` + strict imports on Next.js routes (§1E), and mandatory Pre-Implementation Plan & File Tree Confirmation before coding (§0).
- **5. Lean Function Doc Block**: Every non-trivial exported function (never `.component.tsx` or `page.tsx` views) carries a max 5-line `what` / `param` / `return` comment block directly above the function declaration, omitting anything obvious from the name and types, and using **zero inline `//` comments on code lines inside function bodies**.
