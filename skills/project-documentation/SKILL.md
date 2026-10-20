---
name: project-documentation
description: "Stage 2 of the project workflow (/project-documentation): portable, project-agnostic documentation guardian. Manages and continuously synchronizes a project's canonical context (ubiquitous-language glossary), product, business, architectural, and technical documentation under docs/. Use whenever requirements, business rules, APIs, data models, architecture, or terminology change — or as Stage 2 after /project-grill. Treats each glossary term as the concept's canonical name in both docs and code (so renaming a term renames its code identifiers too), keeps every document describing the current system (removed features are pruned from docs), records ADRs for hard-to-reverse trade-offs, ships deterministic validators, and pauses for user approval when run in the workflow."
license: MIT
compatibility: "Requires Python 3 (standard library only) to run the bundled helpers in scripts/."
metadata:
  version: 1.5.0
---

# Project Documentation (Stage 2)

A project's docs and its code drift apart quietly. This skill keeps them honest: it manages the numbered `docs/` tree, enforces a single canonical vocabulary across docs and code, and validates every documentation change with deterministic linters.

It contains no project-specific facts — everything it needs is discovered from the project and written into that project's own `docs/`.

> **Pre-Implementation Grilling**: If the request has not been grilled yet (e.g. `/project-documentation` was invoked directly on an ambiguous request without running `/project-grill` first), run **`project-grill`** first so terminology conflicts, requirement mismatches, and open design questions are settled before editing `docs/`.

---

## Docs describe the current system, not its history

Documentation is a snapshot of what the system *is right now*, never a changelog. If a feature is removed or replaced, delete its documentation and every reference to it — don't leave a "removed" or "deprecated" section behind, and don't keep describing behavior that no longer exists. When code and docs disagree, the docs are wrong until updated.

The one deliberate exception is the ADR log under `decisions/`: it records *why* past choices were made, and is useful precisely because it is historical.

## The `docs/` tree

Documents live in semantic subfolders, numbered so they're easy to reference:

```text
docs/<subfolder>/<NNN>-<kebab-name>.md
```

Five subfolders cover most projects: `context/` (the canonical language), `product/`, `architecture/`, `decisions/`, and `development/`. Numbers are per-subfolder and stable — don't renumber to close gaps. A complete example is in [references/example-docs-tree.md](references/example-docs-tree.md).

Every document except the glossary and the ADR log opens with a header:

```markdown
# <Title>

**Document Version**: X.Y.Z
**Status**: Draft | Active
```

Keep `docs/README.md` as an index, with the canonical context listed first.

## The canonical context

Different people call the same thing different names — "account" vs "customer", "order" vs "purchase". Left alone, everyone guesses, and the guesses drift. So keep one glossary at `docs/context/001-ubiquitous-language.md` as a table of terms, what each one *means* (what it is, not what it does), and the words to avoid:

```markdown
| Term | Meaning | Avoid |
| :--- | :--- | :--- |
| Order | A request from a customer to buy one or more items. | Purchase, transaction |
| Customer | A person or organization that places orders. | Client, buyer, account |
```

Only project-specific terms belong here — not general programming concepts. One canonical term per concept; list every synonym in `Avoid`. When a term is resolved, write it down immediately. Multi-context repos keep one glossary per context plus a map (format in [references/formats.md](references/formats.md)).

### A glossary term is the same word in docs and code

The canonical term is not just prose vocabulary — it is the name that should appear in the codebase too. Variables, functions, types, DTO fields, API params, DB columns, and route segments all carry the same concept, so they should use the same canonical term. When docs say `Buyer` but code says `client`/`Client`/`clientId`, every reader has to translate between two vocabularies, and the drift is where bugs and misunderstandings hide.

- The glossary term is the single source of truth for a concept's name. Pick the canonical English term, then use it consistently across docs **and** code.
- Code identifiers follow the term, adjusted only for the language's casing convention — i.e. the term's own casing is not mutated beyond that. `Buyer` → `buyer`, `BuyerId`, `buyerId`, `useBuyer`, `fetchBuyers`; never `client`, `ClientId`, `customer`.
- If a concept already has a different name in code, the mismatch is a reconciliation task that must be carried into Stage 3 (`/project-plan`) and Stage 4 (`/project-implement`).

### When a term's meaning changes, rename it everywhere at once

A glossary term is a living definition: requirements change, and the word often changes with them. Treat a rename as a change in the canonical context that must propagate across both docs and code — never let a new name land in the glossary while the old name lingers in code, or new code while docs still describe the old concept.

Example — the requirement shifts so a `Client` is now called a `Buyer`:

1. Update `docs/context/001-ubiquitous-language.md`: rename the term to `Buyer`, rewrite its meaning, and move `Client` into the `Avoid` column.
2. Update every dependent document that mentioned the old term (requirements, business rules, architecture, data models).
3. Ensure every code identifier that carried `client` → `buyer` (`client` → `buyer`, `clientId` → `buyerId`, `ClientCard` → `BuyerCard`, types, API fields, DB references) is scheduled in `/project-plan` and renamed in `/project-implement`.

## Keeping docs in sync

Docs are a graph: the canonical context feeds requirements → business rules → architecture → code → tests. A change in one layer should update only the documents it affects, and every document should end up describing the system as it now stands. Keep names, status values, and rules identical across all of them — and identical to the codebase's identifiers. Preserve unrelated context when you edit.

Removals count as changes: when a feature, endpoint, field, or rule disappears, prune it from every document that mentioned it, and remove the whole document if nothing real is left in it.

## Decisions

Record a decision as an ADR only when it's hard to reverse, surprising without context, and the result of a real trade-off. Otherwise skip it. The template is in [references/formats.md](references/formats.md); keep IDs sequential. ADRs are the one place history is kept on purpose — current-state docs are not.

## Bootstrapping

In a repo with no `docs/`, run `scripts/init_docs.py` to create the tree, index, and glossary skeleton, then document only what you can verify from the code and the agreed design. Mark unknowns with a `<!-- TODO -->` rather than inventing.

## Helpers & Mandatory Validation

`scripts/` holds deterministic helpers; run them from the project root:

- `init_docs.py` / `new_doc.py` — create the tree and allocate the next numbered document.
- `docs_lint.py` / `glossary_lint.py` / `adr_scan.py` — check the conventions (naming, headers, glossary shape, ADR integrity) and flag drift. **Always run these validators after editing `docs/` and fix any failures before completing Stage 2.**

## Stage 2 Gate Output (Pause for Approval)

After updating `docs/` and passing all validator scripts:
1. Summarize which `docs/` files were created, updated, or deleted, plus any glossary renames that must propagate to code in Stage 3.
2. When running inside `/project-workflow`, ask:
   > *"Stage 2 (Documentation) complete and validated. Reply **approve** to proceed to Stage 3 (`/project-plan`), or tell me what to adjust."*
   **STOP and wait for user approval.**
