# First desktop slice audit — F27, 2026-09-29

This is a concrete implementation/acceptance plan. No window has been added or visually accepted. Overall completion remains approximately 51%; an audit does not count as implemented GUI functionality.

## Reference visual contract

The active `src/main.py:mainWorkspaceStyleSheet` was extracted without importing the application into `reference/workspace-style.qss.txt`. Source SHA-256: `6e8a65a2ba7370b1dbda199110e3cfbe0b9f62d91ed9677ceea9f8483b3e2fc5`. `styleAssessmentControls` and toolbar/header construction were also read. This archived reference is not yet a runtime stylesheet or a claim that every selector applies to new widgets.

| Element | Existing treatment to preserve |
|---|---|
| Workspace | #F4F7F9 background; #1B2933 text; Segoe UI 12px |
| Branding | #073E68 header, white brand text; navy #0B326C section labels |
| Panels/cards | White, #D5DEE5 borders, 6–7px corner radii |
| Inputs | 30px minimum height; #BCC9D3 border, 5px radius, 8px horizontal padding |
| Focus/selection | #08A9B5 focus border; #087E91 popup selection with white text |
| Calculate | #087E91 fill, white text, #096D7C hover; calculate_light.png at 28px |
| Reset/history styling | Navy text; original reset uses undo.png at 26px; avoid ambiguous reset/history labels |
| Task headers | 42px sticky header height, aligned with scrolling columns |
| Result emphasis | #F97316 metric value, established risk palette and source-bound results |

Use package copies of the processed reference icons: ergotools_logo.png, lifft.png, new.png, open.png, save.png, undo.png, calculate_light.png, delete.png, cancel.png and close.png. A dedicated Redo icon is absent. Use a styled text/menu action initially, not an unrelated system icon; a future icon must be normalized and reviewed. Do not invent a 3D placeholder and present it as avatar parity. Font availability and fallback metrics must be inspected on the actual display.

## Screen and boundary plan

Build an isolated LiFFT desktop entry point with a thin Qt view, presenter and composition root. Domain/application remain Qt-free; storage stays in infrastructure. The view consumes packaged assets, existing localization, source-bound evaluation and presentation mappings. Qt types never enter the domain or session store.

Expose source unit metadata separately from display units. Initialize editor text with the full-precision formatter; bind an AssessmentEditor context when rendering inputs and capture it in callbacks. A successful commit rebinds and refreshes rows/results. Do not submit untouched rounded text on focus loss. A preference change with pending text needs explicit handling: keep text available, and let the user commit under its original context or discard before switching. Invalid or stale text must remain visible for correction, not disappear during rerender.

Wire project create/open/save/close through the existing workspace, using temporary development projects for tests. Dirty close/switch uses Save/Discard/Cancel; history stays document-owned. Calculation calls AssessmentEvaluator and displays only current outcomes, including metric review-required status. Add/delete/reset/repetition editing must use explicit commands; never let widget callbacks mutate source fields directly. Persist only original source, not view projections or localized text.

The initial screen does not include worker/job/organization context, legacy project import, PLOT/JROT, WebEngine or the avatar. These are explicit remaining integration slices. Full app parity requires them; no disabled mock controls should imply implementation.

## Acceptance after dependency approval

1. Verify exact installed Qt/SIP/Python versions and unchanged existing pins. Test imports, offscreen Qt rendering, display availability and packaged asset loading.
2. Run existing gates plus real widget-event tests for editing, source/display units, decimal settings, stale callbacks, history, calculate/review/failure, save/reopen and dirty-close decisions. Keep operational databases untouched.
3. Capture and inspect the actual window at its intended size and a smaller supported size: empty, populated, invalid, selected, expanded menus/dropdowns, both languages, both units, long labels and scrolling. Check adjacent cards, labels and bottom controls together for clipping. Screenshots and findings belong in the milestone record.
4. Avatar/VTK acceptance is deferred because no avatar is added here. When that adapter arrives, inspect the complete model and neighboring layout at the target size, and request manual inspection if rendering cannot be verified reliably.

The dependency proposal is `desktop-dependency_proposal.md`. Installation is pending explicit approval under AGENTS.md. No dependency files or GUI source were modified during this audit. Baseline checks remain 277 passing tests, 99.61% combined coverage, strict mypy (73 files), Ruff/format, architecture and builds passing.

## F28 implementation

The dependency approval is resolved and the first runnable preview is implemented. See [desktop_preview.md](desktop_preview.md) for actual scope, tested states and remaining work. The audit above remains historical; per-task output columns, shortcuts and full framework localization are still pending.
