---
name: project-documentation
description: "Portable, project-agnostic documentation guardian. Manages, inspects, and continuously synchronizes a project's canonical context (ubiquitous-language glossary), product, business, architectural, and technical documentation under docs/. Use this whenever you develop, modify, or refactor a feature, or when requirements, business rules, APIs, data models, architecture, or terminology change — even if the user never says 'docs' or 'documentation.' It enforces relentless pre-implementation grilling of the request's logic (a design-tree interview that resolves every open decision before anything is written), terminology reconciliation against the canonical context, requirement-mismatch detection with user confirmation before requirement changes, multi-document consistency, bundled deterministic validators (docs-tree, glossary, and ADR checks), and the numbered docs subfolder file convention. Works for any language, framework, or repo shape (single app or monorepo)."
license: MIT
compatibility: "Requires Python 3 (standard library only) to run the bundled helpers in scripts/."
metadata:
  version: 1.2.0
---

# Project Documentation

A project's docs and its code drift apart quietly. This skill keeps them honest: it manages the `docs/` tree, agrees on what words mean, and makes sure a request's logic is settled before anything gets written.

It contains no project-specific facts — everything it needs is discovered from the project and written into that project's own `docs/`.

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
**Status**: Draft | Active | Deprecated
```

Keep `docs/README.md` as an index, with the canonical context listed first.

## The canonical context

Different people call the same thing different names — "account" vs "customer", "order" vs "purchase". Left alone, everyone guesses, and the guesses drift. So keep one glossary at `docs/context/001-ubiquitous-language.md` that says what each project-specific term *is* (not what it does) and lists the words to avoid:

```markdown
**Order**:
A request from a customer to buy one or more items.
_Avoid_: Purchase, transaction
```

Only project-specific terms belong here — not general programming concepts. When a term is resolved, write it down immediately. When someone uses a term that conflicts with the glossary, say so and reconcile it before going further. Multi-context repos keep one glossary per context plus a map (format in [references/formats.md](references/formats.md)).

## Before you build

A request is rarely complete, and its gaps are exactly where you'd guess wrong. So before writing docs or code, grill the request to a shared understanding:

- Treat it as a design tree. Ask the questions you can answer *now* — whose prerequisites are already settled — as one round, then wait for the answers.
- Number each question and give your recommended answer; a concrete proposal is faster to react to than an open question.
- Look facts up yourself (files, configs, existing behavior). Only decisions go to the user.
- Stop when nothing is left assumed and the user confirms you're aligned.

Then check the request against what's already documented:

- **Terminology** — resolve the request's words against the glossary. Undefined terms get a proposed definition; conflicts get flagged.
- **Requirements** — if the request conflicts with a documented requirement, stop and show the mismatch, then wait for confirmation before changing anything.

Message templates are in [references/formats.md](references/formats.md).

## Keeping docs in sync

Docs are a graph: the canonical context feeds requirements → business rules → architecture → code → tests. A change in one layer should update only the documents it affects. Keep names, status values, and rules identical across all of them, and preserve unrelated context when you edit.

## Decisions

Record a decision as an ADR only when it's hard to reverse, surprising without context, and the result of a real trade-off. Otherwise skip it. The template is in [references/formats.md](references/formats.md); keep IDs sequential.

## Bootstrapping

In a repo with no docs, run `scripts/init_docs.py` to create the tree, index, and glossary skeleton, then document only what you can verify from the code. Mark unknowns with a `<!-- TODO -->` rather than inventing, and prompt the user for the high-level things you can't infer — personas, business rules, ambiguous terms.

## Helpers

`scripts/` holds optional helpers; run them from the project root.

- `init_docs.py` / `new_doc.py` — create the tree and allocate the next numbered document.
- `docs_lint.py` / `glossary_lint.py` / `adr_scan.py` — check the conventions (naming, headers, glossary shape, ADR integrity) and flag drift. Treat a failure as a blocker.

These are conveniences, not gates. The point is the shared understanding above.
