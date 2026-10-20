# Example `docs/` Tree

A complete, small example for an orders service showing flat singleton documents and numbered multi-item collections (`flows/` and `decisions/`).

```text
docs/
├── README.md
├── ubiquitous-language.md
├── product.md
├── architecture.md
├── development.md
├── flows/
│   ├── 001-create-order.md
│   └── 002-cancel-order.md
└── decisions/
    ├── 001-store-orders-in-memory.md
    └── 002-hexagonal-module-boundary.md
```

*(For multi-context repositories, `docs/ubiquitous-language.md` is replaced by unnumbered `docs/context/context-map.md` and `docs/context/<context-name>.md` files).*

---

## What each file looks like

### `docs/ubiquitous-language.md`

```markdown
# Orders Context

How orders are created, tracked, and cancelled.

## Language

| Term | Meaning | Avoid |
| :--- | :--- | :--- |
| Order | A request from a customer to buy one or more items. | Purchase, transaction |
| Customer | A person or organization that places orders. | Client, buyer, account |
```

### `docs/product.md`

```markdown
# Product Overview & Business Rules

**Document Version**: 1.0.0
**Status**: Active

## Overview
Self-service order management for verified customers.

## Personas
- **Buyer**: An authenticated user placing or cancelling orders.
- **Support Admin**: An internal operator reviewing order discrepancies.

## Global Business Rules
- **BR-1**: Every order identifier is unique and prefixed `ord_`.
- **BR-2**: Currency is stored in cents (`USD`).
```

### `docs/flows/001-create-order.md`

```markdown
# Create Order Flow

**Document Version**: 1.0.0
**Status**: Active

## Overview & Actor
Triggered by an authenticated Buyer checking out a cart with at least one item.

## Business Rules
- Cart must contain ≥ 1 item with available inventory.
- Total price must equal the sum of item prices plus tax.

## Flow Steps
1. Buyer submits checkout payload with item IDs and payment token.
2. System reserves inventory and creates an `Order` in `placed` status.
3. System emits `OrderPlaced` event and returns `201 Created` with the order summary.

## Edge Cases & Errors
- Insufficient inventory: aborts with `409 Conflict` and releases locks.
- Payment gateway timeout: marks order as `payment_pending` and triggers webhook polling.
```

### `docs/architecture.md`

```markdown
# System Architecture

**Document Version**: 1.0.0
**Status**: Active

## Code Structure
- `internal/modules/order`: Hexagonal domain, use cases, Fiber handlers, and GORM adapters.

## Data Model
| Field | Type | Notes |
| :--- | :--- | :--- |
| `id` | string | `ord_<uuid>`, primary key |
| `customerId` | string | Owner of the order |
| `status` | string | `placed \| cancelled \| completed` |

## API Contracts
- `POST /api/v1/orders` -> `201 Created`
- `POST /api/v1/orders/:id/cancel` -> `200 OK`
```

### `docs/decisions/001-store-orders-in-memory.md`

```markdown
# ADR-001: Store orders in memory for MVP

## Status
Accepted

## Context
The service is a rapid prototype; durability and relational persistence are not required yet.

## Decision
Keep orders in an in-process thread-safe map.

## Consequences
- **Positive**: Zero external database dependency during early developer onboarding.
- **Negative / Trade-offs**: State is lost on process restart; must migrate to PostgreSQL before production.
```

### `docs/development.md`

```markdown
# Development Guide

**Document Version**: 1.0.0
**Status**: Active

- **Run**: `go run cmd/main.go`
- **Lint**: `python scripts/docs_lint.py && golangci-lint run`
- **Test**: `go test ./...`
```
