---
name: project-react-architecture
description: "Use whenever building or editing ANY React/Next.js UI or route — pages, layouts, routers, cards, forms, dropdowns, dashboards, modals, buttons, tables, badges — even if the user doesn't say 'component,' 'layout,' or name a file type. Also use when refactoring existing components/pages, splitting a growing module into semantic submodules, or deciding where a shared type/constant/hook/util/UI primitive should live. Enforces: BEFORE writing or editing any code, scan existing project files, make explicit layer/scope placement decisions, output an annotated File Tree Plan (`[NEW]`, `[UPDATE]`, `[REUSE]`, `[PROMOTE]`), and confirm with the user first that the implementation plan is valid; scan `/components/**` and `/layouts/**` to eliminate duplicate UI components; code shared across features or used app-wide lives at the PROJECT ROOT (`/components/[module]/[name].ui.tsx`, `/layouts/[category]/[name].layout.tsx`, `/hooks/[name].hook.ts`, `/types/[name].type.ts`, `/constants/[name].constant.ts`, `/utils/[name].util.ts`), never inside a feature; only single-feature code lives under `features/[feature]/`; both feature components (`features/[feature]/components/[name]/`) and Next.js page/router components (`app/**/page.tsx`, `app/**/layout.tsx`, `pages/**`) use zero inline className styling; Next.js pages are always Server-Side Rendered (Server Components — never `'use client'`); page/router files only import `.ui.tsx` primitives, `.layout.tsx` containers, and public components from `[feature].feature.ts` (never deep-importing internal feature files); and every exported non-trivial function carries a fixed comment block."
---

# React Clean Component Architecture

Every UI and code element belongs to exactly one layer. The project root holds everything that is **shared across features or used app-wide**; `features/` holds only what belongs to a single domain; and Next.js route/page files act purely as Server-Side Rendered (SSR), zero-`className` composition shells:

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

## 0. Pre-Implementation Decision & File Tree Confirmation Protocol (MANDATORY FIRST STEP)

Whenever the user asks to add, build, update, or refactor any feature, component, or page (e.g. *"add X..."*, *"build a Y page..."*), **DO NOT jump straight to writing or modifying files**. You must first follow this **3-Step Scan → Decide & Plan Tree → Confirm** workflow:

### Step 1: Scan Existing Codebase
Scan `[project]/components/**`, `/layouts/**`, `/constants/**`, `/types/**`, `/hooks/**`, `/utils/**`, `features/**`, and `app/**` to see what already exists and can be reused, extended, or promoted.

### Step 2: Run the Layer & Scope Decision Checklist
For every piece required by the request, decide its exact placement and action in order:

1. **Does a matching or partial UI primitive / layout container already exist?** → Scan `/components/**` and `/layouts/**` BEFORE creating any new UI (§0B).
   - If an exact match exists → mark as **`[REUSE]`**; do not create duplicate UI components.
   - If a partial match exists (e.g. missing HTTP method, prop, or variant) → mark as **`[UPDATE]`** and explain what will be extended in the confirmation plan.
   - If none exists → mark as **`[NEW]`** at `/components/[module]/[name].ui.tsx`, designed as a canonical primitive reusable across cards, tables, and dropdowns.
2. **Is it purely visual/presentational with no domain logic?** → `.ui.tsx` in `/components/[module]/` (§1A).
3. **Is it pure structure (flex/grid/spacing) with no visuals or logic?** → `.layout.tsx` in `/layouts/[category]/` (§1B).
4. **Does it connect business state/hooks to UI + Layout primitives?** → feature component in `features/[feature]/components/[name]/` (§1D).
5. **Is it a Next.js page or router file (`app/**/page.tsx`, `app/**/layout.tsx`, `pages/**`)?** → keep it **Server-Side Rendered (SSR / Server Component — never `'use client'`)**, treat it like a feature component view with **zero custom `className`**, and import **only** `.ui.tsx` primitives, `.layout.tsx` containers, and public components from `[feature].feature.ts` — never deep-import internal `features/[feature]/components/**` (§1E, §2).
6. **Is it a type, constant, hook, or helper?** Decide by consumer count, not by convenience:
   - Used by **≥2 features or app-wide** → **root project**: `/types`, `/constants`, `/hooks`, `/utils` (see §0A). If an existing feature file just gained a second feature consumer, mark it as **`[PROMOTE]`** to move it to root (§3B).
   - Used by **1 feature only** → feature-scoped: `features/[feature]/types|constants|hooks|utils/`.
7. **Is it a sub-component used by exactly one parent?** → Nest it (§3), then re-check the promotion scale (§3B) the moment a second consumer appears.

If a file would mix two of these concerns (e.g. styling + business logic), split it — that split is the point of this architecture, not an edge case to work around.

### Step 3: Output the Architecture Decision Plan & File Tree and Ask for Confirmation
Before creating or editing any code file (unless the user explicitly says *"skip confirmation"* or *"implement immediately"*), present:
1. **Architectural Decisions**: A concise bullet list explaining *why* each element is placed in its layer, what existing primitives are reused (`[REUSE]`) or extended (`[UPDATE]`), and how SSR/import boundaries are preserved.
2. **Proposed File Tree**: An ASCII tree listing every file touched or relied upon, tagged with `[NEW]`, `[UPDATE]`, `[REUSE]`, or `[PROMOTE]` and a 1-line summary of its role.
3. **User Confirmation Prompt**: Ask the user to confirm that the plan and file tree are valid before writing the code.

#### Canonical Plan & File Tree Confirmation Template

