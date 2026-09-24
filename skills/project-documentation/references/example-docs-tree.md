# Example `docs/` Tree

A complete, small example for an orders service. Use it as a target shape — not as content to copy verbatim.

```text
docs/
├── README.md
├── context/
│   ├── 001-ubiquitous-language.md
│   └── 001-context-map.md          # only for multi-context repos
├── product/
│   ├── 001-product-requirements.md
│   ├── 002-business-rules.md
│   └── 003-use-cases.md
├── architecture/
│   ├── 001-system-architecture.md
│   ├── 002-code-structure.md
│   ├── 003-data-model.md
│   └── 004-api-contracts.md
├── decisions/
│   └── 001-decisions.md            # ADR log
└── development/
    ├── 001-development-guide.md
    └── 002-testing.md
```

## What each file looks like

### `context/001-ubiquitous-language.md`

```markdown
# Orders Context

How orders are created, tracked, and cancelled.

## Language

| Term | Meaning | Avoid |
| :--- | :--- | :--- |
| Order | A request from a customer to buy one or more items. | Purchase, transaction |
| Customer | A person or organization that places orders. | Client, buyer, account |
```

### `product/002-business-rules.md`

```markdown
# Business Rules

**Document Version**: 1.0.0
**Status**: Active

- **BR-1**: An order can only be cancelled while its status is `placed` (`src/orders.js:11`).
- **BR-2**: Every order id is unique and prefixed `ord_` (`src/orders.js:6`).
```

### `architecture/003-data-model.md`

```markdown
# Data Model

**Document Version**: 1.0.0
**Status**: Active

| Field | Type | Notes |
| :--- | :--- | :--- |
| `id` | string | `ord_<n>`, unique |
| `customerId` | string | owner of the order |
| `items` | Item[] | at least one |
| `status` | `"placed" \| "cancelled"` | state machine |
```

### `decisions/001-decisions.md`

```markdown
# ADR-001: Store orders in memory

## Status
Accepted

## Context
The service is a prototype; durability is not required yet.

## Decision
Keep orders in an in-process `Map`.

## Consequences
- **Positive**: no external dependency.
- **Negative / Trade-offs**: state is lost on restart.
```

### `development/001-development-guide.md`

```markdown
# Development Guide

**Document Version**: 1.0.0
**Status**: Active

- **Run**: `node src/orders.js`
- **Test**: none configured yet (see `002-testing.md`)
```
