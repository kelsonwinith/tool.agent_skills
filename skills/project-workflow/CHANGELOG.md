# Changelog

## 1.3.0
- Added Pipeline Stages & Skills configuration section to the Web UI dashboard:
  - Enforced locked stages (Stage 1 Grill and Stage 4 Implement are locked 🔒 for flow integrity).
  - Allowed toggling optional stages (Stage 2 Docs and Stage 3 Plan can be toggled on/off on the fly).
  - Displayed attached skills per stage with active/inactive chips.
  - Added interactive Stack Architecture Selector (`React / Next.js`, `Go Hexagonal`, `Generic Clean`).
  - Added `--next-stage <N>` CLI option and automatic stage-skip logic.

## 1.2.0
- Added interactive local Web UI companion (`scripts/workflow_ui.py`) serving an offline single-page stepper dashboard at `http://localhost:4321`.
- Enabled Dual-Mode interaction: review stage artifacts, type instructions, and click "Approve & Next Step" or "Request Revisions" directly in the browser or via chat.
- Auto-stops local server and cleans up `.workflow/` upon Stage 4 completion.

## 1.1.0
- Updated workflow documentation sync references to match the 2.0 flat singletons and numbered flows (`docs/flows/<NNN>-<name>.md`).

## 1.0.0
- Initial release of `project-workflow` orchestrator with Stage 0 auto-bootstrap and strict 4-stage gated pipeline (Grill → Docs → Plan → Implement).
