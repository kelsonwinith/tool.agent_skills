# Growing Module Slicing Reference

Start with one focused file in any layer. When a component, hook, service, store, feature module, or utility accumulates independently changing responsibilities (multiple rule families, transformations, formats, factories, state domains, or UI subviews), split it into a named folder instead of letting one file become a navigation bottleneck.

## Table of Contents
1. [Entrypoint & Semantic Subfolder Invariant](#entrypoint--semantic-subfolder-invariant)
2. [Semantic File Suffixes](#semantic-file-suffixes)
3. [Directory Tree Examples (Root & Feature Scopes)](#directory-tree-examples-root--feature-scopes)
4. [Code Reference: Public Entrypoint + Semantic Child Files](#code-reference-public-entrypoint--semantic-child-files)

---

## Entrypoint & Semantic Subfolder Invariant

1. **Same Path Depth Entrypoint**: The folder keeps one explicit public entrypoint named after the domain (`utils/[utilName]/[utilName].util.ts`, `hooks/[hookName]/[hookName].hook.ts`).
2. **Public Contract**: The entrypoint holds the top-level implementation (or orchestrates the submodules) and re-exports the stable public API. External consumers **only** import the entrypoint, never the internal subfolder files.
3. **No Generic Filenames**: Never use `helper.ts`, `common.ts`, `part.ts`, `runName.ts`, or `index.ts`. Name internal files `[domainOrResponsibility].[suffix].ts` inside a plural semantic subfolder (`rules/`, `geometries/`, `factories/`, `exports/`, `selectors/`, `providers/`).
4. **Identical Rule at Root and Feature Scope**: Root shared slices live under `[project]/utils/[name]/` or `[project]/hooks/[name]/`; single-feature slices live under `features/[feature]/utils/[name]/` or `features/[feature]/hooks/[name]/`.

---

## Semantic File Suffixes

| Suffix | Subfolder | Purpose |
| :--- | :--- | :--- |
| `.rule.ts` | `rules/` | One validation, audit, or policy rule |
| `.factory.ts` | `factories/` | Object or domain-node construction |
| `.geometry.ts` | `geometries/` | Coordinate, size, bounds, grid, or collision calculations |
| `.mapper.ts` | `mappers/` | Transformation between data representations |
| `.parser.ts` | `parsers/` | Parsing and normalization from raw text or external payloads |
| `.format.ts` | `formats/` | Serialization or display formatting |
| `.export.ts` | `exports/` | A specific export target or transport (CSV, JSON, PDF) |
| `.slice.ts` | `slices/` | One state-management slice |
| `.selector.ts` | `selectors/` | One derived-state selector |
| `.provider.ts` | `providers/` | One external service/provider implementation |

---

## Directory Tree Examples (Root & Feature Scopes)

```text
# Root-scoped slices (shared by ≥2 features)
[project]/utils/requestPolicy/
├── requestPolicy.util.ts             # Public entrypoint: main implementation + re-exports
└── rules/
    ├── authentication.rule.ts
    ├── authorization.rule.ts
    └── rateLimit.rule.ts

[project]/utils/layoutModel/
├── layoutModel.util.ts               # Public entrypoint
└── geometries/
    ├── bounds.geometry.ts
    ├── collision.geometry.ts
    └── grid.geometry.ts

[project]/hooks/useSearch/
├── useSearch.hook.ts                 # Public entrypoint
└── selectors/
    ├── matchingItems.selector.ts
    └── groupedResults.selector.ts

# Feature-scoped slices (used by 1 feature only)
features/[feature]/utils/entityBuilder/
├── entityBuilder.util.ts             # Public entrypoint
└── factories/
    ├── user.factory.ts
    └── product.factory.ts

features/[feature]/utils/reportExport/
├── reportExport.util.ts              # Public entrypoint
└── exports/
    ├── csv.export.ts
    ├── json.export.ts
    └── pdf.export.ts

features/[feature]/services/payment/
├── payment.service.ts                # Public entrypoint
└── providers/
    ├── card.provider.ts
    └── wallet.provider.ts

features/[feature]/components/orderSummary/
├── orderSummary.component.tsx        # Parent component view
├── orderSummary.hook.ts
├── orderSummary.type.ts
└── components/                       # Level-1 private sub-components
    ├── orderLine/
    │   ├── orderLine.component.tsx
    │   ├── orderLine.hook.ts
    │   └── orderLine.type.ts
    └── totalsPanel/
        ├── totalsPanel.component.tsx
        ├── totalsPanel.hook.ts
        └── totalsPanel.type.ts
```

---

## Code Reference: Public Entrypoint + Semantic Child Files

```ts
// /utils/layoutModel/geometries/bounds.geometry.ts
import type { Rect, Point } from "@/types/geometry.type";

/**
 * Checks whether a point lies inside or on the boundary of `rect`.
 */
export function isPointWithinBounds(point: Point, rect: Rect): boolean {
  return (
    point.x >= rect.x &&
    point.x <= rect.x + rect.width &&
    point.y >= rect.y &&
    point.y <= rect.y + rect.height
  );
}
```

```ts
// /utils/layoutModel/geometries/grid.geometry.ts
import type { Point } from "@/types/geometry.type";

/**
 * Snaps a coordinate to the nearest multiple of `gridSize` (in px; must be > 0).
 */
export function snapPointToGrid(point: Point, gridSize: number): Point {
  return {
    x: Math.round(point.x / gridSize) * gridSize,
    y: Math.round(point.y / gridSize) * gridSize,
  };
}
```

```ts
// /utils/layoutModel/layoutModel.util.ts (Public Entrypoint)
import type { Point, Rect } from "@/types/geometry.type";
import { isPointWithinBounds } from "./geometries/bounds.geometry";
import { snapPointToGrid } from "./geometries/grid.geometry";

export { isPointWithinBounds, snapPointToGrid };

/**
 * Snaps `point` to `gridSize` and returns it only if the snapped position remains inside `canvas`.
 *
 * return: snapped Point when inside `canvas`; null when out of bounds.
 */
export function resolveValidGridPlacement(
  point: Point,
  gridSize: number,
  canvas: Rect
): Point | null {
  const snapped = snapPointToGrid(point, gridSize);
  return isPointWithinBounds(snapped, canvas) ? snapped : null;
}
```
