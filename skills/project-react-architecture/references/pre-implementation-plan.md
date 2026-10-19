# Pre-Implementation File Tree & Confirmation Gate

Whenever the user asks to add, build, update, or refactor any feature, component, or page (e.g. *"add X..."*, *"build a Y page..."*, *"refactor Z..."*), **do not jump straight to creating or editing files**, and **do not output long multi-section prose explanations**.

Keep the pre-implementation confirmation response strictly limited to **two sections only**:
1. `### Proposed File Tree` (with a brief inline `# [NEW] | [UPDATE] | [REUSE] | [PROMOTE] | [DELETE]` comment per file)
2. `### Confirmation` (numbered questions `1.`, `2.`, ... with lettered choices `a.`, `b.`, `c.`, ... where the recommended choice has `(Recommended)` and the **final choice is always `[last letter]. Type your own answer`**)

## Table of Contents
1. [Step 1: Internal Inventory Scan](#step-1-internal-inventory-scan)
2. [Step 2: Internal Layer & Scope Decision Matrix](#step-2-internal-layer--scope-decision-matrix)
3. [Step 3: Output Format — `### Proposed File Tree` & `### Confirmation` ONLY](#step-3-output-format--proposed-file-tree--confirmation-only)

---

## Step 1: Internal Inventory Scan

Before proposing a file tree, silently inspect the workspace:

1. **Global UI Primitives (`/components/**`)**: Check `/components/button/`, `/components/badge/`, `/components/text/`, `/components/input/`, `/components/indicator/` for existing `.ui.tsx` primitives.
2. **Global Layout Containers (`/layouts/**`)**: Check `/layouts/page/`, `/layouts/card/`, `/layouts/flex/`, `/layouts/grid/`, `/layouts/dialog/`, `/layouts/panel/` for structural wrappers.
3. **App-Wide Shared Layers (`/constants/**`, `/types/**`, `/hooks/**`, `/utils/**`)**: Check for existing shared constants, style maps, `RequestState<T>`, or utility helpers.
4. **Feature Modules (`features/**`) & Routes (`app/**` / `pages/**`)**: Check existing `[feature].feature.ts` entrypoints, route structures, and any duplicate or obsolete files that should be removed (`[DELETE]`).

---

## Step 2: Internal Layer & Scope Decision Matrix

Decide the placement and tag (`[NEW]`, `[UPDATE]`, `[REUSE]`, `[PROMOTE]`, `[DELETE]`) for every file:

| Question | Decision | Target Path & Tag |
| :--- | :--- | :--- |
| Does an exact `.ui.tsx` or `.layout.tsx` already exist? | Reuse as-is (zero duplication) | `[REUSE]` `/components/[module]/[name].ui.tsx` or `/layouts/[category]/[name].layout.tsx` |
| Does a partial `.ui.tsx` or `.layout.tsx` match exist (missing variant/size/method)? | Propose extending the existing primitive & its `.constant.ts` | `[UPDATE]` `/components/[module]/[name].ui.tsx` + `/constants/[name].constant.ts` |
| Is it a brand-new visual primitive (raw CSS/Tailwind, no domain logic)? | Create canonical placement-agnostic primitive at root | `[NEW]` `/components/[module]/[name].ui.tsx` |
| Is it pure structural geometry (flex/grid/spacing/border, no visuals or logic)? | Create categorized layout container at root | `[NEW]` `/layouts/[category]/[name].layout.tsx` |
| Is it a hook, type, constant, or helper used by **≥2 features** or app-wide? | Place at project root (or promote if previously in 1 feature, deleting old path) | `[NEW]` or `[PROMOTE]` `/hooks/`, `/types/`, `/constants/`, `/utils/` (and `[DELETE]` old feature-local path) |
| Is it a hook, type, constant, or helper used by **1 feature only**? | Keep inside the single feature module | `[NEW]` `features/[feature]/hooks\|types\|constants\|utils/` |
| Does it connect business state/hooks to `.ui.tsx` + `.layout.tsx` primitives? | Create a feature component folder (zero inline `className`) | `[NEW]` `features/[feature]/components/[name]/[name].{component.tsx,hook.ts,type.ts}` |
| Is it a sub-component used exclusively by **1 parent component**? | Nest under the parent component (Level 1) | `[NEW]` `features/[feature]/components/[parent]/components/[child]/` |
| Is it a Next.js route/page (`app/**/page.tsx`, `app/**/layout.tsx`)? | Keep as SSR Server Component (no `'use client'`), zero `className`, importing only `.ui.tsx`, `.layout.tsx`, and `[feature].feature.ts` | `[NEW]` or `[UPDATE]` `app/**/{page,layout}.tsx` |
| Is an existing file obsolete, duplicated, or replaced by promotion/slicing? | Remove the redundant or old file | `[DELETE]` path to obsolete/duplicate file |

---

## Step 3: Output Format — `### Proposed File Tree` & `### Confirmation` ONLY

**Do NOT include a separate "Architectural Decisions" prose section.** Output **only** `### Proposed File Tree` and `### Confirmation`.

### Strict Rules for `### Confirmation` (No Random or Filler Questions!)
- **Only ask clarifying questions when genuinely needed**:
  1. The user's prompt has a real functional/requirement ambiguity that cannot be inferred from the codebase, **OR**
  2. An existing shared file is being modified (`[UPDATE]`), moved (`[PROMOTE]`), or removed (`[DELETE]`) and requires user verification (e.g. extending an existing `/components/badge/httpBadge.ui.tsx` primitive).
- **NEVER ask random or filler architectural questions** about things already settled by the prompt or by these skill rules (for example, NEVER ask *"Should we export the components from `.feature.ts`?"*, *"Should the page be an SSR Server Component?"*, or *"Should we put styles in `.ui.tsx`?"* — those are mandatory architecture rules, not user questions!).
- **When the prompt is clear and no existing file modification needs verification**: `### Confirmation` contains **only a single question**: `1. Proceed with implementing this file tree?`.
- Format every question sequentially (`1.`, `2.`, ...) with lettered options (`a.`, `b.`, `c.`, ...), mark the recommended choice with `(Recommended)`, and **always make the final option `[last letter]. Type your own answer`**.

### Template A: When Extending/Deleting an Existing File or Clarifying an Ambiguity

```markdown
### Proposed File Tree

```text
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
            ├── dropdownHttpBadge/                         # [DELETE] Remove duplicate badge component
            └── methodDropdown/
                ├── methodDropdown.component.tsx           # [NEW] Pure JSX view (zero className)
                ├── methodDropdown.hook.ts                 # [NEW] Dropdown selection state & handlers
                └── methodDropdown.type.ts                 # [NEW] Props & dropdown types
```

### Confirmation

1. `httpBadge.ui.tsx` currently only supports `GET` and `POST`. How should we support `PUT`, `PATCH`, `DELETE`, and the compact dropdown badge size?
   a. Update `/components/badge/httpBadge.ui.tsx` and `/constants/httpBadge.constant.ts` with `PUT`/`PATCH`/`DELETE` and `size="sm"` (Recommended)
   b. Keep `httpBadge.ui.tsx` unchanged and create a separate badge component
   c. Type your own answer

2. Proceed with implementing this file tree?
   a. Yes, proceed with implementation (Recommended)
   b. Type your own answer
```

### Template B: When the Prompt Is Clear and No Existing Shared File Needs Verification

```markdown
### Proposed File Tree

```text
[project]/
├── app/users/
│   └── page.tsx                                           # [NEW] SSR Server Component page shell (zero className)
├── components/text/
│   └── headingText.ui.tsx                                 # [REUSE] Canonical heading primitive
├── layouts/page/
│   └── pageLayout.layout.tsx                              # [REUSE] Page structural wrapper
└── features/users/
    ├── users.feature.ts                                   # [NEW] Public feature entrypoint exporting UserDirectory & UserInviteModal
    └── components/
        ├── userDirectory/
        │   ├── userDirectory.component.tsx                # [NEW] Pure JSX view (zero className)
        │   ├── userDirectory.hook.ts                      # [NEW] Directory state & handlers
        │   └── userDirectory.type.ts                      # [NEW] Directory props & types
        └── userInviteModal/
            ├── userInviteModal.component.tsx              # [NEW] Pure JSX view (zero className)
            ├── userInviteModal.hook.ts                    # [NEW] Modal open/form state & handlers
            └── userInviteModal.type.ts                    # [NEW] Modal props & types
```

### Confirmation

1. Proceed with implementing this file tree?
   a. Yes, proceed with implementation (Recommended)
   b. Type your own answer
```
