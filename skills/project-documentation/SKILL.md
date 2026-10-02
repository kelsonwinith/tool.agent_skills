---
name: project-documentation
description: "Portable, project-agnostic documentation guardian. Manages and continuously synchronizes a project's canonical context (ubiquitous-language glossary), product, business, architectural, and technical documentation under docs/. Use this whenever you develop, modify, or refactor a feature, or when requirements, business rules, APIs, data models, architecture, or terminology change — even if the user never says 'docs' or 'documentation.' It grills the request's logic before writing (a design-tree interview), reconciles terminology against the canonical context (treating each glossary term as the concept's name in both docs and code, so a renamed term renames its code identifiers too), detects requirement mismatches and confirms before changing them, keeps every document describing the current system (removed features are removed from the docs), ships deterministic validators, and follows the numbered docs subfolder file convention. Works for any language, framework, or repo shape."
license: MIT
compatibility: "Requires Python 3 (standard library only) to run the bundled helpers in scripts/."
metadata:
  version: 1.4.0
---

# Project Documentation

A project's docs and its code drift apart quietly. This skill keeps them honest: it manages the `docs/` tree, agrees on what words mean, and makes sure a request's logic is settled before anything gets written.

It contains no project-specific facts — everything it needs is discovered from the project and written into that project's own `docs/`.

## Docs describe the current system, not its history

Documentation is a snapshot of what the system *is right now*, never a changelog. If a feature is removed or replaced, delete its documentation and every reference to it — don't leave a "removed" or "deprecated" section behind, and don't keep describing behaviour that no longer exists. When code and docs disagree, the docs are wrong until updated.

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

Only project-specific terms belong here — not general programming concepts. One canonical term per concept; list every synonym in `Avoid`. When a term is resolved, write it down immediately. When someone uses a term that conflicts with the glossary, say so and reconcile it before going further. Multi-context repos keep one glossary per context plus a map (format in [references/formats.md](references/formats.md)).

### A glossary term is the same word in docs and code

The canonical term is not just prose vocabulary — it is the name that should appear in the codebase too. Variables, functions, types, DTO fields, API params, DB columns, and route segments all carry the same concept, so they should use the same canonical term. When docs say `Buyer` but code says `client`/`Client`/`clientId`, every reader has to translate between two vocabularies, and the drift is where bugs and misunderstandings hide.

- The glossary term is the single source of truth for a concept's name. Pick the canonical English term, then use it consistently across docs **and** code.
- Code identifiers follow the term, adjusted only for the language's casing convention — i.e. the term's own casing is not mutated beyond that. `Buyer` → `buyer`, `BuyerId`, `buyerId`, `useBuyer`, `fetchBuyers`; never `client`, `ClientId`, `customer`.
- If a concept already has a different name in code, the mismatch is a reconciliation task, not something to leave in place.

### When a term's meaning changes, rename it everywhere at once

A glossary term is a living definition: requirements change, and the word often changes with them. Treat a rename as a change in the canonical context that must propagate in a single, synchronized move — never let a new name land in the glossary while the old name lingers in code, or new code while docs still describe the old concept.

The rule: **changing a term means updating both its glossary entry and every code identifier that used the old name, in the same change.** No half-renames, no alias left behind, no "avoid" synonym still living in the source.

Example — the requirement shifts so a `Client` is now called a `Buyer`:

1. Update `docs/context/001-ubiquitous-language.md`: rename the term to `Buyer`, rewrite its meaning, and move `Client` into the `Avoid` column.
2. Rename the code identifiers that carried `client` → `buyer` (`client` → `buyer`, `clientId` → `buyerId`, `ClientCard` → `BuyerCard`, types, API fields, DB references).
3. Update every dependent document that mentioned the old term (requirements, business rules, architecture, data models).
4. Flag the rename to the user as a terminology change, per the reconciliation rules below, before executing it.

Skip the glossary-vs-code link and you get the exact confusion this skill exists to prevent: docs talking about buyers while the codebase still talks about clients. This skill defines *what you should do* — the ordering of the rename and the invariant that both sides stay in sync — not the mechanics of any specific refactoring tool; apply your project's own rename/refactor process to carry it out.

## Before you build

A request is rarely complete, and its gaps are exactly where you'd guess wrong. So before writing docs or code, grill the request to a shared understanding:

- Treat it as a design tree. Ask the questions you can answer *now* — whose prerequisites are already settled — as one round, then wait for the answers.
- Number each question and give your recommended answer; a concrete proposal is faster to react to than an open question.
- Look facts up yourself (files, configs, existing behavior). Only decisions go to the user.
- Stop when nothing is left assumed and the user confirms you're aligned.

Then check the request against what's already documented:

- **Terminology** — resolve the request's words against the glossary. Undefined terms get a proposed definition; conflicts get flagged. If a term's *meaning* changed, treat it as a rename: the glossary entry and every code identifier using the old word change together (§"When a term's meaning changes").
- **Requirements** — if the request conflicts with a documented requirement, stop and show the mismatch, then wait for confirmation before changing anything.

Message templates are in [references/formats.md](references/formats.md).

## Keeping docs in sync

Docs are a graph: the canonical context feeds requirements → business rules → architecture → code → tests. A change in one layer should update only the documents it affects, and every document should end up describing the system as it now stands. Keep names, status values, and rules identical across all of them — and identical to the codebase's identifiers, since the glossary term is also the code's name for that concept. Preserve unrelated context when you edit.

Removals count as changes: when a feature, endpoint, field, or rule disappears, prune it from every document that mentioned it, and remove the whole document if nothing real is left in it.

## Decisions

Record a decision as an ADR only when it's hard to reverse, surprising without context, and the result of a real trade-off. Otherwise skip it. The template is in [references/formats.md](references/formats.md); keep IDs sequential. ADRs are the one place history is kept on purpose — current-state docs are not.

## Bootstrapping

In a repo with no docs, run `scripts/init_docs.py` to create the tree, index, and glossary skeleton, then document only what you can verify from the code. Mark unknowns with a `<!-- TODO -->` rather than inventing, and prompt the user for the high-level things you can't infer — personas, business rules, ambiguous terms.

## Helpers

`scripts/` holds optional helpers; run them from the project root.

- `init_docs.py` / `new_doc.py` — create the tree and allocate the next numbered document.
- `docs_lint.py` / `glossary_lint.py` / `adr_scan.py` — check the conventions (naming, headers, glossary shape, ADR integrity) and flag drift. Treat a failure as a blocker.

These are conveniences, not gates. The point is the shared understanding above.
