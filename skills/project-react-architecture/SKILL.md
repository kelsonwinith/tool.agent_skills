---
name: project-react-architecture
description: "Use whenever building or editing ANY React/Next.js UI — cards, forms, dropdowns, dashboards, modals, buttons, tables — even if the user doesn't say 'component,' 'layout,' or name a file type. Also use when refactoring existing components, splitting a growing module into semantic submodules, or adding shared types/constants. Enforces: global UI primitives in `/components/[module]/[name].ui.tsx`, categorized layout containers in `/layouts/[category]/[name].layout.tsx`, app-wide types in `/types/[name].type.ts`, app-wide constants in `/constants/[name].constant.ts`, feature components in `features/[feature]/components/[name]/` with zero inline className styling, and a fixed @does/@flow/@returns/@edge comment block on every exported non-trivial function."
---

# Project React Architecture

Every UI and code element belongs to exactly one layer:

```text
├── /components/[module]/[name].ui.tsx     # Global UI System Primitives (ONLY place raw CSS lives)
├── /layouts/[category]/[name].layout.tsx  # Pure Structural Containers (categorized)
├── /types/[name].type.ts                  # App-wide Shared Types & Interfaces
├── /constants/[name].constant.ts          # App-wide Shared Constants & Config
└── /features/[feature]/                   # Domain Feature Modules
    ├── components/[name]/                 # 1 folder per component (ZERO inline className)
    ├── hooks/                             # Feature-scoped hooks & store slices
    ├── types/                             # Feature-scoped domain types
    ├── constants/                         # Feature-scoped constants
    ├── utils/                             # Feature-scoped helpers
    └── [feature].feature.ts               # Public feature entrypoint
```

## 0. Decision Checklist (read this first)

Before creating or touching any file, answer in order:

1. **Is it purely visual/presentational with no domain logic?** → `.ui.tsx` in `/components/[module]/` (§1A).
2. **Is it pure structure (flex/grid/spacing) with no visuals or logic?** → `.layout.tsx` in `/layouts/[category]/` (§1B).
3. **Does it connect business state/hooks to UI + Layout primitives?** → feature component in `features/[feature]/components/[name]/` (§1D).
4. **Is it a type, constant, or helper?** → Used by ≥2 features? Global (`/types`, `/constants`). Used by 1 feature only? Feature-scoped (`features/[feature]/types|constants|utils/`).
5. **Is it a sub-component used by exactly one parent?** → Nest it (§3), then re-check the promotion scale (§3B) the moment a second consumer appears.

If a file would mix two of these concerns (e.g. styling + business logic), split it — that split is the point of this architecture, not an edge case to work around.

---

## 1. Core Architecture Layers

### A. UI System Components (`/components/[module]/[name].ui.tsx`)

Self-contained, presentational visual building blocks grouped by module (button, text, input, badge).

- **Rule**: Exactly 1 file per component, holding its Props interface, styling, and render. No feature/business logic. This is the only layer where raw CSS/Tailwind classes live.
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

### C. App-Wide Shared Types & Constants

- **`/types/[name].type.ts`**: data models, shared interfaces, common unions used across ≥2 features (e.g. `layout.type.ts`, `user.type.ts`, `api.type.ts`).
- **`/constants/[name].constant.ts`**: static configs, theme maps, shared constants (e.g. `layout.constant.ts`, `routes.constant.ts`).
- **No barrel exports at this layer.** Unlike feature modules, `/components`, `/layouts`, `/types`, and `/constants` are always imported by their direct file path (e.g. `@/components/button/confirmButton.ui`), never through an `index.ts` re-export. A global barrel would force every consumer to pull in the whole layer's dependency graph and makes tree-shaking and promotion (§3B) harder to reason about.

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

- `.ui.tsx` and `.layout.tsx` files are presentational and should stay server-renderable by default — add `'use client'` only if the primitive itself needs browser APIs or interactivity that can't be lifted to the caller (rare; prefer passing handlers down instead).
- `.component.tsx` gets `'use client'` at the very top of the file whenever its `.hook.ts` uses state, effects, or browser-only APIs — which is the common case for feature components.
- `.hook.ts`, `.util.ts`, and `.type.ts` never declare `'use client'`/`'use server'` themselves; the directive belongs on the `.component.tsx` (or route file) that consumes them, not on every file in the chain.
- `.service.ts` gets `'use server'` only when it is a Server Action being called directly from a client component; plain fetch-based services making calls from the server need neither directive.

---

## 1E. Growing Module Slicing

Start with one focused file in any layer. When a component, hook, service, store, feature module, or utility accumulates independently changing responsibilities, split it into a named folder instead of allowing one file to become a navigation bottleneck. The split is justified when a file contains multiple rule families, transformations, formats, factories, state domains, UI subviews, or other responsibilities that developers need to find independently.

