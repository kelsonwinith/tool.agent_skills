# Growing Module Slicing — Worked Examples

Companion reference for the **Growing Module Slicing** guidance in `SKILL.md`. Read this when a component, hook, service, store, feature module, or utility has accumulated independently changing responsibilities and you are deciding how to split it.

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

When a feature itself grows, the same rule applies at the feature level:

```text
features/editor/
├── editor.feature.ts
├── components/
├── hooks/
└── utils/
```