```text
### 1. Architectural Decisions
- **UI Primitives & Layouts**:
  - `[REUSE]` `/layouts/page/pageLayout.layout.tsx` & `/layouts/card/cardLayout.layout.tsx` for page and card framing.
  - `[UPDATE]` `/components/badge/httpBadge.ui.tsx` & `/constants/httpBadge.constant.ts` — add `PUT`, `PATCH`, `DELETE` and `size="sm"` so both the endpoint card and dropdown selector share one primitive.
- **Shared vs. Feature Scope**:
  - `httpBadge.constant.ts` lives at project root `/constants/` because it is shared across `apiDocs` and `apiTester` (≥2 features).
  - `methodDropdown` is specific to `apiTester`, so its `.component.tsx`, `.hook.ts`, and `.type.ts` live under `features/apiTester/components/methodDropdown/` and are exported via `apiTester.feature.ts`.
- **Next.js SSR Page Boundary**:
  - `[NEW]` `/app/api-playground/page.tsx` is an SSR Server Component (no `'use client'`, zero `className`) importing only `.layout.tsx`, `.ui.tsx`, and `apiTester.feature.ts`.

### 2. Proposed File Tree
[project]/
├── app/api-playground/
│   └── page.tsx                                           # [NEW] SSR Server Component page shell (zero className)
├── components/
│   ├── badge/httpBadge.ui.tsx                             # [UPDATE] Add compact size="sm" variant
│   └── text/headingText.ui.tsx                            # [REUSE] Canonical heading primitive
├── constants/
│   └── httpBadge.constant.ts                              # [UPDATE] Add PUT/PATCH/DELETE styles & HTTP_BADGE_SIZE_MAP
├── layouts/
│   ├── card/cardLayout.layout.tsx                         # [REUSE] Card structural wrapper
│   └── page/pageLayout.layout.tsx                         # [REUSE] Page structural wrapper
└── features/
    └── apiTester/
        ├── apiTester.feature.ts                           # [NEW] Public feature entrypoint exporting MethodDropdown
        └── components/
            └── methodDropdown/
                ├── methodDropdown.component.tsx           # [NEW] Pure JSX view (zero className)
                ├── methodDropdown.hook.ts                 # [NEW] Dropdown selection state & handlers
                └── methodDropdown.type.ts                 # [NEW] Props & dropdown types

Does this architecture plan and file tree look valid to proceed with implementation?
```

### 0A. Shared code lives at the project root, never inside a feature

This is the most common placement mistake, so decide it before anything else: **if a `.type.ts`, `.constant.ts`, `.hook.ts`, `.util.ts`, or `.ui.tsx` is shared across features — or is genuinely app-wide — it belongs at the [project] root, not inside `features/[feature]/`.** A feature may only own code that no other feature needs.

The root is split by kind, exactly mirroring the feature layout:

| Shared thing                                          | Root location                          | First imported by                    |
| ----------------------------------------------------- | -------------------------------------- | ------------------------------------ |
| Presentational primitive (raw CSS)                    | `[project]/components/[module]/[name].ui.tsx` | ≥2 features / app-wide        |
| Structural container                                  | `[project]/layouts/[category]/[name].layout.tsx` | ≥2 features / app-wide         |
| Hook (state, selectors, effects)                      | `[project]/hooks/[name].hook.ts`       | ≥2 features                          |
| Shared type / interface / union                       | `[project]/types/[name].type.ts`       | ≥2 features / app-wide               |
| Shared constant / config / map                        | `[project]/constants/[name].constant.ts` | ≥2 features / app-wide             |
| Shared pure helper                                    | `[project]/utils/[name].util.ts`       | ≥2 features                          |

Rules that keep this honest:

- **A `.ui.tsx` never lives under a feature.** UI primitives are global by definition — if you are writing one, it goes to `[project]/components/[module]/`. A feature composes primitives; it does not own them.
- **Constants/helpers that even *look* reusable (theme tokens, formatting, validation, route maps, enums used for display) go to the root**, because "used by 1 feature today" almost always becomes "used by 2 tomorrow." Only keep a constant/helper in a feature when it is genuinely domain-specific to that feature's own logic.
- **Import direction is one-way: `features/` → root, never root → `features/`.** A root `.util.ts`, `.hook.ts`, `.ui.tsx`, or `.type.ts` must not import from any `features/` folder. If a shared file needs feature-specific data, the data is passed in as a parameter or prop — that keeps the root layer dependency-free and reusable.
- **Root files import siblings by direct path** (`@/utils/formatDate.util`, `@/types/user.type`), never through a global `index.ts` barrel (§1C).
- **When a feature-scoped file gains a second feature consumer, promote it in the same change** — move it from `features/[feature]/…` up to the matching root folder and update every import (§3B, Level 2 → Level 3). Leaving a copy in the feature after promotion creates two sources of truth.

### 0B. Scan before creating: single source of truth for UI primitives (Zero duplication)

A frequent architectural failure is recreating duplicate UI components for the same visual concept across different placements — for example, building an HTTP method badge for an endpoint detail card, and then building a second, separate HTTP badge component for a dropdown selector, and a third inside an API log table. This leads to duplicate styling, inconsistent colors/padding across screens, and an unnecessarily heavy app.

Every recurring visual element must have **exactly one canonical UI primitive** in `[project]/components/[module]/`.

Follow the **Scan → Evaluate → Ask → Reuse** protocol before writing any UI code:

#### 1. Mandatory Inventory Scan
Before creating any `.ui.tsx` file or building a feature sub-component that renders visual tags, badges, buttons, inputs, or indicators:
- Scan `[project]/components/**` (and `/layouts/**`, `/constants/**`) to see what primitives already exist.
- Look across component modules (e.g. `/components/badge/`, `/components/tag/`, `/components/button/`, `/components/indicator/`).

#### 2. Evaluate: Exact Fit vs. Extension
- **Exact match**: Reuse the existing primitive directly across all features, cards, dialogs, and dropdowns.
- **Partial match** (component exists, but lacks a required variant, size, or supported value — e.g. `httpBadge` exists with `GET`/`POST`, but now needs `PUT`/`PATCH`/`DELETE`, or a compact `size="sm"` for dropdown menus):
  - ❌ **NEVER** create a second, placement-specific duplicate (e.g. `dropdownHttpBadge.ui.tsx`, `endpointBadge.ui.tsx`, or inline badge markup inside a feature).
  - ❌ **NEVER** make breaking alterations silently.
  - ✅ **Ask the user first**: Explain what already exists, specify what is missing, and ask whether to update the existing shared primitive or create a new one.

