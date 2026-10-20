# Grill Mismatch & Summary Formats

Use these templates during `project-grill` whenever a terminology conflict, requirement conflict, or final Stage 1 summary is emitted.

## Contents

- [Terminology mismatch message](#terminology-mismatch-message)
- [Requirement mismatch message](#requirement-mismatch-message)
- [Agreed Design Summary (Stage 1 Gate)](#agreed-design-summary-stage-1-gate)

---

## Terminology mismatch message

Emit this when the request uses a word that conflicts with `docs/context/001-ubiquitous-language.md` or changes an existing term's meaning:

```text
Canonical definition:
[Term]: [documented definition] — docs/context/001-ubiquitous-language.md

You used it to mean:
[the different meaning or synonym implied by the request]

Why it matters:
[how the two meanings lead to different behavior, requirements, or code names]

Code identifiers using the current term:
• [every file/symbol carrying the old name — variables, types, fields, routes]

Options:
1. (Recommended) [Best-fit option below based on context]
2. Keep the canonical term with its documented meaning
3. Change the canonical definition (updates docs/context/... and every dependent doc)
4. Rename the term everywhere (updates the glossary AND every code identifier listed above in the same change)
5. Introduce a distinct term for the new concept
```

---

## Requirement mismatch message

Emit this when the request contradicts or changes an existing rule in `docs/product/`:

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

---

## Agreed Design Summary (Stage 1 Gate)

Output this summary once all grilling questions are answered and before moving to Stage 2 (`/project-documentation`):

```markdown
### Agreed Design Summary

- **Goal & Scope**: [1–3 bullets on what is being added, modified, or removed]
- **Canonical Terminology (`docs/context/001-ubiquitous-language.md`)**:
  - [New / Updated / Renamed terms, plus any code identifiers to rename, or "No changes"]
- **Requirements & Business Rules (`docs/product/`)**:
  - [Key rules, validations, edge cases, and pruned rules for removed features]
- **Architecture & ADR Check (`docs/architecture/` & `docs/decisions/`)**:
  - [Affected architectural contracts/models; whether an ADR will be recorded and why]
```
