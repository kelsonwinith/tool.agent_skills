---
name: project-documentation
description: "Portable, project-agnostic documentation guardian. Manages, inspects, and continuously synchronizes a project's canonical context (ubiquitous-language glossary), product, business, architectural, and technical documentation under docs/. Use whenever developing, modifying, or refactoring features, changing requirements, business rules, APIs, data models, or architecture, or touching any code or workflow that may affect documented specifications. Enforces pre-implementation inspection, terminology reconciliation against the canonical context, requirement-mismatch detection, user confirmation before requirement changes, multi-document consistency, and the numbered docs/<subfolder>/<NNN>-<name>.md convention. Works for any language, framework, or repo shape (single app or monorepo)."
---

# Project Documentation

A portable, project-agnostic tool for managing, inspecting, and continuously synchronizing a project's documentation with its code and requirements.

It contains **no project-specific facts**. Every fact it needs is discovered from the target project and written into that project's own `docs/` tree.

---

## 0. Scope & Output Contract

- **Artifact**: markdown documents under `docs/`, following the convention in §3. This includes the **canonical context** (the project's ubiquitous-language glossary, §2).
- **Input**: the project's existing `docs/`, source code, configs, and the user's request.
- **No hardcoding**: never bake a specific project's services, stack, or paths into this skill. If a fact is project-specific, it belongs in `docs/` (or a project conventions doc), not here.
- **Portability**: works for any language, framework, package manager, or repository shape — single app, library, or monorepo.
- **Discover, don't assume**: on activation, read the actual `docs/` tree and repository to learn the project before writing anything.
- **Terminology authority**: the canonical context (§2) defines what the project's terms mean. Never silently override it, and never guess a definition the glossary already fixes.

---

## 1. Purpose & Core Philosophy

This skill acts as a **requirements-aware documentation guardian**. It ensures language, requirements, specifications, architecture, code, and tests never silently diverge.

### Priority Hierarchy
```text
Canonical Context & Ubiquitous Language   (what the words mean)
    ↓
Requirements
    ↓
Business Rules
    ↓
System Design & Architecture
    ↓
Implementation (Code)
    ↓
Testing
```

### Core Invariants
1. **Speak the project's language**: before interpreting a request, resolve its domain terms against the canonical context (§2). If the user's wording conflicts with a documented definition, surface the conflict and reconcile it before proceeding.
2. **Never silently override or modify requirements**: If user instructions conflict with documented requirements, halt, explain the conflict, and obtain explicit user confirmation before touching code or documentation.
3. **Never implement before inspecting documentation**: Always read the relevant documents under `docs/` — starting with the canonical context — before implementing any feature, change, or refactoring.
4. **Documentation reflects reality**: Document only approved, implemented, or explicitly marked "planned" features. Never document unverified assumptions as facts.
5. **Keep documentation synchronized**: Treat the documents as an interconnected graph (§5). A change in one layer propagates downstream through the affected files only.
6. **Follow the numbered folder convention**: Every document lives at `docs/<subfolder>/<NNN>-<kebab-name>.md` (§3). Never create ad-hoc files directly under `docs/`.
7. **Keep this skill generic**: Project-specific conventions belong in the project's `docs/`, never in this skill file.

---

## 2. Canonical Context & Ubiquitous Language

The same concept is often called different things by different people — "account" vs "customer" vs "user", "order" vs "purchase" vs "transaction". Without one agreed definition, every human and every AI silently guesses, and the guess drifts from what the user actually meant. The result is code that implements the wrong concept and docs that describe three different ones.

The **canonical context** is the project's single source of truth for its language. It is a **glossary and nothing else**: what each project-specific term *is*, plus the words to avoid. It is **not** a spec, a scratch pad, or a home for implementation decisions. Every layer below it — requirements, business rules, architecture, code, tests — must speak this language.

### 2.1 What belongs here

- **Only terms specific to this project's domain.** General programming concepts (timeouts, error types, utility patterns) never belong, however heavily the project uses them. Before adding a term, ask: is this unique to *this* context, or a general programming concept? Only the former belongs.
- **One canonical term per concept.** When several words mean the same thing, pick the best one and list the rest under `_Avoid_`.
- **Definitions of what a thing IS**, in one or two sentences — not what it does, not how it is built.

### 2.2 Where it lives

Default location: `docs/context/001-ubiquitous-language.md` (the `context/` subfolder, §3.2). Create it **lazily** — the first time a term is actually resolved, not upfront. If a term is still unresolved, leave `<!-- TODO: confirm definition -->` rather than inventing one.

### 2.3 Format

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

Rules:
- **Be opinionated.** When multiple words exist for one concept, pick the best and list the others under `_Avoid_`.
- **Keep definitions tight.** One or two sentences max. Define what it IS.
- **Only project-specific terms.** General programming concepts are excluded even if used heavily.
- **Group terms under subheadings** when natural clusters emerge; a flat list is fine otherwise.

### 2.4 Multi-context repos

A single app usually has one `docs/context/001-ubiquitous-language.md`. If the repo holds multiple bounded contexts, keep **one glossary per context** and add a map at `docs/context/001-context-map.md` listing each context, where it lives, and how they relate:

```markdown
# Context Map

## Contexts
- [Ordering](./ordering/001-ubiquitous-language.md): receives and tracks customer orders
- [Billing](./billing/001-ubiquitous-language.md): generates invoices and processes payments

## Relationships
- **Ordering → Billing**: Ordering emits `OrderPlaced`; Billing consumes it to invoice.
- **Ordering ↔ Billing**: shared `CustomerId` and `Money`.
```

Infer which context the current topic belongs to; if unclear, ask.

### 2.5 Terminology reconciliation (the active discipline)

The glossary is not a one-time artifact — it is sharpened continuously while work happens. Apply this discipline on every task:

- **Challenge against the glossary.** When the user uses a term that conflicts with the canonical definition, call it out immediately: *"The glossary defines 'cancellation' as X, but you seem to mean Y. Which is it?"*
- **Sharpen fuzzy language.** When a term is vague or overloaded, propose a precise canonical term: *"You said 'account': do you mean the Customer or the User? Those are different things."*
- **Stress-test with concrete scenarios.** Invent edge-case scenarios that force precision about where one concept ends and another begins.
- **Cross-reference with code.** When the user states how something works, check the code. Surface contradictions: *"The code cancels entire Orders, but you just said partial cancellation is possible. Which is right?"*
- **Update the glossary inline.** The moment a term is resolved, edit `docs/context/001-ubiquitous-language.md`. Do not batch these up.
- **Never silently pick a definition.** If a term is missing, propose a definition, confirm it with the user, then record it — and propagate it to dependent documents (§5).

> **Note**: merely *reading* the canonical context for vocabulary is a habit any task should have. This section is for when you are *changing* the model, not just consuming it.

---

## 3. Documentation Architecture

Documents are organized into **semantic subfolders**, and each file is prefixed with a **zero-padded running number** unique within its subfolder.

### 3.1 Naming Convention

```text
docs/<subfolder>/<NNN>-<kebab-case-name>.md
```

- `<subfolder>` — a registered subfolder (§3.2).
- `<NNN>` — 3-digit running number, starting at `001`, unique **within its subfolder**.
- `<kebab-case-name>` — lowercase, hyphen-separated, no spaces (e.g. `002-business-rules.md`).

### 3.2 Default Subfolders

Adapt or extend per project, but these five cover most software projects:

| Subfolder | Scope | Typical documents |
| :--- | :--- | :--- |
| `context/` | Canonical language & domain vocabulary | Ubiquitous-language glossary, context map |
| `product/` | Product requirements & domain behavior | PRD, business rules, use cases |
| `architecture/` | System design & technical contracts | Architecture, code structure, data model, API contracts |
| `decisions/` | Decision history | Architecture Decision Records |
| `development/` | How to build, verify, and contribute | Development guide, testing, conventions |

> Adding a subfolder is an explicit decision: register it in the project's docs index (§3.5), then create documents using §3.1.

### 3.3 Document Type Catalog

Map each concern to a document. Reuse an existing equivalent instead of creating a parallel file.

| Concern | Core Responsibilities & Contents |
| :--- | :--- |
| **Ubiquitous language** | Canonical terms for the project's domain, each with a tight "what it IS" definition and an `_Avoid_` list of synonyms. The terminology authority for every other document. (§2) |
| **Context map** | For multi-context repos: the list of bounded contexts, where each glossary lives, and how the contexts relate. (§2.4) |
| **Product requirements** | Product vision, problem statements, personas. Scope boundaries, functional/non-functional requirements, feature list, out-of-scope items. |
| **Business rules** | Testable business logic and validation rules. Domain constraints, invariants, state transitions, role permissions, domain calculations. |
| **Use cases** | Actors, preconditions, triggers, postconditions. Main success / alternate / error flows and expected user outcomes. |
| **System architecture** | High-level system design, service/module boundaries, component interactions, dependency graph, protocols, diagrams. |
| **Code structure** | Repository layout, directory responsibilities, module anatomy, layering, naming/import rules, placement rules for new code. |
| **Data model** | Entities, attributes, types, keys, relationships, indexes, ownership, lifecycles, persistence invariants, ER diagrams. |
| **API contracts** | Routes/endpoints, methods, request/response payloads, schemas, validation, error codes, auth/authz, rate limiting. |
| **Decision records** | Significant architectural/technical decisions as ADR entries (§6). |
| **Development guide** | Prerequisites, environment setup, commands, debugging, contribution workflow, local tooling. |
| **Testing** | Test strategy, current verification pipeline, test matrix, fixtures, coverage expectations, roadmap. |
| **Project conventions** | App/framework-specific rules that don't fit the above (e.g. state-management patterns, framework gotchas). Keep these in `docs/`, never in this skill. |

### 3.4 Document Header & Versioning

Every document opens with a header block:

```markdown
# <Title>

**Document Version**: X.Y.Z
**Status**: Draft | Active | Deprecated
```

Bump the version on every material edit; mark superseded docs `Deprecated` rather than deleting them.

### 3.5 Docs Index (optional but recommended)

Maintain a `docs/README.md` (the one allowed file at the `docs/` root) as a human-readable index listing each subfolder and its documents, with the canonical context listed first. If absent, discover the registry by listing the `docs/` tree — the numbered filenames are self-describing.

### 3.6 Adding, Splitting & Renumbering

- **Adding a document**: allocate the next free number in the target subfolder (e.g. after `004` comes `005-...`), create it, and add it to the docs index.
- **Splitting an oversized document**: never grow one file indefinitely. Allocate a new number, move the relevant sections into the new file, and leave a short pointer link in the original.
- **Numbers are stable identifiers**: do not renumber existing files to close gaps, so links and history stay valid. Renumbering requires an explicit decision, a full cross-reference sweep, and an ADR entry.
- **Cross-references**: always link using the full path (`docs/architecture/002-code-structure.md`) so references survive navigation.
- **Reuse over duplication**: if an equivalent document already exists, update it instead of creating a parallel file.

---

## 4. Workflow: Pre-Implementation Inspection & Mismatch Detection

Whenever the user requests to:
- Add, modify, or remove a feature
- Change application behavior or UI flows
- Update business rules, validation, or permissions
- Change API contracts, routes, or payloads
- Alter data schemas, models, or state structures
- Refactor architecture or major parts of the codebase
- Modify testing strategy or test suites

**DO NOT immediately write or modify code.** Follow this decision flow:

```text
User Request
     ↓
Resolve Terminology Against the Canonical Context (§2)
     ↓
Inspect Relevant Docs in docs/
     ↓
Compare Request vs. Documented Requirements
     ↓
 ┌───────────────────────────────────────────────┐
 │                                               │
 [Compatible / New In-Scope Feature]     [Conflicting / Requirement Change]
 │                                               │
 ↓                                               ↓
Proceed with Implementation             Stop & Report Requirement Mismatch
                                                 ↓
                                        Present Mismatch Details to User
                                                 ↓
                                        Ask for Confirmation
                                                 ↓
                                        [User Confirms]
                                                 ↓
                                        Update Docs First → Implement Code & Tests
```

### 4.1 Terminology Check (do this first)

Before comparing the request to requirements, resolve its language against the canonical context (§2):

1. Map every domain term in the request to its canonical definition.
2. **Term undefined?** Propose a definition, confirm it with the user, and record it in `docs/context/001-ubiquitous-language.md` before relying on it.
3. **Term conflicts?** HALT and use the terminology-mismatch format below.

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

Then ask which the user intends, and update the glossary inline before proceeding.

### 4.2 Requirement Mismatch Detection

If a request conflicts with or alters existing documented requirements, HALT and output:

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

Then ask the user for confirmation:
> *"Do you want to update the documented requirement to match your request and proceed with implementation?"*

### 4.3 When the User Explicitly Changes a Requirement

If the user explicitly states an intention to change a business rule or requirement:
1. Analyze all downstream impacts across the affected documents (§5).
2. Outline the exact changes that will be applied to documentation and code.
3. Confirm the scope with the user.
4. Update the affected documents before or alongside code implementation.

---

## 5. Documentation Synchronization Graph

Documentation is an interconnected system. Changes cascade downstream; update only the affected nodes.

```text
Canonical Context & Ubiquitous Language
    ↓
Product Requirements
    ↓
Business Rules
    ↓
Use Cases
    ↓
System Architecture
    ↓
Decision Records
    ↓
API Contracts
    ↓
Data Model
    ↓
Code Structure
    ↓
Development Guide
    ↓
Testing
```

### Synchronization Rules
- **Language first**: if a term's definition changes, propagate it to every document that uses the term before touching code.
- **Targeted Updates**: update only the specific documents affected by the change. Avoid churn across unrelated documents.
- **Cross-Document Consistency**: ensure terminology, entity names, status values, and logic match identically across all documents.
- **Preserve Existing Context**: when updating a document, preserve unrelated sections, notes, and context.
- **Registry Integrity**: any document added, split, or removed must be reflected in the docs index.

---

## 6. Standard ADR Template

When a significant architectural or technical decision is made, append an entry to the decision-record document:

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

> **Gate**: only write an ADR when **all three** hold — (1) **hard to reverse**: changing your mind later is costly; (2) **surprising without context**: a future reader will wonder "why did they do it this way?"; (3) **a real trade-off**: genuine alternatives existed and one was chosen for specific reasons. If any is missing, skip the ADR — do not create ADRs for trivial implementation details (naming a variable, helper refactoring).
> **Note**: ADR IDs are globally sequential (`ADR-001`, `ADR-002`, ...). The containing file keeps its stable numbered path; if the log grows large, split it into additional numbered files under the decisions subfolder.

---

## 7. Implementation & Verification Lifecycle

### Phase 1: Pre-Implementation
- [ ] Resolve the request's domain terms against the canonical context (§4.1).
- [ ] Read all relevant documents under `docs/`, starting with the canonical context.
- [ ] Verify the request is compatible with current specifications.
- [ ] If terminology conflicts, halt and reconcile using the §4.1 format.
- [ ] If requirements conflict, halt and obtain explicit confirmation using the §4.2 template.

### Phase 2: Implementation
- [ ] Adhere to the documented architecture and code structure.
- [ ] Maintain documented business rules and invariants.
- [ ] Use canonical terms from the glossary in code, tests, and comments — never the `_Avoid_` synonyms.
- [ ] Follow the project's documented conventions (including any `development/` conventions doc).
- [ ] If implementation reveals edge cases or documentation gaps, pause and clarify before assuming behavior.

### Phase 3: Post-Implementation Verification & Sync
- [ ] Run the project's documented build/lint/test commands (from the development guide / testing doc).
- [ ] Review each affected document for consistency with the change.
- [ ] Update the canonical context if any term was sharpened or introduced.
- [ ] Record any significant decision as an ADR.
- [ ] Update the docs index if documents were added, split, or removed.

---

## 8. Initial Project Setup (Bootstrapping)

When activated in a project lacking documentation:
1. **Inspect the codebase**: explore repository layout, packages, build configs, source, data models, routes, and tests.
2. **Create the folder structure**: the default subfolders (§3.2), adapted to the project.
3. **Seed the canonical context**: extract the domain's recurring nouns and verbs into `docs/context/001-ubiquitous-language.md` (§2.3), using only verified, project-specific terms. Mark uncertain ones `<!-- TODO: confirm definition -->` rather than inventing.
4. **Create the standard documents** using the §3.1 naming convention and the §3.4 header.
5. **Document verified facts**: write only what can be definitively verified from the codebase.
6. **Mark unknowns**: flag unconfirmed requirements with `<!-- TODO: Clarify with product owner -->` rather than hallucinating.
7. **Prompt the user**: clarify missing high-level requirements, personas, business rules, or ambiguous term definitions.

### Numbering Discipline
- Numbers are allocated per subfolder: `001`, `002`, `003`, ...
- To add a file, take the next free number in the subfolder; never reuse a retired number.
- To split a file, allocate the next number and move sections out; never let a single document grow unbounded.
- Update the docs index and all cross-references in the same change.

---

## 9. Extending for a Specific Project

This skill stays generic. Project-specific rules are added **as documents**, not as edits to this skill:

- Framework/stack gotchas, state-management patterns, module conventions, and verification steps → a `development/` conventions document (e.g. `docs/development/003-<area>-conventions.md`).
- Repository/service topology → the code-structure and architecture documents.
- Project-specific vocabulary and domain terms → the canonical context (§2), never here.
- The docs index (`docs/README.md`) lists everything so any agent can discover the project's conventions by reading `docs/`.

If a project needs rules that this generic workflow cannot express, write them into `docs/` and reference them from the project's agent entry point (e.g. `AGENTS.md`) — never fork this skill.
