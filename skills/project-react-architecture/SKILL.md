---
name: project-react-architecture
description: "Use this whenever building or editing ANY React or Next.js UI — cards, forms, dropdowns, dashboards, modals, buttons, tables — even if the user doesn't say 'component,' 'layout,' or name a file type. Also use when refactoring components, splitting a growing module into semantic submodules, or adding shared types/constants. It enforces: global UI primitives in `/components/[module]/[name].ui.tsx`, categorized layout containers in `/layouts/[category]/[name].layout.tsx`, app-wide types in `/types/[name].type.ts`, app-wide constants in `/constants/[name].constant.ts`, feature components in `features/[feature]/components/[name]/` with zero inline className styling, and a lean what/param/return comment block on exported non-trivial functions."
license: MIT
metadata:
  version: 1.2.0
---

# Project React Architecture

This skill is about *where code lives and how it is composed* — not React runtime behavior, performance, or backend setup. It keeps a React/Next.js codebase navigable by giving every element one clear home.

## The core idea

Every piece of UI or code belongs to exactly one layer:

```text
components/[module]/[name].ui.tsx      visual primitives — the only place styling lives
layouts/[category]/[name].layout.tsx   structure only (flex/grid/spacing)
types/[name].type.ts                   shared data types (used by 2+ features)
constants/[name].constant.ts           shared config (used by 2+ features)
features/[feature]/                    one folder per feature
├── [feature].feature.ts               the feature's public entrypoint
├── components/[name]/                 a component = view + hook + types
└── hooks/  types/  constants/  utils/ feature-scoped pieces
```

If a file would mix two concerns — styling and logic, structure and data — that's the signal to split it, not an edge case to work around.

## Layers

**UI primitives** (`components/[module]/[name].ui.tsx`) are small, presentational, one component per file. This is the only layer that owns raw CSS/Tailwind classes. Keep business logic out of them.

**Layouts** (`layouts/[category]/[name].layout.tsx`) are pure structure — flex/grid, spacing, alignment, borders. Group them by purpose (`card/`, `flex/`, `grid/`, `page/`). No domain logic, no branding.

**Shared types and constants** (`types/`, `constants/`) exist only when used by two or more features; otherwise keep them inside the feature. Import them by direct path rather than through a barrel `index.ts` — a barrel drags a whole layer into every consumer and makes later promotion harder.

**Feature modules** (`features/[feature]/`) are the domain layer. A feature exposes one public entrypoint, `[feature].feature.ts` (named exports), and keeps everything else behind it. Each component is a folder:

```text
features/[feature]/components/[name]/
├── [name].component.tsx   pure JSX view (default export)
├── [name].hook.ts         state, handlers, resolved props
├── [name].type.ts         Props and component types
├── [name].constant.ts     optional
├── [name].util.ts         optional
└── [name].service.ts      optional — network calls, returns RequestState<T>
```

Filenames are camelCase; the component/function they export is PascalCase; types are PascalCase; constants are SCREAMING_SNAKE_CASE. Keep the pairing consistent within a file.

`'use client'` belongs on the `.component.tsx` (or route file) that needs it — not on every hook, type, or util in the chain.

## Keep views clean

Feature components should hold no inline styles and no `className`. They compose UI primitives and layouts instead. That's what keeps styling in one place and the view readable at a glance.

```tsx
// good: the view composes, it doesn't style
export default function UserCard(props: UserCardProps) {
  const { user, isDeleting, handleDelete } = useUserCard(props);
  return (
    <CardLayout>
      <DimmedText>{user.role}</DimmedText>
      <ParagraphText bold>{user.name}</ParagraphText>
      <DeleteButton isBusy={isDeleting} onDelete={handleDelete}>Delete</DeleteButton>
    </CardLayout>
  );
}
```

## When things grow

Start with one file. Split it into a named folder when it takes on several independently changing responsibilities — multiple rule families, formats, state domains, or subviews. Give the folder one entrypoint named after the domain, and name the inner files by what they do (`.rule.ts`, `.geometry.ts`, `.factory.ts`, `.selector.ts`, `.provider.ts`, ...). Avoid vague names like `helper.ts`, `common.ts`, or `index.ts` — they hide why a file exists. Worked layouts are in [references/module-slicing.md](references/module-slicing.md).

Promote code as its reach grows: private to one parent → nested under it; used by two components in a feature → feature level; used across features → a global layer (`components/`, `layouts/`, `types/`, `constants/`).

## Code hygiene

These keep a layered codebase from hiding bugs at the seams where layers meet:

- Prefer `null` over `undefined` for "no value". The `?` marker is fine on an outer Props interface, but it leaks `undefined` anywhere else.
- Avoid `any`, `@ts-ignore`, and non-null assertions (`!`) — narrow `unknown`, or handle the null branch explicitly.
- Model loading/success/empty/error as one `RequestState<T>` union instead of flags that drift out of sync.
- Put repeated literals and thresholds in a `.constant.ts`.
- Name boolean props `is`/`has`/`can`/`should`.
- Name handlers for the action (`onSave`, `onDeleteUser`), not the DOM event, and pass plain data rather than the event object.
- A UI primitive owns its accessibility (`type`, `aria-*`, focus and disabled states). Never hardcode user-facing text in a view — take it as a prop or from the i18n layer.

## Comments

A non-trivial exported function gets one short block: what it does, plus `param:`/`return:` only where the name and types don't already say it. Keep it to a few lines — if it needs more, the function is doing too much. Skip one-line getters, and don't comment `.component.tsx` views; the JSX plus the hook is the documentation.

## Scaffolding

`python scripts/new_feature.py <feature> [--component <name>]` creates the feature folder, entrypoint, and component/hook/type stubs, with names normalized for you. Fill the TODOs. A full worked example is in [references/example-feature-module.md](references/example-feature-module.md).