> **Prompting pattern when an update is needed:**
> "Found existing UI primitive at `[project]/components/badge/httpBadge.ui.tsx` supporting `GET` and `POST`. To support our method selector dropdown and API views with `PUT`, `PATCH`, and `DELETE` (and a compact `size="sm"`), should we update `httpBadge.ui.tsx` and its constants map, or is a separate primitive preferred? (Recommended: update the existing primitive to keep badge styling consistent app-wide)."

#### 3. Canonical Example: Shared HTTP Method Badge
Instead of duplicating badges across dropdowns and detail views, define one shared primitive backed by constants:

```ts
// /constants/httpBadge.constant.ts
export const HTTP_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE"] as const;
export type HttpMethod = (typeof HTTP_METHODS)[number];

export const HTTP_METHOD_STYLE_MAP: Record<
  HttpMethod,
  { bg: string; text: string; border: string }
> = {
  GET: { bg: "bg-blue-500/10", text: "text-blue-500", border: "border-blue-500/20" },
  POST: { bg: "bg-green-500/10", text: "text-green-500", border: "border-green-500/20" },
  PUT: { bg: "bg-amber-500/10", text: "text-amber-500", border: "border-amber-500/20" },
  PATCH: { bg: "bg-orange-500/10", text: "text-orange-500", border: "border-orange-500/20" },
  DELETE: { bg: "bg-red-500/10", text: "text-red-500", border: "border-red-500/20" },
};

export const HTTP_BADGE_SIZE_MAP = {
  sm: "px-1.5 py-0.5 text-[10px]",
  md: "px-2 py-1 text-xs",
} as const;
```

```tsx
// /components/badge/httpBadge.ui.tsx
import {
  HTTP_METHOD_STYLE_MAP,
  HTTP_BADGE_SIZE_MAP,
  type HttpMethod,
} from "@/constants/httpBadge.constant";

export interface HttpBadgeProps {
  method: HttpMethod;
  size?: "sm" | "md";
}

export default function HttpBadge({ method, size = "md" }: HttpBadgeProps) {
  const styles = HTTP_METHOD_STYLE_MAP[method];
  return (
    <span
      className={`inline-flex items-center font-mono font-semibold rounded border ${styles.bg} ${styles.text} ${styles.border} ${HTTP_BADGE_SIZE_MAP[size]}`}
    >
      {method}
    </span>
  );
}
```

Both features pick and reuse the same canonical primitive:

```tsx
// /features/apiDocs/components/endpointCard/endpointCard.component.tsx
// Usage in feature display: just pick from the shared badge primitive
import HttpBadge from "@/components/badge/httpBadge.ui";

export default function EndpointCard({ method, path }: EndpointCardProps) {
  return (
    <CardLayout>
      <HttpBadge method={method} />
      <PathText>{path}</PathText>
    </CardLayout>
  );
}
```

```tsx
// /features/apiTester/components/methodDropdown/methodDropdown.component.tsx
// Usage in dropdown option: reuses the exact same badge primitive with compact size
import HttpBadge from "@/components/badge/httpBadge.ui";

export default function MethodOption({ method, label }: MethodOptionProps) {
  return (
    <OptionLayout>
      <HttpBadge method={method} size="sm" />
      <OptionLabel>{label}</OptionLabel>
    </OptionLayout>
  );
}
```

Neither the dropdown nor the endpoint card re-invents a badge. The design is identical, styles are centralized, and the app avoids duplicate UI code.

---

## 1. Core Architecture Layers

### A. UI System Components (`/components/[module]/[name].ui.tsx`)

Self-contained, presentational visual building blocks grouped by module (button, text, input, badge).

- **Rule**: Exactly 1 file per component, holding its Props interface, styling, and render. No feature/business logic. This is the only layer where raw CSS/Tailwind classes live.
- **Context-neutral & Reusable**: Primitives are placement-agnostic. Never create placement-bound variations like `dropdownHttpBadge.ui.tsx` or `tableBadge.ui.tsx`. Pass sizing, variants, or slot props so the same primitive serves cards, dropdowns, tables, and modals (§0B).
- **Examples**: `/components/button/primaryButton.ui.tsx`, `/components/text/dimmedText.ui.tsx`

```tsx
// /components/button/confirmButton.ui.tsx
import { Button } from "@/components/ui/button";

export interface ConfirmButtonProps {
  label: string;
  onConfirm: () => void;
  destructive?: boolean;
}

export default function ConfirmButton({
  label,
  onConfirm,
  destructive,
}: ConfirmButtonProps) {
  return (
    <Button
      variant={destructive ? "destructive" : "default"}
      size="sm"
      onClick={onConfirm}
    >
      {label}
    </Button>
  );
}
```

### B. Layout Containers (`/layouts/[category]/[name].layout.tsx`)

Pure structural containers managing flex/grid geometry, spacing, alignment, padding, borders.

- **Categorization**: Group by structural purpose (`dashboard/`, `flex/`, `grid/`, `card/`, `dialog/`, `panel/`, `page/`...). Never place layout files flat in the root `/layouts/` folder.
- **Rule**: Exactly 1 file per container. Accepts `children` or slot props. Zero domain logic, zero branding.
- **Examples**: `/layouts/card/cardLayout.layout.tsx`, `/layouts/flex/flexRow.layout.tsx`

```tsx
// /layouts/card/cardLayout.layout.tsx
import type { ReactNode } from "react";
import { CARD_PADDING_CLASS_MAP } from "@/constants/layout.constant";

export interface CardLayoutProps {
  children: ReactNode;
  padding?: "sm" | "md" | "lg";
}

export default function CardLayout({
  children,
  padding = "md",
}: CardLayoutProps) {
  return (
    <div
      className={`flex flex-col gap-3 rounded-lg border bg-card ${CARD_PADDING_CLASS_MAP[padding]}`}
    >
      {children}
    </div>
  );
}
```

