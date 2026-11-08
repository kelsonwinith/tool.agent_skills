# Changelog

## 2.0.0
- **Requirement-Polishing Focus**: Refocused the skill from low-level coding mechanics to requirement polishing and mutual understanding. The skill reconciles user prompts with the existing codebase and docs, settles edge cases, and secures alignment before any coding occurs.
- **Prettier Temporary `SUMMARY.md` Confirmation**: Instead of dumping walls of raw text into the terminal, the agent writes the Plain-Language Before & After breakdown, Mermaid flowchart, and collision audit to a temporary `SUMMARY.md` in the project root so it renders beautifully in markdown preview before code implementation.
- **Zero-Context Scaffolding (No `references/` directory)**: Removed `references/example-docs-tree.md` and `references/formats.md`. All templates and structural conventions are executed strictly via scripts (`init_docs.py`, `new_doc.py`), achieving zero token waste on reference documents.
- **Strict Docs-First Implementation Loop**: Enforces "Requirements First, Code Later" across all development requests (add, fix, modify, remove) before touching code.
- **Pre-Implementation Grilling**: Prompts and aligns on requirements for non-existent/incomplete features before drafting specs or code.
- **Lean High-Signal Structure**:
  - Root singletons without numbering: `docs/README.md`, `docs/context.md`, `docs/architecture.md`.
  - Scalable numbered subfolders: `docs/features/<NNN>-<kebab>.md` and `docs/decisions/<NNN>-<kebab>.md`.
- **Mandatory Feature Flowcharts**: Every feature spec in `docs/features/` must include a Mermaid flowchart representing its logic or state flow.
- **Cross-Feature Collision & Overlap Auditing**: Each feature doc explicitly checks and documents potential overlaps or contradictory rules against adjacent features.
- **Automated Template Scaffolding**: `init_docs.py` automatically generates starter templates for all topics to conserve LLM token usage and prompts users to document existing codebases first.
- **Updated Validators**: `docs_lint.py`, `glossary_lint.py`, `new_doc.py`, and test suite updated to validate lean root singletons, Mermaid blocks, and feature templates.

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
