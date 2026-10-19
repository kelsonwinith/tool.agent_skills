# Pre-Implementation Decision & File Tree Confirmation Protocol

Whenever the user asks to add, build, update, or refactor any feature, component, or page (e.g. *"add X..."*, *"build a Y page..."*, *"refactor Z..."*), **do not jump straight to creating or editing files**. Follow the **Scan → Decide → Propose Tree & Confirm** protocol first.

## Table of Contents
1. [Step 1: Mandatory Inventory Scan](#step-1-mandatory-inventory-scan)
2. [Step 2: Layer & Scope Decision Matrix](#step-2-layer--scope-decision-matrix)
3. [Step 3: Architecture Plan & Annotated File Tree Template](#step-3-architecture-plan--annotated-file-tree-template)
4. [Scenario Templates (Partial UI Match & Promotion)](#scenario-templates-partial-ui-match--promotion)

---

## Step 1: Mandatory Inventory Scan

Before proposing a file tree or writing any code, inspect the existing workspace:

1. **Global UI Primitives (`/components/**`)**: Check `/components/button/`, `/components/badge/`, `/components/text/`, `/components/input/`, `/components/indicator/`, etc. for existing `.ui.tsx` files that already solve or partially solve the visual requirement.
2. **Global Layout Containers (`/layouts/**`)**: Check `/layouts/page/`, `/layouts/card/`, `/layouts/flex/`, `/layouts/grid/`, `/layouts/dialog/`, `/layouts/panel/` for structural wrappers.
3. **App-Wide Shared Layers (`/constants/**`, `/types/**`, `/hooks/**`, `/utils/**`)**: Check for existing shared constants, style maps, `RequestState<T>`, or utility helpers.
4. **Feature Modules (`features/**`) & Routes (`app/**` / `pages/**`)**: Check existing feature entrypoints (`[feature].feature.ts`) and route structures.

---

## Step 2: Layer & Scope Decision Matrix

Evaluate every element required by the user's prompt using this decision matrix:

| Question | Decision | Target Path & Tag |
| :--- | :--- | :--- |
| Does an exact `.ui.tsx` or `.layout.tsx` already exist? | Reuse as-is (zero duplication) | `[REUSE]` `/components/[module]/[name].ui.tsx` or `/layouts/[category]/[name].layout.tsx` |
| Does a partial `.ui.tsx` or `.layout.tsx` match exist (missing variant/size/method)? | Propose extending the existing primitive & its `.constant.ts` | `[UPDATE]` `/components/[module]/[name].ui.tsx` + `/constants/[name].constant.ts` |
| Is it a brand-new visual primitive (raw CSS/Tailwind, no domain logic)? | Create canonical placement-agnostic primitive at root | `[NEW]` `/components/[module]/[name].ui.tsx` |
| Is it pure structural geometry (flex/grid/spacing/border, no visuals or logic)? | Create categorized layout container at root | `[NEW]` `/layouts/[category]/[name].layout.tsx` |
| Is it a hook, type, constant, or helper used by **≥2 features** or app-wide? | Place at project root (or promote if previously in 1 feature) | `[NEW]` or `[PROMOTE]` `/hooks/`, `/types/`, `/constants/`, `/utils/` |
| Is it a hook, type, constant, or helper used by **1 feature only**? | Keep inside the single feature module | `[NEW]` `features/[feature]/hooks\|types\|constants\|utils/` |
| Does it connect business state/hooks to `.ui.tsx` + `.layout.tsx` primitives? | Create a feature component folder (zero inline `className`) | `[NEW]` `features/[feature]/components/[name]/[name].{component.tsx,hook.ts,type.ts}` |
| Is it a sub-component used exclusively by **1 parent component**? | Nest under the parent component (Level 1) | `[NEW]` `features/[feature]/components/[parent]/components/[child]/` |
| Is it a Next.js route/page (`app/**/page.tsx`, `app/**/layout.tsx`)? | Keep as SSR Server Component (no `'use client'`), zero `className`, importing only `.ui.tsx`, `.layout.tsx`, and `[feature].feature.ts` | `[NEW]` or `[UPDATE]` `app/**/{page,layout}.tsx` |

---

## Step 3: Architecture Plan & Annotated File Tree Template

Before touching any code (unless the user explicitly says *"skip confirmation"* or *"just implement it"*), present this 3-part plan and wait for confirmation:

1. **Architectural Decisions**: Explain *why* each item is placed in its layer, what is reused (`[REUSE]`), what is updated (`[UPDATE]`), what is promoted (`[PROMOTE]`), and how SSR/import boundaries are maintained.
2. **Proposed File Tree**: An ASCII directory tree of every file to be created, modified, promoted, or reused, annotated with `[NEW]`, `[UPDATE]`, `[REUSE]`, or `[PROMOTE]`.
3. **Confirmation Question**: Ask the user to confirm that the plan and file tree are valid before writing code.

### Example Output to User

```markdown
### 1. Architectural Decisions
- **UI Primitives & Layouts**:
  - `[REUSE]` `/layouts/page/pageLayout.layout.tsx` & `/layouts/card/cardLayout.layout.tsx` for page and card framing.
  - `[UPDATE]` `/components/badge/httpBadge.ui.tsx` & `/constants/httpBadge.constant.ts` — extend with `PUT`, `PATCH`, `DELETE` and `size="sm"` so both the endpoint card and dropdown selector reuse one canonical primitive.
- **Shared vs. Feature Scope**:
  - `httpBadge.constant.ts` lives at project root `/constants/` because it is shared across `apiDocs` and `apiTester` (≥2 features).
  - `methodDropdown` is specific to `apiTester`, so its `.component.tsx`, `.hook.ts`, and `.type.ts` live under `features/apiTester/components/methodDropdown/` and are exported via `apiTester.feature.ts`.
- **Next.js SSR Page Boundary**:
  - `[NEW]` `/app/api-playground/page.tsx` is an SSR Server Component (no `'use client'`, zero `className`) importing only `.layout.tsx`, `.ui.tsx`, and `apiTester.feature.ts`.

### 2. Proposed File Tree
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
            └── methodDropdown/
                ├── methodDropdown.component.tsx           # [NEW] Pure JSX view (zero className)
                ├── methodDropdown.hook.ts                 # [NEW] Dropdown selection state & handlers
                └── methodDropdown.type.ts                 # [NEW] Props & dropdown types
```

Does this architecture plan and file tree look valid to proceed with implementation?
```

---

## Scenario Templates (Partial UI Match & Promotion)

### When an Existing UI Primitive Partially Matches
> "Found existing UI primitive at `[project]/components/badge/httpBadge.ui.tsx` supporting `GET` and `POST`. To support our method selector dropdown and API views with `PUT`, `PATCH`, and `DELETE` (and a compact `size="sm"`), I have marked `httpBadge.ui.tsx` and `/constants/httpBadge.constant.ts` as `[UPDATE]` in the file tree above rather than creating a duplicate badge component. Please confirm if extending `httpBadge.ui.tsx` is preferred."

### When Promoting a File Across Scopes (`[PROMOTE]`)
> "`formatCurrency.util.ts` currently lives in `features/checkout/utils/formatCurrency.util.ts`, and is now needed by `features/invoices/`. In the file tree above, it is marked `[PROMOTE]` to move to `[project]/utils/formatCurrency.util.ts` (and delete the feature-local copy) so both features import from the root layer. Please confirm before I apply the move."