```ts
// /constants/layout.constant.ts
export const CARD_PADDING_CLASS_MAP = {
  sm: "p-3",
  md: "p-4",
  lg: "p-6",
} as const;
```

This map is itself a repeated enum-like lookup (`"sm" | "md" | "lg"` → class), so it lives in `/constants/` per Rule G (§4G) — never inline inside the `.layout.tsx`, even though the layout is its only consumer today.

### C. App-Wide Shared Code (root `/hooks`, `/types`, `/constants`, `/utils`)

The root is where cross-feature and app-wide code lives. Everything here obeys the same consumer-count rule: **≥2 features (or genuinely app-wide) → root; 1 feature → feature folder** (§0A).

- **`/types/[name].type.ts`**: data models, shared interfaces, common unions used across ≥2 features (e.g. `layout.type.ts`, `user.type.ts`, `api.type.ts`).
- **`/constants/[name].constant.ts`**: static configs, theme maps, shared constants (e.g. `layout.constant.ts`, `routes.constant.ts`).
- **`/hooks/[name].hook.ts`**: hooks, store selectors, and effects reused by ≥2 features (e.g. `useMediaQuery.hook.ts`, `useDebouncedValue.hook.ts`). Feature-only hooks stay in `features/[feature]/hooks/`.
- **`/utils/[name].util.ts`**: pure, dependency-light helpers reused by ≥2 features (e.g. `formatDate.util.ts`, `slugify.util.ts`). Feature-only helpers stay in `features/[feature]/utils/`.
- **`/components/[module]/`** and **`/layouts/[category]/`** are also root shared layers: `.ui.tsx` primitives and `.layout.tsx` containers are global and never live under a feature (§0A, §1A, §1B).
- **No barrel exports at this layer.** Unlike feature modules, `/components`, `/layouts`, `/hooks`, `/types`, `/constants`, and `/utils` are always imported by their direct file path (e.g. `@/components/button/confirmButton.ui`, `@/utils/formatDate.util`), never through an `index.ts` re-export. A global barrel would force every consumer to pull in the whole layer's dependency graph and makes tree-shaking and promotion (§3B) harder to reason about.
- **One-way imports.** These root files must not import from `features/`; feature code flows into the root, not the other way around (§0A).

### D. Feature Components (`features/[feature]/components/[name]/`)

Domain orchestrators connecting business state/hooks to UI and Layout primitives.

```
features/[feature]/
├── [feature].feature.ts    # Public feature entrypoint (only public APIs)
├── components/
│   └── [component_name]/   # 1 folder per component
│       ├── [component_name].component.tsx # Pure JSX view (ZERO inline className)
│       ├── [component_name].hook.ts      # React state, hooks, store selectors, handlers
│       ├── [component_name].type.ts      # Props & component-specific types
│       ├── [component_name].constant.ts  # Static constants & labels (optional)
│       ├── [component_name].util.ts      # Pure calculation helpers (optional)
│       └── [component_name].service.ts   # Network & API calls (optional)
├── hooks/     # Feature-wide hooks & store slices
├── types/     # Feature domain types
├── constants/ # Feature-wide constants
└── utils/     # Feature-wide helpers
```

**Export rule**: `.component.tsx` uses a default export. Hooks, types, and constants use named exports. The feature entrypoint uses named exports and is imported explicitly as `[feature].feature.ts`; do not create a generic `index.ts` for feature modules.

**Naming convention**: every filename (`.ui.tsx`, `.layout.tsx`, `.component.tsx`, `.feature.ts`, `.hook.ts`, `.type.ts`, `.constant.ts`, `.util.ts`, `.service.ts`, `.rule.ts`, `.factory.ts`, `.geometry.ts`, `.mapper.ts`, `.parser.ts`, `.format.ts`, `.export.ts`, `.slice.ts`) is **camelCase**, matching the module it belongs to (`userCard.component.tsx`, `publicDatabaseAccess.rule.ts`). The React component/function it exports is **PascalCase** (`UserCard`). Hooks and rule functions are `camelCase` with a meaningful verb (`useUserCard`, `runPublicDatabaseAccess`). Types and interfaces are `PascalCase` (`UserCardProps`). Constants are `SCREAMING_SNAKE_CASE` (`CARD_PADDING_CLASS_MAP`). Never mix conventions across a file/export pair — the filename casing never changes just because the layer changed.

**`.service.ts` and store slices**: a `.service.ts` function must return the `RequestState<T>` shape defined in §4A/§4H — never throw past its own boundary and never resolve to a bare `T | undefined`. Feature `hooks/` store slices follow the same shape: model `status: "idle" | "loading" | "success" | "error"` explicitly rather than separate `isLoading`/`error` fields that can drift out of sync with each other.

**`'use client'` / `'use server'` placement**:

- **Next.js `page.tsx` and `layout.tsx` are always Server-Side Rendered (Server Components)** — **never** place `'use client'` on a `page.tsx` or `layout.tsx` file (§1E). Client interactivity is pushed down to individual feature `.component.tsx` leaves.
- `.ui.tsx` and `.layout.tsx` files are presentational and should stay server-renderable by default — add `'use client'` only if the primitive itself needs browser APIs or interactivity that can't be lifted to the caller (rare; prefer passing handlers down instead).
- `.component.tsx` gets `'use client'` at the very top of the file whenever its `.hook.ts` uses state, effects, or browser-only APIs — which is the common case for interactive feature components.
- `.hook.ts`, `.util.ts`, and `.type.ts` never declare `'use client'`/`'use server'` themselves; the directive belongs on the `.component.tsx` that consumes them, not on every file in the chain.
- `.service.ts` gets `'use server'` only when it is a Server Action being called directly from a client component; plain fetch-based services making calls from the server need neither directive.

