# Core Architecture Layers & Next.js SSR Routes

Every UI and code file belongs to one layer with strict responsibilities, naming conventions, and import boundaries.

## Table of Contents
1. [A. UI System Components (`/components/[module]/[name].ui.tsx`)](#a-ui-system-components-componentsmodulenameuui-tsx)
2. [B. Layout Containers (`/layouts/[category]/[name].layout.tsx`)](#b-layout-containers-layoutscategorynamelayouttsx)
3. [C. App-Wide Shared Code (Root `/hooks`, `/types`, `/constants`, `/utils`)](#c-app-wide-shared-code-root-hooks-types-constants-utils)
4. [D. Feature Components (`features/[feature]/components/[name]/`)](#d-feature-components-featuresfeaturecomponentsname)
5. [E. Next.js Page & Router Components (`app/**/page.tsx`, `app/**/layout.tsx`, `pages/**`)](#e-nextjs-page--router-components-apppagetsx-applayouttsx-pages)
6. [The No-Inline-`className` Rule (BAD vs. GOOD Reference Code)](#the-no-inline-classname-rule-bad-vs-good-reference-code)

---

## A. UI System Components (`/components/[module]/[name].ui.tsx`)

Self-contained, presentational visual building blocks grouped by module (`button/`, `text/`, `input/`, `badge/`, `indicator/`).

- **Single Responsibility**: Exactly 1 file per component holding its `Props` interface, styling, and render. Zero feature/business logic. **This is the only layer (alongside `.layout.tsx`) where raw CSS/Tailwind classes live.**
- **Context-Neutral & Reusable**: Primitives are placement-agnostic. Never create placement-bound variations like `dropdownHttpBadge.ui.tsx` or `tableBadge.ui.tsx`. Pass sizing, variants, or slot props so the same primitive serves cards, dropdowns, tables, and modals.
- **Server-Renderable by Default**: Omit `'use client'` unless the primitive itself directly requires browser APIs that cannot be passed in as props/handlers.

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
  destructive = false,
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

---

## B. Layout Containers (`/layouts/[category]/[name].layout.tsx`)

Pure structural containers managing flex/grid geometry, spacing, alignment, padding, and borders.

- **Categorization**: Always group by structural purpose (`dashboard/`, `flex/`, `grid/`, `card/`, `dialog/`, `panel/`, `page/`). Never place layout files flat in `/layouts/`.
- **Single Responsibility**: Exactly 1 file per container. Accepts `children` or slot props. Zero domain logic, zero branding.
- **No Magic Values**: Variant-to-class lookup maps live in `/constants/layout.constant.ts`, never inline inside `.layout.tsx`.

```ts
// /constants/layout.constant.ts
export const CARD_PADDING_CLASS_MAP = {
  sm: "p-3",
  md: "p-4",
  lg: "p-6",
} as const;
```

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

---

## C. App-Wide Shared Code (Root `/hooks`, `/types`, `/constants`, `/utils`)

Cross-feature and app-wide code lives at the project root (`≥2 features` → root; `1 feature` → feature folder):

- **`/types/[name].type.ts`**: Shared data models, `RequestState<T>`, common unions (`user.type.ts`, `api.type.ts`).
- **`/constants/[name].constant.ts`**: Static configs, theme/style maps, route constants (`httpBadge.constant.ts`, `layout.constant.ts`).
- **`/hooks/[name].hook.ts`**: Hooks, store selectors, and effects reused by ≥2 features (`useMediaQuery.hook.ts`, `useDebouncedValue.hook.ts`).
- **`/utils/[name].util.ts`**: Pure, dependency-light helpers reused by ≥2 features (`formatDate.util.ts`, `slugify.util.ts`).
- **No Barrel Exports**: Always import root files by direct file path (`@/components/button/confirmButton.ui`, `@/utils/formatDate.util`), never via an `index.ts` barrel.
- **One-Way Imports**: Root files must **never** import from `features/`.

---

## D. Feature Components (`features/[feature]/components/[name]/`)

Domain orchestrators connecting business state/hooks to UI and Layout primitives.

```text
features/[feature]/
├── [feature].feature.ts                      # Public feature entrypoint (named exports only)
├── components/
│   └── [component_name]/                     # 1 folder per component
│       ├── [component_name].component.tsx    # Pure JSX view (default export, ZERO inline className)
│       ├── [component_name].hook.ts          # State, hooks, store selectors, resolved defaults, handlers
│       ├── [component_name].type.ts          # Props & component-specific types
│       ├── [component_name].constant.ts      # Static constants & labels (optional)
│       ├── [component_name].util.ts          # Pure calculation helpers (optional)
│       └── [component_name].service.ts       # Network & API calls returning RequestState<T> (optional)
├── hooks/                                    # Feature-wide hooks & store slices
├── types/                                    # Feature domain types
├── constants/                                # Feature-wide constants
└── utils/                                    # Feature-wide helpers
```

### Naming & Export Conventions
- **Filenames**: Always `camelCase` matching the module (`userCard.component.tsx`, `useUserCard.hook.ts`, `publicDatabaseAccess.rule.ts`).
- **Exports**:
  - `.component.tsx`, `.ui.tsx`, `.layout.tsx`: `default` export (`PascalCase`, e.g. `UserCard`).
  - `.hook.ts`, `.type.ts`, `.constant.ts`, `.util.ts`, `.service.ts`, `[feature].feature.ts`: named exports (`useUserCard`, `UserCardProps`, `CARD_PADDING_CLASS_MAP`).
  - Never use a generic `index.ts` for features; always use `[feature].feature.ts`.

### `'use client'` & `'use server'` Placement
- **Next.js `page.tsx` and `layout.tsx`**: Always Server-Side Rendered (Server Components) — **never** add `'use client'`.
- **`.ui.tsx` & `.layout.tsx`**: Server-renderable by default; only add `'use client'` if browser APIs cannot be lifted to the caller.
- **`.component.tsx`**: Add `'use client'` at the top of the file whenever its paired `.hook.ts` uses React state, effects, or browser APIs.
- **`.hook.ts`, `.util.ts`, `.type.ts`, `.constant.ts`**: Never add `'use client'` or `'use server'`.
- **`.service.ts`**: Add `'use server'` only when exposing a Next.js Server Action called directly from a client component.

---

## E. Next.js Page & Router Components (`app/**/page.tsx`, `app/**/layout.tsx`, `pages/**`)

Next.js route entrypoints (`page.tsx`, `layout.tsx`, `loading.tsx`, `not-found.tsx`, and Pages Router files) **must be Server-Side Rendered (SSR) and act like feature component views**:

1. **Always Server-Side Rendered (Server Component — NEVER `'use client'`)**:
   - Never place `'use client'` on `app/**/page.tsx` or `app/**/layout.tsx`. Keeping routes on the server preserves SSR HTML rendering, `async` server execution (awaiting `params`/`searchParams` or server data), Next.js `metadata` / `generateMetadata`, and lean client bundles.
   - Client interactivity (`useState`, `useEffect`, DOM handlers) lives inside feature `.component.tsx` + `.hook.ts` leaves imported via `[feature].feature.ts`.
2. **Zero Custom `className` or Inline `style`**:
   - Never write `<main className="p-6">`, `<div className="container mx-auto">`, or raw styled HTML tags inside `page.tsx` or `layout.tsx`.
3. **Strict Import Allowlist**:
   - `@/components/[module]/[name].ui` (`.ui.tsx` primitives)
   - `@/layouts/[category]/[name].layout` (`.layout.tsx` structural containers)
   - `@/features/[feature]/[feature].feature` (`[feature].feature.ts` public entrypoints)
   - ❌ **Never deep-import inside a feature** (e.g. never import `@/features/users/components/userCard/userCard.component` directly in `page.tsx`).

```ts
// /features/users/users.feature.ts
export { default as UserDirectory } from "./components/userDirectory/userDirectory.component";
export { default as UserInviteModal } from "./components/userInviteModal/userInviteModal.component";
```

```tsx
// /app/users/page.tsx (Server Component / SSR — NO "use client", ZERO className)
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

## The No-Inline-`className` Rule (BAD vs. GOOD Reference Code)

### ❌ BAD — Inline `className` in Feature Component & Client/Styled Next.js Page

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

### ✅ GOOD — Composing `.ui.tsx`, `.layout.tsx`, and `[feature].feature.ts`

```ts
// /features/users/components/userCard/userCard.type.ts
export interface User {
  id: string;
  name: string;
  role: string;
}

export interface UserCardProps {
  user: User;
  isBold?: boolean;
  onDeleteUser: (userId: string) => void;
}
```

```ts
// /features/users/components/userCard/userCard.hook.ts
import type { UserCardProps } from "./userCard.type";

/**
 * Resolves UserCard display defaults and binds the delete action to the current user ID.
 */
export function useUserCard({
  user,
  isBold = true,
  onDeleteUser,
}: UserCardProps) {
  const handleDelete = () => {
    onDeleteUser(user.id);
  };

  return {
    role: user.role,
    name: user.name,
    isBold,
    handleDelete,
  };
}
```

```tsx
// /features/users/components/userCard/userCard.component.tsx
"use client";
import type { UserCardProps } from "./userCard.type";
import { useUserCard } from "./userCard.hook";
import CardLayout from "@/layouts/card/cardLayout.layout";
import DimmedText from "@/components/text/dimmedText.ui";
import ParagraphText from "@/components/text/paragraphText.ui";
import ConfirmButton from "@/components/button/confirmButton.ui";

export default function UserCard(props: UserCardProps) {
  const { role, name, isBold, handleDelete } = useUserCard(props);
  return (
    <CardLayout>
      <DimmedText>{role}</DimmedText>
      <ParagraphText bold={isBold}>{name}</ParagraphText>
      <ConfirmButton label="Delete" destructive onConfirm={handleDelete} />
    </CardLayout>
  );
}
```

```tsx
// /app/users/page.tsx (SSR Server Component, zero className, imports only .layout, .ui, and .feature)
import PageLayout from "@/layouts/page/pageLayout.layout";
import HeadingText from "@/components/text/headingText.ui";
import { UserDirectory } from "@/features/users/users.feature";

export default async function UsersPage() {
  return (
    <PageLayout>
      <HeadingText>Users</HeadingText>
      <UserDirectory />
    </PageLayout>
  );
}
```
