# Changelog

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