### E. Next.js Page & Router Components (`app/**/page.tsx`, `app/**/layout.tsx`, `pages/**`)

Next.js route entrypoints (`page.tsx`, `layout.tsx`, `loading.tsx`, `not-found.tsx`, and Pages Router files) **must be Server-Side Rendered (SSR) and act like feature component views**:

- **Always Server-Side Rendered (Server Component — NEVER `'use client'`)**:
  - `app/**/page.tsx` and `app/**/layout.tsx` must **never** declare `'use client'`. Keeping pages on the server guarantees SSR html delivery, allows `async` server component execution (awaiting route `params`/`searchParams` or server data), preserves Next.js `metadata` / `generateMetadata` exports, and prevents the entire route tree from being forced into the client bundle.
  - Client interactivity (`useState`, `useEffect`, event handlers) belongs strictly inside the feature's `.component.tsx` + `.hook.ts` leaf components, which are imported into the SSR page via `[feature].feature.ts`.
- **Zero custom `className` or inline `style`**: A page or route layout must never contain raw Tailwind classes, CSS utility strings, or styled HTML wrappers (`<main className="p-6">`, `<div className="flex gap-4">`). All visual and structural framing comes from `.ui.tsx` primitives and `.layout.tsx` containers (§2).
- **Strict Import Allowlist**: A Next.js page or router component may **only** import UI and components from:
  1. **UI System Primitives**: `@/components/[module]/[name].ui` (`.ui.tsx`)
  2. **Public Feature Entrypoints**: `@/features/[feature]/[feature].feature` (`[feature].feature.ts`)
  3. **Layout Containers** (when structural framing is needed): `@/layouts/[category]/[name].layout` (`.layout.tsx`)
- **Never deep-import inside a feature**: Route files must **never** import directly from `features/[feature]/components/[name]/[name].component.tsx`, `features/[feature]/hooks/`, or `features/[feature]/utils/`. Any feature component rendered on a page must be exported from `[feature].feature.ts` and imported from that `[feature].feature` entrypoint.
- **No inline business logic or client hooks in `page.tsx`**: Keep route files as thin SSR composition shells. Domain state, event handlers, and feature logic belong inside the feature's own `.component.tsx` + `.hook.ts`, exposed via `[feature].feature.ts`.

```ts
// /features/users/users.feature.ts
export { default as UserDirectory } from "./components/userDirectory/userDirectory.component";
export { default as UserInviteModal } from "./components/userInviteModal/userInviteModal.component";
```

```tsx
// /app/users/page.tsx (Server Component / SSR — NO "use client")
import PageLayout from "@/layouts/page/pageLayout.layout";
import HeadingText from "@/components/text/headingText.ui";
import { UserDirectory, UserInviteModal } from "@/features/users/users.feature";

export default async function UsersPage() {
  return (
    <PageLayout>
      <HeadingText>Team Members</HeadingText>
      <UserInviteModal />
      <UserDirectory />
    </PageLayout>
  );
}
```

---

## 1F. Growing Module Slicing

Start with one focused file in any layer. When a component, hook, service, store, feature module, or utility accumulates independently changing responsibilities, split it into a named folder instead of allowing one file to become a navigation bottleneck. The split is justified when a file contains multiple rule families, transformations, formats, factories, state domains, UI subviews, or other responsibilities that developers need to find independently.

The folder keeps one explicit public entrypoint named after the domain, at the same path depth as the flat file it replaced (`utils/[utilName]/[utilName].util.ts`, `hooks/[hookName]/[hookName].hook.ts`). The entrypoint is the folder's public surface — it holds the main implementation and re-exports the stable API; consumers import the entrypoint, never the internal files. Internal implementations live in semantic subfolders whose suffix describes what each file does, named `[main function name].[subfolder].ts` so the file says which entrypoint owns it and what role it plays:

```text
[project]/utils/requestPolicy/        # root slice — shared by ≥2 features
├── requestPolicy.util.ts             # public entrypoint: main implementation + re-exports
└── rules/
    ├── authentication.rule.ts
    ├── authorization.rule.ts
    └── rateLimit.rule.ts

[project]/utils/layoutModel/          # root slice
├── layoutModel.util.ts               # entrypoint
└── geometries/
    ├── bounds.geometry.ts
    ├── collision.geometry.ts
    └── grid.geometry.ts

[project]/hooks/useSearch/            # root slice — shared by ≥2 features
├── useSearch.hook.ts                 # entrypoint
└── selectors/
    ├── matchingItems.selector.ts
    └── groupedResults.selector.ts

features/[feature]/utils/requestPolicy/
├── requestPolicy.util.ts
└── rules/
    ├── authentication.rule.ts
    ├── authorization.rule.ts
    └── rateLimit.rule.ts

features/[feature]/utils/layoutModel/
├── layoutModel.util.ts
└── geometries/
    ├── bounds.geometry.ts
    ├── collision.geometry.ts
    └── grid.geometry.ts

features/[feature]/utils/entityBuilder/
├── entityBuilder.util.ts
└── factories/
    ├── user.factory.ts
    └── product.factory.ts

features/[feature]/utils/reportExport/
├── reportExport.util.ts
└── exports/
    ├── csv.export.ts
    ├── json.export.ts
    └── pdf.export.ts

features/[feature]/components/orderSummary/
├── orderSummary.component.tsx
└── components/
    ├── orderLine.component.tsx
    └── totalsPanel.component.tsx

features/[feature]/hooks/useSearch/
├── useSearch.hook.ts
└── selectors/
    ├── matchingItems.selector.ts
    └── groupedResults.selector.ts

features/[feature]/services/payment/
├── payment.service.ts
└── providers/
    ├── card.provider.ts
    └── wallet.provider.ts
```

Use the implementation suffix, not a generic child marker, because it tells the next developer why the file exists:

