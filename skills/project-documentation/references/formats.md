# Formats & Templates

Companion reference for `SKILL.md`. Read the relevant section when you are about to create or edit one of these artifacts.

## Contents

- [Canonical context glossary](#canonical-context-glossary)
- [Context map for multi-context repos](#context-map-for-multi-context-repos)
- [ADR template](#adr-template)
- [Terminology mismatch message](#terminology-mismatch-message)
- [Requirement mismatch message](#requirement-mismatch-message)

---

## Canonical context glossary

`docs/context/001-ubiquitous-language.md`:

```markdown
# <Project / Context Name>

<One or two sentences on what this context is and why it exists.>

## Language

**Order**:
A request from a customer to buy one or more items.
_Avoid_: Purchase, transaction

**Invoice**:
A request for payment sent to a customer after delivery.
_Avoid_: Bill, payment request

**Customer**:
A person or organization that places orders.
_Avoid_: Client, buyer, account
```

---

## Context map for multi-context repos

`docs/context/001-context-map.md`:

```markdown
# Context Map

## Contexts
- [Ordering](./ordering/001-ubiquitous-language.md): receives and tracks customer orders
- [Billing](./billing/001-ubiquitous-language.md): generates invoices and processes payments

## Relationships
- **Ordering → Billing**: Ordering emits `OrderPlaced`; Billing consumes it to invoice.
- **Ordering ↔ Billing**: shared `CustomerId` and `Money`.
```

---

## ADR template

Append one block per decision to the decision-record document under `docs/decisions/`:

```markdown
# ADR-001: [Concise Title of Decision]

## Status
[Proposed | Accepted | Deprecated | Superseded by ADR-XXX]

## Context
[What problem are we solving? What are the constraints, requirements, and background?]

## Decision
[What is the change/choice being made? What technology, pattern, or architecture is selected?]

## Alternatives Considered
- **Option 1**: [Description and why it was rejected]
- **Option 2**: [Description and why it was rejected]

## Consequences
- **Positive**: [Benefits, simplifications, performance improvements]
- **Negative / Trade-offs**: [Complexity, migration cost, limitations]
```

---

## Terminology mismatch message

Emit this, then ask which meaning the user intends before proceeding:

```text
Canonical definition:
[Term]: [documented definition] — docs/context/001-ubiquitous-language.md

You used it to mean:
[the different meaning implied by the request]

Why it matters:
[how the two meanings lead to different behavior or requirements]

Options:
• Keep the canonical term with its documented meaning
• Change the canonical definition (updates docs/context/... and every dependent doc)
• Introduce a distinct term for the new concept
```

---

## Requirement mismatch message

Emit this, then ask for explicit confirmation:

```text
Current documented requirement:
[Quote or summarize the exact documented requirement and source file path]

User requested:
[Summarize the requested change and what behavior it implies]

Difference:
[Explain precisely how the request contradicts or modifies existing rules]

Affected documents:
• docs/<subfolder>/<NNN>-<name>.md
• [every other document that encodes the affected requirement]

Potential impact:
[Explain implications on architecture, existing users, data integrity, or downstream features]
```
