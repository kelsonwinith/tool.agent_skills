# Changelog

## 1.5.0
- Growing-module slicing now explicitly applies to root `/utils` and `/hooks` (and every layer), not just feature folders. The public entrypoint keeps its flat-file path/depth (`utils/[utilName]/[utilName].util.ts`, `hooks/[hookName]/[hookName].hook.ts`) and re-exports the stable API; children are named `[main function name].[subfolder].ts`. Added root-scoped slicing examples and clarified entrypoint/child roles.

## 1.4.0
- Clarified file placement: code shared across features or used app-wide lives at the PROJECT ROOT (`/components`, `/layouts`, `/hooks`, `/types`, `/constants`, `/utils`), never inside a feature. Added root `hooks/` and `utils/` layers.
- Added §0A "Shared code lives at the project root" with a kind→location table, one-way import direction (`features/` → root), and the rule that UI primitives never live under a feature.
- Updated the decision checklist and promotion scale (Level 3 now lists all six root layers; promotion moves rather than copies).

## 1.3.0
- Function comments: added explicit rule that doc blocks live only above the function declaration, with no `//` comments on individual code lines (extract to a named helper instead).
- Expanded the §5 BAD example to show and call out inline code-line comment noise.

## 1.2.0
- Rewrote SKILL.md as a lean guideline: principles and rationale instead of a numbered, cross-referenced rulebook.

## 1.1.0
- Added `scripts/new_feature.py` to scaffold a feature module (folder, entrypoint, `.component`/`.hook`/`.type` stubs) with a regression test suite.
- Added accessibility and user-facing-text guidance.
- Removed third-party library assumptions from examples (self-contained UI primitive).
- Moved growing-module examples into `references/module-slicing.md`.

## 1.0.0
- Initial layered React/Next.js component and file architecture with zero inline styling.
