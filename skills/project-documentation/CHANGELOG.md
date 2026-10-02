# Changelog

## 1.4.0
- Glossary terms now bind docs to code: a canonical term is also the name of the concept's code identifiers, and a term whose meaning changes must be renamed in the glossary and every code identifier in the same change (e.g. `Client` → `Buyer` across docs and variables/types/fields/routes).
- Terminology-mismatch message now lists code identifiers carrying the current term and offers a coordinated rename option.
- "Keeping docs in sync" notes that document names must match codebase identifiers.

## 1.3.0
- Docs now describe the current system only: removed features are deleted from the docs and every reference is pruned. Document status is `Draft | Active` (dropped `Deprecated`).
- Canonical-context glossary is now a `| Term | Meaning | Avoid |` table; `glossary_lint.py`, `init_docs.py`, `new_doc.py`, and the examples follow the new format.

## 1.2.0
- Rewrote SKILL.md as a lean guideline: principles and rationale instead of a numbered, cross-referenced rulebook.

## 1.1.0
- Added pre-implementation grilling: a design-tree interview with frontier rounds and recommended answers.
- Added the canonical context / ubiquitous-language glossary, with a context map for multi-context repos.
- Added bundled scripts: `init_docs.py`, `new_doc.py`, `docs_lint.py`, `glossary_lint.py`, `adr_scan.py`, and a regression test suite.
- Moved formats and templates into `references/formats.md` (progressive disclosure).
- Added ADR gating criteria and terminology-mismatch reconciliation.

## 1.0.0
- Initial portable documentation guardian: numbered `docs/` tree, pre-implementation inspection, requirement-mismatch detection, and the standard ADR template.
