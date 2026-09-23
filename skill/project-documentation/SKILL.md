---
name: project-documentation
description: "Portable, project-agnostic documentation guardian. Manages, inspects, and continuously synchronizes a project's product, business, architectural, and technical documentation under docs/. Use whenever developing, modifying, or refactoring features, changing requirements, business rules, APIs, data models, or architecture, or touching any code or workflow that may affect documented specifications. Enforces pre-implementation inspection, requirement-mismatch detection, user confirmation before requirement changes, multi-document consistency, and the numbered docs/<subfolder>/<NNN>-<name>.md convention. Works for any language, framework, or repo shape (single app or monorepo)."
---

# Project Documentation

A portable, project-agnostic tool for managing, inspecting, and continuously synchronizing a project's documentation with its code and requirements.

It contains **no project-specific facts**. Every fact it needs is discovered from the target project and written into that project's own `docs/` tree.

---

## 0. Scope & Output Contract

- **Artifact**: markdown documents under `docs/`, following the convention in §2.
- **Input**: the project's existing `docs/`, source code, configs, and the user's request.
- **No hardcoding**: never bake a specific project's services, stack, or paths into this skill. If a fact is project-specific, it belongs in `docs/` (or a project conventions doc), not here.
- **Portability**: works for any language, framework, package manager, or repository shape — single app, library, or monorepo.
- **Discover, don't assume**: on activation, read the actual `docs/` tree and repository to learn the project before writing anything.

---

## 1. Purpose & Core Philosophy

This skill acts as a **requirements-aware documentation guardian**. It ensures requirements, specifications, architecture, code, and tests never silently diverge.

### Priority Hierarchy
```text
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
1. **Never silently override or modify requirements**: If user instructions conflict with documented requirements, halt, explain the conflict, and obtain explicit user confirmation before touching code or documentation.
2. **Never implement before inspecting documentation**: Always read the relevant documents under `docs/` before implementing any feature, change, or refactoring.
3. **Documentation reflects reality**: Document only approved, implemented, or explicitly marked "planned" features. Never document unverified assumptions as facts.
4. **Keep documentation synchronized**: Treat the documents as an interconnected graph (§4). A change in one layer propagates downstream through the affected files only.
5. **Follow the numbered folder convention**: Every document lives at `docs/<subfolder>/<NNN>-<kebab-name>.md` (§2). Never create ad-hoc files directly under `docs/`.
6. **Keep this skill generic**: Project-specific conventions belong in the project's `docs/`, never in this skill file.

---

## 2. Documentation Architecture

Documents are organized into **semantic subfolders**, and each file is prefixed with a **zero-padded running number** unique within its subfolder.

### 2.1 Naming Convention

```text
docs/<subfolder>/<NNN>-<kebab-case-name>.md
```

- `<subfolder>` — a registered subfolder (§2.2).
- `<NNN>` — 3-digit running number, starting at `001`, unique **within its subfolder**.
- `<kebab-case-name>` — lowercase, hyphen-separated, no spaces (e.g. `002-business-rules.md`).

### 2.2 Default Subfolders

Adapt or extend per project, but these four cover most software projects:

| Subfolder | Scope | Typical documents |
| :--- | :--- | :--- |
| `product/` | Product requirements & domain behavior | PRD, business rules, use cases |
| `architecture/` | System design & technical contracts | Architecture, code structure, data model, API contracts |
| `decisions/` | Decision history | Architecture Decision Records |
| `development/` | How to build, verify, and contribute | Development guide, testing, conventions |

> Adding a subfolder is an explicit decision: register it in the project's docs index (§2.5), then create documents using §2.1.

### 2.3 Document Type Catalog

Map each concern to a document. Reuse an existing equivalent instead of creating a parallel file.

| Concern | Core Responsibilities & Contents |
| :--- | :--- |
| **Product requirements** | Product vision, problem statements, personas. Scope boundaries, functional/non-functional requirements, feature list, out-of-scope items. |
| **Business rules** | Testable business logic and validation rules. Domain constraints, invariants, state transitions, role permissions, domain calculations. |
| **Use cases** | Actors, preconditions, triggers, postconditions. Main success / alternate / error flows and expected user outcomes. |
| **System architecture** | High-level system design, service/module boundaries, component interactions, dependency graph, protocols, diagrams. |
| **Code structure** | Repository layout, directory responsibilities, module anatomy, layering, naming/import rules, placement rules for new code. |
| **Data model** | Entities, attributes, types, keys, relationships, indexes, ownership, lifecycles, persistence invariants, ER diagrams. |
| **API contracts** | Routes/endpoints, methods, request/response payloads, schemas, validation, error codes, auth/authz, rate limiting. |
| **Decision records** | Significant architectural/technical decisions as ADR entries (§5). |
| **Development guide** | Prerequisites, environment setup, commands, debugging, contribution workflow, local tooling. |
| **Testing** | Test strategy, current verification pipeline, test matrix, fixtures, coverage expectations, roadmap. |
| **Project conventions** | App/framework-specific rules that don't fit the above (e.g. state-management patterns, framework gotchas). Keep these in `docs/`, never in this skill. |

### 2.4 Document Header & Versioning

Every document opens with a header block:

```markdown
# <Title>