- `.rule.ts`: one validation, audit, or policy rule
- `.factory.ts`: object or domain-node construction
- `.geometry.ts`: coordinate, size, grid, or collision calculations
- `.mapper.ts`: transformation between representations
- `.parser.ts`: parsing and normalization from text or external data
- `.format.ts`: serialization or display formatting
- `.export.ts`: a specific export target or transport
- `.slice.ts`: one state-management slice only
- `.selector.ts`: one derived-state selector
- `.provider.ts`: one external provider implementation

The public entrypoint (`[utilName].util.ts` / `[hookName].hook.ts`) is where the main exported function lives — it either implements the top-level logic or composes the internals — and it re-exports the stable API the subfolders provide. Consumers import the entrypoint; sibling implementations import shared types/constants explicitly. Do not use generic names such as `helper.ts`, `common.ts`, `part.ts`, `runName.ts`, or `index.ts` to indicate that a file belongs to a larger module. Directory scope plus semantic suffix provides that relationship without hiding the implementation's responsibility.

This slicing rule is **the same at the root and inside a feature** — only the parent path differs (`[project]/utils/…` for cross-feature code, `features/[feature]/utils/…` for single-feature code). The folder name matches the entrypoint file name at both scopes.

When a feature grows, use the same rule:

```text
features/editor/
├── editor.feature.ts
├── components/
├── hooks/
└── utils/
```

The `[feature].feature.ts` file is the public feature entrypoint. It replaces a generic `index.ts`, makes imports searchable, and prevents unrelated feature APIs from becoming indistinguishable. Keep internal implementation files behind that entrypoint unless a consumer explicitly needs a lower-level public contract.

Do not split cohesive small modules only to satisfy a folder pattern. Slice a module when the semantic boundaries reduce search cost and independent changes become easier to review.

---

## 2. The No-Inline-`className` Rule (Feature Components & Next.js Pages/Routers)

Both `.component.tsx` files **and Next.js page/router files** (`app/**/page.tsx`, `app/**/layout.tsx`, `pages/**`) must contain **zero inline styles and zero `className` attributes**.
- All visual styling and structure come from composing UI System components (`/components/[module]/[name].ui.tsx`) and Layout Containers (`/layouts/[category]/[name].layout.tsx`).
- Furthermore, Next.js page/router files must be **Server-Side Rendered (Server Components — never `'use client'`)** and may **only** import `.ui.tsx` primitives, `.layout.tsx` containers, and public components from `[feature].feature.ts` — never deep-importing internal feature files (§1E).

### ❌ BAD — ad-hoc inline styling in a feature component or Next.js page

```tsx
// ❌ BAD Feature Component: raw HTML tags and custom className
export default function UserCard({ user, onDelete }: UserCardProps) {
  return (
    <div className="flex flex-col gap-2 rounded-lg border bg-card p-4">
      <p className="text-sm font-medium text-gray-500">{user.role}</p>
      <h3 className="text-lg font-bold text-gray-900">{user.name}</h3>
      <button
        className="rounded bg-red-600 px-3 py-1.5 text-xs text-white"
        onClick={onDelete}
      >
        Delete
      </button>
    </div>
  );
}
```

```tsx
// ❌ BAD Next.js Page (app/users/page.tsx): "use client" on page + custom className + deep feature import
"use client";
import UserCard from "@/features/users/components/userCard/userCard.component";

export default function UsersPage() {
  return (
    <main className="mx-auto flex max-w-5xl flex-col gap-6 p-8">
      <h1 className="text-2xl font-bold tracking-tight">Users</h1>
      <UserCard />
    </main>
  );
}
```

### ✅ GOOD — composing UI primitives, Layouts, and `[feature].feature.ts`

```tsx
// ✅ GOOD Feature Component (/features/users/components/userCard/userCard.component.tsx)
"use client";
import type { UserCardProps } from "./userCard.type";
import { useUserCard } from "./userCard.hook";
import CardLayout from "@/layouts/card/cardLayout.layout";
import DimmedText from "@/components/text/dimmedText.ui";
import ParagraphText from "@/components/text/paragraphText.ui";
import DeleteButton from "@/components/button/deleteButton.ui";

export default function UserCard(props: UserCardProps) {
  const { user, handleDelete } = useUserCard(props);
  return (
    <CardLayout>
      <DimmedText>{user.role}</DimmedText>
      <ParagraphText bold>{user.name}</ParagraphText>
      <DeleteButton onClick={handleDelete}>Delete</DeleteButton>
    </CardLayout>
  );
}
```

```tsx
// ✅ GOOD Next.js Page (/app/users/page.tsx): SSR Server Component (no "use client"), zero className, imports only .ui, .layout, and [feature].feature
import PageLayout from "@/layouts/page/pageLayout.layout";
import HeadingText from "@/components/text/headingText.ui";
import { UserCard } from "@/features/users/users.feature";

export default async function UsersPage() {
  return (
    <PageLayout>
      <HeadingText>Users</HeadingText>
      <UserCard />
    </PageLayout>
  );
}
```

---

## 3. Sub-Components & Promotion Rules

### A. Strict Nesting Invariant (1:1 Parent Ownership)

A nested sub-component (`features/[feature]/components/[parent]/components/[child]/`) is **only** allowed if used exclusively by that one `[parent]`. No sibling, no other feature component, and no other layer may import it directly. Deep sibling imports (`../parentA/components/childB`) are forbidden.

### B. Promotion Scale

| Level | Scope & usage                             | Location                                                                                        |
| ----- | ----------------------------------------- | ----------------------------------------------------------------------------------------------- |
| **1** | Private to 1 parent                       | `features/[feature]/components/[parent]/components/[child]/`                                    |
| **2** | Used by ≥2 components in the same feature | `features/[feature]/components/[child]/` (or `features/[feature]/hooks\|types\|constants\|utils/`) |
| **3** | Used across multiple features / app-wide  | Project root: `/components/`, `/layouts/`, `/hooks/`, `/types/`, `/constants/`, `/utils/`      |

