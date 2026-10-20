# Changelog

## 1.2.0
- Added interactive local Web UI companion (`scripts/workflow_ui.py`) serving an offline single-page stepper dashboard at `http://localhost:4321`.
- Enabled Dual-Mode interaction: review stage artifacts, type instructions, and click "Approve & Next Step" or "Request Revisions" directly in the browser or via chat.
- Auto-stops local server and cleans up `.workflow/` upon Stage 4 completion.

## 1.1.0
- Updated workflow documentation sync references to match the 2.0 flat singletons and numbered flows (`docs/flows/<NNN>-<name>.md`).

## 1.0.0
- Initial release of `project-workflow` orchestrator with Stage 0 auto-bootstrap and strict 4-stage gated pipeline (Grill → Docs → Plan → Implement).