**Document Version**: X.Y.Z
**Status**: Draft | Active | Deprecated
```

Bump the version on every material edit; mark superseded docs `Deprecated` rather than deleting them.

### 2.5 Docs Index (optional but recommended)

Maintain a `docs/README.md` (the one allowed file at the `docs/` root) as a human-readable index listing each subfolder and its documents. If absent, discover the registry by listing the `docs/` tree — the numbered filenames are self-describing.

### 2.6 Adding, Splitting & Renumbering

- **Adding a document**: allocate the next free number in the target subfolder (e.g. after `004` comes `005-...`), create it, and add it to the docs index.
- **Splitting an oversized document**: never grow one file indefinitely. Allocate a new number, move the relevant sections into the new file, and leave a short pointer link in the original.
- **Numbers are stable identifiers**: do not renumber existing files to close gaps, so links and history stay valid. Renumbering requires an explicit decision, a full cross-reference sweep, and an ADR entry.
- **Cross-references**: always link using the full path (`docs/architecture/002-code-structure.md`) so references survive navigation.
- **Reuse over duplication**: if an equivalent document already exists, update it instead of creating a parallel file.

---

## 3. Workflow: Pre-Implementation Inspection & Mismatch Detection

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

### Requirement Mismatch Detection Format
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

### When the User Explicitly Changes a Requirement
If the user explicitly states an intention to change a business rule or requirement:
1. Analyze all downstream impacts across the affected documents (§4).
2. Outline the exact changes that will be applied to documentation and code.
3. Confirm the scope with the user.
4. Update the affected documents before or alongside code implementation.

---

## 4. Documentation Synchronization Graph

Documentation is an interconnected system. Changes cascade downstream; update only the affected nodes.

```text
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
- **Targeted Updates**: update only the specific documents affected by the change. Avoid churn across unrelated documents.
- **Cross-Document Consistency**: ensure terminology, entity names, status values, and logic match identically across all documents.
- **Preserve Existing Context**: when updating a document, preserve unrelated sections, notes, and context.
- **Registry Integrity**: any document added, split, or removed must be reflected in the docs index.

---

## 5. Standard ADR Template

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

> **Rule**: Do not create ADRs for trivial implementation details (naming a variable, helper refactoring).
> **Note**: ADR IDs are globally sequential (`ADR-001`, `ADR-002`, ...). The containing file keeps its stable numbered path; if the log grows large, split it into additional numbered files under the decisions subfolder.

---

## 6. Implementation & Verification Lifecycle

### Phase 1: Pre-Implementation
- [ ] Read all relevant documents under `docs/`.
- [ ] Verify the request is compatible with current specifications.
- [ ] If conflicting, halt and obtain explicit confirmation using the §3 mismatch template.

### Phase 2: Implementation
- [ ] Adhere to the documented architecture and code structure.
- [ ] Maintain documented business rules and invariants.
- [ ] Follow the project's documented conventions (including any `development/` conventions doc).
- [ ] If implementation reveals edge cases or documentation gaps, pause and clarify before assuming behavior.

### Phase 3: Post-Implementation Verification & Sync
- [ ] Run the project's documented build/lint/test commands (from the development guide / testing doc).
- [ ] Review each affected document for consistency with the change.
- [ ] Record any significant decision as an ADR.
- [ ] Update the docs index if documents were added, split, or removed.

---

## 7. Initial Project Setup (Bootstrapping)

When activated in a project lacking documentation:
1. **Inspect the codebase**: explore repository layout, packages, build configs, source, data models, routes, and tests.
2. **Create the folder structure**: the default subfolders (§2.2), adapted to the project.
3. **Create the standard documents** using the §2.1 naming convention and the §2.4 header.
4. **Document verified facts**: write only what can be definitively verified from the codebase.
5. **Mark unknowns**: flag unconfirmed requirements with `<!-- TODO: Clarify with product owner -->` rather than hallucinating.
6. **Prompt the user**: clarify missing high-level requirements, personas, or business rules.

### Numbering Discipline
- Numbers are allocated per subfolder: `001`, `002`, `003`, ...
- To add a file, take the next free number in the subfolder; never reuse a retired number.
- To split a file, allocate the next number and move sections out; never let a single document grow unbounded.
- Update the docs index and all cross-references in the same change.

---

## 8. Extending for a Specific Project

This skill stays generic. Project-specific rules are added **as documents**, not as edits to this skill:

- Framework/stack gotchas, state-management patterns, module conventions, and verification steps → a `development/` conventions document (e.g. `docs/development/003-<area>-conventions.md`).
- Repository/service topology → the code-structure and architecture documents.
- The docs index (`docs/README.md`) lists everything so any agent can discover the project's conventions by reading `docs/`.

If a project needs rules that this generic workflow cannot express, write them into `docs/` and reference them from the project's agent entry point (e.g. `AGENTS.md`) — never fork this skill.