**Promoting Level 1 → Level 2**: As soon as a Level-1 child is needed anywhere else in the same feature (e.g. `calendarDropdown`, nested under `yearDashboard`, is also needed by `monthDashboard`), move it up to `features/dashboard/components/calendarDropdown/`. Both parents then import it from the feature level — never from each other's nested folders.

**Promoting Level 2 → Level 3**: As soon as an element is needed across multiple features, move it to the matching root layer — a feature is left owning nothing that another feature also needs (§0A):

- Visual primitives / `.ui.tsx` (raw CSS) → `/components/[module]/[name].ui.tsx`
- Structural containers → `/layouts/[category]/[name].layout.tsx`
- Shared hooks / selectors → `/hooks/[name].hook.ts`
- Shared data types → `/types/[name].type.ts`
- Shared constants/config → `/constants/[name].constant.ts`
- Shared pure helpers → `/utils/[name].util.ts`

Promotion means **moving**, not copying: update every import to the root path and delete the feature-scoped original in the same change.

---

## 4. Code Hygiene & Type-Safety Rules

These apply to every file in every layer. A loosely-typed or silently-`undefined` value is a runtime crash waiting to happen, and in a decomposed architecture the crash hides exactly where layers connect.

### A. Never declare `undefined`

`undefined` means "no explicit statement about why or when a value is missing" — every consumer has to guess. `null` is a deliberate, checkable "no value." If a value can be absent, type it `T | null` with an explicit initial value; if it starts empty, model the real empty state (`[]`, `""`, `0`, a sentinel, or a `status` union) instead of `undefined`.

```tsx
// ❌ BAD
let selectedId: string | undefined = undefined;
const [user, setUser] = useState<User | undefined>();

// ✅ GOOD
let selectedId: string | null = null;
const [user, setUser] = useState<User | null>(null);

type RequestState<T> = {
  status: "idle" | "loading" | "success" | "error";
  data: T | null;
  error: string | null;
};
```

`RequestState<T>` above is the canonical shape referenced by §1D and §4H — define it once per feature (or globally in `/types/` if shared across ≥2 features) and reuse it rather than restating the fields ad hoc.

The `?` optional marker is the same violation in disguise — it silently widens to `T | undefined`. It's **only** acceptable on an outer Props interface, meaning "callers may omit this." Anywhere else (data models, config, store slices, types below the hook) it's an undefined leak: replace it with `T | null` or a concrete value.

```ts
// ❌ BAD
interface Service {
  name?: string;
  timeoutMs?: number;
}
// ✅ GOOD
interface Service {
  name: string | null;
  timeoutMs: number;
}
```

### B. No `any`, no `@ts-ignore`, no `as` casts

Never use `any` — it erases the contract this architecture enforces; use `unknown` and narrow with a type guard instead. Never suppress a type error with `@ts-ignore`/`@ts-expect-error` — fix the type. Avoid `as` casts; where one is unavoidable (a third-party boundary), write a typed guard function in a `.util.ts` and narrow through it — never `as any` / `as unknown as`.

### C. No non-null assertion (`!`)

`foo!.bar` still throws at runtime if the assumption is wrong. Handle the null branch explicitly, or prove the value can't be null with types.

```tsx
// ❌ BAD
const name = user!.name;
// ✅ GOOD
if (user === null) return null;
const name = user.name;
```

### D. Optional props get real defaults in the hook

`.hook.ts` must resolve every optional prop to a concrete value _before_ the view renders — `undefined` must never flow from a component into a UI primitive.

```tsx
// ❌ BAD — view forwards the optional prop untouched
<ParagraphText bold={props.bold}>{props.label}</ParagraphText>;

// ✅ GOOD — hook resolves defaults once
export function useUserCard({
  label,
  bold = false,
  dense = false,
}: UserCardProps) {
  return { label, isBold: bold, isDense: dense };
}
```

### E. Never spread the whole parent props object

Feature components pass **slices** of `Props` down, never `{...props}` — spreading leaks implementation fields into children and breaks the 1:1 nesting invariant (§3A). The hook decides which slices go where.

### F. Boolean names use `is`/`has`/`can`/`should`

`isLoading`, `hasError`, `canSubmit`, `shouldWarn` — not bare nouns (`loading`, `error`) whose negation reads ambiguously (`!error` vs `!hasError`).

### G. No magic values

Any string/number/threshold/enum-like literal used more than once belongs in a `.constant.ts` at the right scope (feature or global). Never inline `"sm"`, `0.5`, `400`, `"asc"`, or a hex color in hook or view logic — see the `CARD_PADDING_CLASS_MAP` example in §1B.

### H. Model state explicitly, not with boolean flags

Represent loading/success/empty/error as the `RequestState<T>` discriminated union (§4A) rather than combinations like `isLoading && !isError && data === undefined`. A single `status` field makes every branch exhaustive and type-checked. `.service.ts` return values and store slices (§1D) follow this same shape.

### I. Zero unused declarations

Remove unused imports, params, variables, and types before a file is done — dead declarations are stale types that mislead the next reader.

### J. Prop handlers are actions, not DOM events

Name handlers for what the caller does (`onSave`, `onDelete`, `onSelectUser`), never for the DOM event (`onClick`, `onSubmit`). They receive plain data (an id, a record, a value), not a `SyntheticEvent` — DOM wiring stays inside the hook.

### K. Zero UI Duplication (Single Source of Truth for Visuals)

Never create duplicate components or parallel visual primitives for the same concept (e.g. separate badges, status dots, or avatar pills across dropdowns and pages). Always scan `/components/**` first (§0B). If a primitive needs additional capabilities (new variants, sizes, or supported values), ask the user first before updating or creating, then update the canonical primitive at `/components/[module]/[name].ui.tsx` so all consumers share the same consistent design.

### L. Next.js Page & Router Boundary (SSR Only, Zero `className`, Strict Imports)