The folder keeps one explicit public entrypoint named after the domain. Internal implementations live in semantic subfolders whose suffix describes what each file does. This is not a `utils`-only rule:

```text
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

The public entrypoint re-exports the stable API. Consumers import the entrypoint, while sibling implementations import shared types/constants explicitly. Do not use generic names such as `helper.ts`, `common.ts`, `part.ts`, `runName.ts`, or `index.ts` to indicate that a file belongs to a larger module. Directory scope plus semantic suffix provides that relationship without hiding the implementation's responsibility.

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

## 2. The No-Inline-`className` Rule

`.component.tsx` files must contain **zero inline styles and zero `className` attributes**. All visual styling comes from composing UI System components (`/components/[module]/`) and Layout Containers (`/layouts/[category]/`).

### ❌ BAD — ad-hoc inline styling

```tsx
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

### ✅ GOOD — composing UI primitives and Layouts

```tsx
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

---

## 3. Sub-Components & Promotion Rules

### A. Strict Nesting Invariant (1:1 Parent Ownership)

A nested sub-component (`features/[feature]/components/[parent]/components/[child]/`) is **only** allowed if used exclusively by that one `[parent]`. No sibling, no other feature component, and no other layer may import it directly. Deep sibling imports (`../parentA/components/childB`) are forbidden.

### B. Promotion Scale

| Level | Scope & usage                             | Location                                                      |
| ----- | ----------------------------------------- | ------------------------------------------------------------- |
| **1** | Private to 1 parent                       | `features/[feature]/components/[parent]/components/[child]/`  |
| **2** | Used by ≥2 components in the same feature | `features/[feature]/components/[child]/`                      |
| **3** | Used across multiple features             | Global: `/components/`, `/layouts/`, `/types/`, `/constants/` |

**Promoting Level 1 → Level 2**: As soon as a Level-1 child is needed anywhere else in the same feature (e.g. `calendarDropdown`, nested under `yearDashboard`, is also needed by `monthDashboard`), move it up to `features/dashboard/components/calendarDropdown/`. Both parents then import it from the feature level — never from each other's nested folders.

**Promoting Level 2 → Level 3**: As soon as an element is needed across multiple features, move it to the matching global layer:

- Visual primitives/tokens → `/components/[module]/[name].ui.tsx`
- Structural containers → `/layouts/[category]/[name].layout.tsx`
- Shared data types → `/types/[name].type.ts`
- Shared constants/config → `/constants/[name].constant.ts`

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

- **Hard ceiling of 5 lines.** If the block needs more, the function is doing too much — split it (§1E) instead of writing more comment.
- **Delete test**: if a line only restates the name and types (`param: user — the user`), remove it. Never document a parameter whose meaning matches its name and type.
- **Intent goes in `what`.** Fold the reason the function exists into the summary when it isn't obvious; never narrate the mechanics step by step.
- **Only exported, non-trivial functions.** Skip one-line getters and pass-through wrappers — a comment that restates the signature is noise, not documentation, the same instinct as §4I: a declaration that earns nothing stays out.
- **Never on `.component.tsx` views.** The JSX plus the paired hook's `what` line is the documentation for a view — per §2, a view's meaning should come from composition, not prose above it. If a view needs a comment to be understood, split it (§1E) instead of explaining it.
- **A section banner is not a function comment.** Existing `// ===== SECTION =====` separators group code; they do not replace the doc block on each function.
- **Do not restate the file suffix.** `.rule.ts`, `.geometry.ts`, `.service.ts` already say what kind of function it is — the comment states what this specific one does.
- `.type.ts` and `.constant.ts` files don't use this block — a type or constant should be self-naming. If a constant's value needs explaining (why `400`, not `500`), add one plain `//` line above it instead.

### What each layer's block must not omit

| File                                                                                                        | The one thing the block must say                                  |
| ----------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| `.rule.ts`                                                                                                  | the condition it flags                                            |
| `.service.ts` / `.hook.ts`                                                                                  | the `RequestState<T>` shape returned and that it never throws     |
| `.geometry.ts` / `.util.ts`                                                                                 | the formula/invariant and any threshold                           |
| `.mapper.ts` / `.parser.ts` / `.format.ts` / `.export.ts` / `.selector.ts` / `.provider.ts` / `.factory.ts` | the transformation performed and any assumption about input shape |
| `.ui.tsx` / `.layout.tsx`                                                                                   | usually none — only comment a non-obvious prop                    |

### ❌ BAD — restates types, narrates the how, runs long

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
  ...
}
```

### ✅ GOOD — what, param, return

```ts
/**
 * Returns the display name for a user, preferring a saved nickname.
 *
 * param:  user — null means "no user selected".
 *
 * return: the display name, or "" when it cannot be resolved.
 */
export function getUserDisplayName(user: User | null): string {
```

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
