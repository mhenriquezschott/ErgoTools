> Avatar clicking follow-up: immediate-click checks here missed held-click native
> camera rotation. See [the corrective acceptance](avatar_click_acceptance.md) for
> the reproduced failure and fixed input handling. Toolbar/icon acceptance is unchanged.

# Visible Undo/Redo and anatomical selection — accepted

The owner's bounded follow-up is **4/4 complete (100%)**. No migration milestones,
dependencies or unrelated repairs were added. Reference code/environment and permanent
projects remain untouched. Original migration/cleanup ledgers stay 12/12 and 6/6.

## Implemented behavior

1. Redo uses a saved horizontal mirror of the processed Undo image, preserving every
   mirrored pixel, canvas, padding and alpha. Runtime loads icons/redo.png normally.
   Derived provenance/hash are separate from the 71 unchanged copied reference assets.
2. Main toolbar starts Undo, Redo, then New, Open, Save, PLOT, JROT and Export.
   Settings remains under Tools and Help under Help; their buttons are removed from
   the toolbar. Menu-only action callbacks remain available internally.
3. PLOT and JROT show a compact themed Undo/Redo strip at the upper left below Edit,
   above workspace controls. This conventional top-of-window placement keeps history
   discoverable without mixing it with map zoom or solver commands. Toolbars reuse
   existing QAction instances; menus/shortcuts share captions, availability, local
   typing/document history, pending-edit rules and busy-solver interlocks. Main buttons
   likewise route through the existing assessment history action owner. No second
   history stack, automatic Save or expansion of Undo's persistence scope is introduced.
4. A simple left click on a visible colored lower back selects LiFFT; forearms/hands
   select DUET; shoulders select ST. Built-in VTK actor picking supplies the anatomical
   region through the optional SelectableBodyRenderer port. No custom recognition,
   ray-tracing algorithm, worker/SQL interpretation or new dependency is introduced.
   Ordinary tool-tab validation preserves context/unsaved edits; rejected transitions
   retain the current tool. Accepted region changes use the existing enabled animation
   preference, and disabled animation retains full-body view. Clicking the already
   selected region leaves selection unchanged. Neutral anatomy/background do nothing.
   Movement beyond five widget pixels cancels click intent while native VTK dragging
   still rotates. Pixel scaling is accounted for; closed renderers ignore queued clicks
   and release their callback. Sidebar remains active-tool-specific.

## Verification

- Full approved Linux gate: **1,311 tests passed, zero failures/skips; 95.79% combined
  statement/branch coverage**. Ruff, formatting, strict types (256 source/tool files),
  architecture, naming, complete documentation review and builds pass.
- Fifteen changed/new maintained files were substantively reviewed and their source
  hashes renewed. The complete documentation inventory has zero pending reviews.
- Focused tests compare static mirrored image pixels and resource hashes, exercise
  main-toolbar exact Undo/Redo, actual PLOT/JROT toolbar replay, real VTK surface clicks
  for all three tools, neutral/drag no-ops, disabled/enabled animation and safe close.
- Twenty-three native EN/ES captures were inspected, including main empty/populated
  and Undo/Redo states, body selection/focus, PLOT/JROT initial and history-enabled
  states, and enlargement to 1800×1200. Model, result cards, footer and bottom controls
  remain visible. Existing Spanish main-window minimum-width text fit is unchanged;
  the enlarged Spanish workspace was inspected at 1800×1120.
- Comprehensive-project copy: all **194 saved assessment sources/results unchanged**,
  permanent fixture hash unchanged. Click navigation/history controls do not Save.
- Final bilingual guide/resource follow-up: **16 tests and 78 subtests passed**.
  Packaged guides describe the menu-only Settings/Help entry points and new controls.

Evidence: artifacts/history_toolbar_check.log, history_toolbar_guides.log,
history_toolbar_review/validation.json and history_toolbar_reviewed_files.json.
Icon inventory no longer lists Redo as missing; Retire remains pending owner artwork.
Linux delivery is refreshed locally; nothing was installed, published or pushed.
