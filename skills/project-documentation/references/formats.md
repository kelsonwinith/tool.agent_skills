# Formats & Templates

Companion reference for `SKILL.md`. Read the relevant section when you are about to create or edit one of these artifacts.

## Contents

- [Canonical context glossary](#canonical-context-glossary)
- [Context map for multi-context repos](#context-map-for-multi-context-repos)
- [Structured Flow template](#structured-flow-template)
- [ADR template (one file per decision)](#adr-template-one-file-per-decision)
- [Terminology mismatch message](#terminology-mismatch-message)
- [Requirement mismatch message](#requirement-mismatch-message)

---

## Canonical context glossary

Single-context repositories: `docs/ubiquitous-language.md`
Multi-context repositories: `docs/context/<context-name>.md`

```markdown
# <Project / Context Name>

<One or two sentences on what this context is and why it exists.>

## Language

| Term | Meaning | Avoid |
| :--- | :--- | :--- |
| Order | A request from a customer to buy one or more items. | Purchase, transaction |
| Invoice | A request for payment sent to a customer after delivery. | Bill, payment request |
| Customer | A person or organization that places orders. | Client, buyer, account |
```

Definitions say what a term *is*, not what it does. Keep each to one or two sentences, and put every synonym in the `Avoid` column.

---

## Context map for multi-context repos

`docs/context/context-map.md`:

```markdown
# Context Map

## Contexts
- [Ordering](./ordering.md): receives and tracks customer orders
- [Billing](./billing.md): generates invoices and processes payments

## Relationships
- **Ordering → Billing**: Ordering emits `OrderPlaced`; Billing consumes it to invoice.
- **Ordering ↔ Billing**: shared `CustomerId` and `Money`.
```

---

## Structured Flow template

`docs/flows/<NNN>-<kebab-name>.md`:

```markdown
# [Flow Title]

**Document Version**: 0.1.0
**Status**: [Draft | Active]

## Overview & Actor
[Who triggers this flow and what outcome does it accomplish?]

## Business Rules
- [Rule 1]: [Requirement or validation]
- [Rule 2]: [State constraint or invariant]

## Flow Steps
1. [Step 1: User or system action]
2. [Step 2: Processing, state update, or event emission]
3. [Step 3: Response or completion]

## Edge Cases & Errors
- [Error condition 1]: [Behavior, response status, and fallback]
- [Error condition 2]: [Conflict resolution or retry policy]
```

---

## ADR template (one file per decision)

`docs/decisions/<NNN>-<kebab-name>.md`:

```markdown
# ADR-[NNN]: [Concise Title of Decision]

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
[Term]: [documented definition] — docs/ubiquitous-language.md

You used it to mean:
[the different meaning implied by the request]

Why it matters:
[how the two meanings lead to different behavior or requirements]

Code identifiers using the current term:
• [every file/symbol carrying the old name — variables, types, fields, routes]

Options:
• Keep the canonical term with its documented meaning
• Change the canonical definition (updates docs/ubiquitous-language.md and dependent docs)
• Rename the term (updates the glossary AND every code identifier listed above in the same change)
• Introduce a distinct term for the new concept
```

---

## Requirement mismatch message

Emit this, then ask for explicit confirmation:

```text
Current documented requirement:
[Quote or summarize the exact documented requirement and source file path, e.g. docs/product.md or docs/flows/<NNN>-<name>.md]

User requested:
[Summarize the requested change and what behavior it implies]

Difference:
[Explain precisely how the request contradicts or modifies existing rules]

Affected documents:
• docs/product.md
• docs/flows/<NNN>-<name>.md
• [every other document that encodes the affected requirement]

Potential impact:
[Explain implications on architecture, existing users, data integrity, or downstream features]
```