Next.js page and router components (`app/**/page.tsx`, `app/**/layout.tsx`, `app/**/loading.tsx`, `app/**/not-found.tsx`, `pages/**`) must be **Server-Side Rendered (Server Components — never `'use client'`)** and obey the exact same view rules as `.component.tsx`: **zero custom `className` or inline `style`**, and they may **only** import UI primitives from `/components/[module]/[name].ui.tsx`, structural containers from `/layouts/[category]/[name].layout.tsx`, and feature components exported by `features/[feature]/[feature].feature.ts` (§1E, §2). Never add `'use client'` to a page or route layout, and never deep-import internal feature files (`features/[feature]/components/**`) into a route file.

### M. Pre-Implementation Plan & File Tree Confirmation Gate

Never create or modify files blindly on an implementation request. Always scan existing project layers first, formulate the architectural decisions (layer placement, root vs. single-feature scope, UI primitive reuse vs. extension), present the annotated **Proposed File Tree (`[NEW]`, `[UPDATE]`, `[REUSE]`, `[PROMOTE]`)**, and ask the user to confirm that the plan is valid before writing code (§0).

---

## 5. Function Comments (Lean Doc Block)

Every non-trivial exported function gets exactly one comment block directly above it. The block has three labeled parts, in a fixed order, and **omits any part already obvious from the name and the TypeScript types**:

1. **what** — one imperative sentence stating what it does (always present).
2. **param** — only parameters whose meaning is not obvious from their name and type (omit if all are obvious).
3. **return** — output meaning, including `null`/empty and error policy (omit if obvious).

```ts
/**
 * <what: imperative one-liner>.
 *
 * param:  <only params that need explaining>
 *
 * return: <meaning, null/empty, error policy>
 */
```

Rules:

- **Hard ceiling of 5 lines.** If the block needs more, the function is doing too much — split it (§1F) instead of writing more comment.
- **Delete test**: if a line only restates the name and types (`param: user — the user`), remove it. Never document a parameter whose meaning matches its name and type.
- **Intent goes in `what`.** Fold the reason the function exists into the summary when it isn't obvious; never narrate the mechanics step by step.
- **Only exported, non-trivial functions.** Skip one-line getters and pass-through wrappers — a comment that restates the signature is noise, not documentation, the same instinct as §4I: a declaration that earns nothing stays out.
- **Never on `.component.tsx` or Next.js page/router views.** The JSX plus the paired hook's `what` line is the documentation for a view — per §2, a view's meaning should come from composition, not prose above it. If a view needs a comment to be understood, split it (§1F) instead of explaining it.
- **A section banner is not a function comment.** Existing `// ===== SECTION =====` separators group code; they do not replace the doc block on each function.
- **Do not restate the file suffix.** `.rule.ts`, `.geometry.ts`, `.service.ts` already say what kind of function it is — the comment states what this specific one does.
- **Function level only — never scribble comments on code lines.** The doc block lives in exactly one place: directly above the function declaration. Do **not** drop `//` comments on individual statements, branches, assignments, or expressions inside a function body. `// check if user is null`, `// loop through items`, `// increment counter`, `// return the result` are all noise — the code already states them, and each one risks drifting out of sync when the line changes. If a code line genuinely cannot be understood without prose, that is a signal to extract it into a named function/helper with its own doc block (or give it a descriptive name), not to annotate the line. The only permitted inline comment in a file is the single explanatory `//` above a non-obvious `.constant.ts` value (see below); everything else must be function-level.
- `.type.ts` and `.constant.ts` files don't use this block — a type or constant should be self-naming. If a constant's value needs explaining (why `400`, not `500`), add one plain `//` line above it instead.

### What each layer's block must not omit

| File                                                                                                        | The one thing the block must say                                  |
| ----------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| `.rule.ts`                                                                                                  | the condition it flags                                            |
| `.service.ts` / `.hook.ts`                                                                                  | the `RequestState<T>` shape returned and that it never throws     |
| `.geometry.ts` / `.util.ts`                                                                                 | the formula/invariant and any threshold                           |
| `.mapper.ts` / `.parser.ts` / `.format.ts` / `.export.ts` / `.selector.ts` / `.provider.ts` / `.factory.ts` | the transformation performed and any assumption about input shape |
| `.ui.tsx` / `.layout.tsx`                                                                                   | usually none — only comment a non-obvious prop                    |

### ❌ BAD — restates types, narrates the how, scribbles on code lines, runs long

```ts
/**
 * Gets the name.
 * @param user - the user
 * @returns the name
 */
export function getUserDisplayName(user: User | null): string {
  // check if user is null
  if (!user) return "";
  // check if a display name exists
  const nickname = pickNickname(user); // grab the nickname
  // fall back to the real name
  return nickname ?? user.name; // return result
}
```

Every `//` above is on a code line and adds nothing — remove them. The remaining prose still only restates the signature.

### ✅ GOOD — what, param, return; zero code-line comments

```ts
/**
 * Returns the display name for a user, preferring a saved nickname.
 *
 * param:  user — null means "no user selected".
 *
 * return: the display name, or "" when it cannot be resolved.
 */
export function getUserDisplayName(user: User | null): string {
  if (user === null) return "";
  const nickname = pickNickname(user);
  return nickname ?? user.name;
}
```

The body reads on its own: no `// check if null`, no `// grab the nickname`, no `// return result`. If a branch did need explaining, it would be pulled into its own named function with its own block — not annotated inline.

```ts
/**
 * Flags every account whose email is already used by a different account.
 *
 * param:  accounts — the full set to check, including the account being validated.
 *
 * return: one issue per duplicate email; [] when all emails are unique.
 */
export function runDuplicateEmailCheck(accounts: Account[]): ValidationIssue[] {
```

```ts
/**
 * Loads the user list for the admin table.
 *
 * return: RequestState<User[]> — never throws; failures land in `error` with status "error".
 */
export async function fetchUsers(): Promise<RequestState<User[]>> {
```
