# UI Primitive Reuse, Root vs. Feature Placement & Promotion Scale

## Table of Contents
1. [Shared Code Lives at the Project Root (Never Inside a Feature)](#shared-code-lives-at-the-project-root-never-inside-a-feature)
2. [Zero UI Duplication Protocol (Scan → Evaluate → Reuse / Update)](#zero-ui-duplication-protocol-scan--evaluate--reuse--update)
3. [Canonical Case Study: Shared HTTP Method Badge](#canonical-case-study-shared-http-method-badge)
4. [Sub-Component Nesting Invariant & 3-Level Promotion Scale](#sub-component-nesting-invariant--3-level-promotion-scale)

---

## Shared Code Lives at the Project Root (Never Inside a Feature)

If a `.type.ts`, `.constant.ts`, `.hook.ts`, `.util.ts`, `.layout.tsx`, or `.ui.tsx` is shared across features — or is genuinely app-wide — it belongs at the **`[project]` root**, never inside `features/[feature]/`. A feature may only own code that no other feature needs.

| Shared Element | Root Location | Consumer Rule |
| :--- | :--- | :--- |
| Presentational primitive (raw CSS) | `[project]/components/[module]/[name].ui.tsx` | Always global (never inside `features/`) |
| Structural container | `[project]/layouts/[category]/[name].layout.tsx` | Always global (never inside `features/`) |
| Hook (state, selectors, effects) | `[project]/hooks/[name].hook.ts` | ≥2 features / app-wide |
| Shared type / interface / union | `[project]/types/[name].type.ts` | ≥2 features / app-wide |
| Shared constant / config / map | `[project]/constants/[name].constant.ts` | ≥2 features / app-wide |
| Shared pure helper | `[project]/utils/[name].util.ts` | ≥2 features / app-wide |

### Core Invariants
- **A `.ui.tsx` or `.layout.tsx` never lives under a feature.** Features compose primitives; they do not own them.
- **Constants/helpers that even *look* reusable** (theme tokens, formatting, validation, route maps, display enums) go straight to the root.
- **Import direction is strictly one-way (`features/` → root, never root → `features/`).** If a shared root file needs feature data, pass it via parameters or props.
- **Root files import siblings by direct path** (`@/utils/formatDate.util`, `@/types/user.type`), never through an `index.ts` barrel.

---

## Zero UI Duplication Protocol (Scan → Evaluate → Reuse / Update)

A frequent architectural failure is recreating duplicate UI components for the same visual concept across different placements — for example, building an HTTP method badge for an endpoint detail card, a second HTTP badge for a dropdown selector, and a third inside an API log table.

Every recurring visual element must have **exactly one canonical UI primitive** in `[project]/components/[module]/`.

1. **Mandatory Inventory Scan**: Before creating any `.ui.tsx` or feature sub-component that renders badges, tags, buttons, inputs, or indicators, scan `[project]/components/**`, `/layouts/**`, and `/constants/**`.
2. **Evaluate**:
   - **Exact match**: Mark as `[REUSE]` in your `### Proposed File Tree` and reuse it directly.
   - **Partial match** (e.g. `httpBadge.ui.tsx` exists with `GET`/`POST`, but now needs `PUT`/`PATCH`/`DELETE` or `size="sm"` for a dropdown):
     - ❌ **NEVER** create a placement-specific duplicate (`dropdownHttpBadge.ui.tsx`, `endpointBadge.ui.tsx`, or inline markup).
     - ✅ **Mark as `[UPDATE]` in `### Proposed File Tree`** with a short comment describing the extension to the canonical primitive and its `.constant.ts` map.

---

## Canonical Case Study: Shared HTTP Method Badge

Instead of duplicating badges across dropdowns and detail cards, define one shared primitive backed by root constants:

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

Both features reuse the exact same primitive:

```tsx
// /features/apiDocs/components/endpointCard/endpointCard.component.tsx
import CardLayout from "@/layouts/card/cardLayout.layout";
import HttpBadge from "@/components/badge/httpBadge.ui";
import CodeText from "@/components/text/codeText.ui";
import type { EndpointCardProps } from "./endpointCard.type";

export default function EndpointCard({ method, path }: EndpointCardProps) {
  return (
    <CardLayout>
      <HttpBadge method={method} />
      <CodeText>{path}</CodeText>
    </CardLayout>
  );
}
```

```tsx
// /features/apiTester/components/methodDropdown/components/methodOption/methodOption.component.tsx
import FlexRowLayout from "@/layouts/flex/flexRow.layout";
import HttpBadge from "@/components/badge/httpBadge.ui";
import ParagraphText from "@/components/text/paragraphText.ui";
import type { MethodOptionProps } from "./methodOption.type";

export default function MethodOption({ method, label }: MethodOptionProps) {
  return (
    <FlexRowLayout>
      <HttpBadge method={method} size="sm" />
      <ParagraphText>{label}</ParagraphText>
    </FlexRowLayout>
  );
}
```

---

## Sub-Component Nesting Invariant & 3-Level Promotion Scale

### A. Strict Nesting Invariant (1:1 Parent Ownership)
A nested sub-component (`features/[feature]/components/[parent]/components/[child]/`) is **only** allowed if used exclusively by that single `[parent]`. No sibling, no other feature component, and no other layer may import it directly. Deep sibling imports (`../parentA/components/childB`) are forbidden.

### B. The 3-Level Promotion Scale

| Level | Scope & Usage | Canonical Location |
| :--- | :--- | :--- |
| **Level 1** | Private to **1 parent component** | `features/[feature]/components/[parent]/components/[child]/` |
| **Level 2** | Used by **≥2 components in the same feature** | `features/[feature]/components/[child]/` (or `features/[feature]/hooks\|types\|constants\|utils/`) |
| **Level 3** | Used across **≥2 features or app-wide** | Project root: `/components/`, `/layouts/`, `/hooks/`, `/types/`, `/constants/`, `/utils/` |

- **Promoting Level 1 → Level 2**: As soon as a Level-1 child (`calendarDropdown` nested under `yearDashboard`) is also needed by `monthDashboard` in the same feature, move it up to `features/dashboard/components/calendarDropdown/`.
- **Promoting Level 2 → Level 3**: As soon as a feature-scoped hook, util, type, constant, or component is needed by a second feature, **move** (never copy) it to the matching project root folder and update all imports in the same change.
