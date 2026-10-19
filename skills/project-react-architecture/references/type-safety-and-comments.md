# Code Hygiene, Type-Safety & Function Comments Reference

## Table of Contents
1. [Code Hygiene & Type-Safety Rules (A–M)](#code-hygiene--type-safety-rules-am)
2. [Lean Function Doc Block Standard (`what` / `param` / `return`)](#lean-function-doc-block-standard-what--param--return)
3. [BAD vs. GOOD Function Comment Examples](#bad-vs-good-function-comment-examples)

---

## Code Hygiene & Type-Safety Rules (A–M)

### A. Never Declare `undefined` — Use `null` and `RequestState<T>`
`undefined` means "no explicit statement about why or when a value is missing." `null` is a deliberate, checkable absence.
- Replace `T | undefined` with `T | null` and initialize explicitly (`useState<User | null>(null)`).
- The `?` optional marker is **only** permitted on outer `Props` interfaces (meaning callers may omit the prop). Never use `?` on data models, configs, store slices, or internal types.

```ts
// /types/request.type.ts
export type RequestState<T> = {
  status: "idle" | "loading" | "success" | "error";
  data: T | null;
  error: string | null;
};
```

```ts
// ❌ BAD
let selectedId: string | undefined = undefined;
const [user, setUser] = useState<User | undefined>();
interface ServiceConfig {
  name?: string;
  timeoutMs?: number;
}

// ✅ GOOD
let selectedId: string | null = null;
const [user, setUser] = useState<User | null>(null);
interface ServiceConfig {
  name: string | null;
  timeoutMs: number;
}
```

### B. No `any`, No `@ts-ignore`, No `as` Casts
- Never use `any`; use `unknown` and narrow with a type guard in a `.util.ts`.
- Never suppress errors with `@ts-ignore` or `@ts-expect-error`.
- Never use `as any` or `as unknown as`.

### C. No Non-Null Assertion (`!`)
Handle the `null` branch explicitly instead of asserting `user!.name`.

```tsx
// ❌ BAD
const name = user!.name;

// ✅ GOOD
if (user === null) return null;
const name = user.name;
```

### D. Resolve Optional Props to Concrete Defaults in `.hook.ts`
`undefined` must never flow from a feature component into a `.ui.tsx` primitive.

```tsx
// ❌ BAD — view forwards optional prop untouched
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

### E. Never Spread Parent Props (`{...props}`)
Pass explicit slices down to children so implementation fields never leak across boundaries.

### F. Boolean Names Use `is` / `has` / `can` / `should`
Use `isLoading`, `hasError`, `canSubmit`, `shouldWarn` — never bare nouns (`loading`, `error`).

### G. No Magic Values
Extract any repeated literal, threshold, or enum-to-style lookup map into a `.constant.ts` at the appropriate scope (root `/constants/` or `features/[feature]/constants/`).

### H. Model Async & Store State Explicitly (`RequestState<T>`)
Every `.service.ts` function and store slice models `status: "idle" | "loading" | "success" | "error"` via `RequestState<T>` and **never throws past its boundary**.

```ts
// /features/users/components/userDirectory/userDirectory.service.ts
import type { RequestState } from "@/types/request.type";
import type { User } from "./userDirectory.type";

/**
 * Loads the active user directory list from the API.
 *
 * return: RequestState<User[]> — never throws; network/HTTP failures populate `error` with status "error".
 */
export async function fetchUsers(): Promise<RequestState<User[]>> {
  try {
    const response = await fetch("/api/users");
    if (!response.ok) {
      return { status: "error", data: null, error: `HTTP ${response.status}` };
    }
    const data: User[] = await response.json();
    return { status: "success", data, error: null };
  } catch (err) {
    const message = err instanceof Error ? err.message : "Unknown error";
    return { status: "error", data: null, error: message };
  }
}
```

### I. Zero Unused Declarations
Remove unused imports, parameters, variables, and types before finishing any file.

### J. Prop Handlers Are Domain Actions, Not DOM Events
Name handlers `onSave`, `onDeleteUser`, `onSelectMethod` (receiving plain domain values like `userId: string`), never `onClick` or `onSubmit` with `SyntheticEvent`. DOM event wiring stays inside `.hook.ts`.

### K. Zero UI Duplication
Always scan `/components/**` before creating UI; extend canonical primitives (after confirming with the user) instead of creating duplicate components.

### L. Next.js Page & Router Boundary
Next.js pages/layouts are always SSR Server Components (no `'use client'`), have zero custom `className`, and only import `.ui.tsx`, `.layout.tsx`, and `[feature].feature.ts`.

### M. Pre-Implementation File Tree Gate
Always output **only** `### Proposed File Tree` (`[NEW]`, `[UPDATE]`, `[REUSE]`, `[PROMOTE]`, `[DELETE]` + short inline comment) before writing code, with no extra prose sections or questionnaires.

---

## Lean Function Doc Block Standard (`what` / `param` / `return`)

Every non-trivial exported function carries one doc block directly above its declaration with up to three labeled parts in fixed order, **omitting any part already obvious from the function name and TypeScript types**:

```ts
/**
 * <what: imperative one-liner>.
 *
 * param:  <only params whose meaning/units/sentinel is not obvious from name + type>
 *
 * return: <output meaning, null/empty sentinel, and error policy>
 */
```

### Strict Comment Rules
1. **Hard ceiling of 5 content lines.** If a function needs more explanation, split it (`references/module-slicing.md`).
2. **Delete test**: Never write `param: user — the user`. If name + type already say it, omit `param:`.
3. **Never on `.component.tsx` or Next.js `page.tsx`/`layout.tsx` views.** Views are self-documenting through composition.
4. **Function-level only — ZERO inline `//` comments on code lines.** Never write `// check if null`, `// loop through items`, or `// return result` inside a function body. If a branch is non-obvious, extract it into a named helper with its own doc block. The only allowed `//` line is a single explanatory comment above a non-obvious `.constant.ts` value.

| File Suffix | What the Doc Block Must State |
| :--- | :--- |
| `.rule.ts` | The exact condition it flags |
| `.service.ts` / `.hook.ts` | The `RequestState<T>` or state/handler contract returned, and that it never throws |
| `.geometry.ts` / `.util.ts` | The formula/invariant and any threshold or unit |
| `.mapper.ts` / `.parser.ts` / `.format.ts` / `.export.ts` / `.selector.ts` / `.provider.ts` / `.factory.ts` | The transformation performed and any input assumptions |
| `.ui.tsx` / `.layout.tsx` | Usually none — only comment a non-obvious prop |

---

## BAD vs. GOOD Function Comment Examples

### ❌ BAD — Restates Types & Litters Code Lines with `//` Comments

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

### ✅ GOOD — Lean `what` / `param` / `return`, Zero Code-Line Comments

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
