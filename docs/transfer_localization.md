# F95 — Worker Transfer language completion, 2026-10-06

The original Worker Transfer form now localizes supporting paragraphs, empty
source guidance, filter/operation tooltips, full tool descriptions, checkbox hints,
Cancel, All, previews and owned confirmation/warning/error/success messages.
Spanish All is Todos with 34-pixel width to avoid clipping; filter keys remain
stable. The source-derived English three-column form and F92's 1280 by 640 minimum
are retained. No transfer rules, data fields, dependencies or project schema changed.

A dedicated presentation catalog translates construction-time captions only.
The former post-load walk over QLabel widgets could translate a user's name if
it matched a caption such as Shift. Record widgets are now populated separately:
IDs, names, workplace/shift values and tool identities remain exact data.

Owned message boxes translate Yes/No/OK and preserve keyboard mnemonics, No as
confirmation default, and No on Escape. No global translator is installed.
Native review found a presentation discrepancy to retain in the final parity
inventory: the explicitly owned Qt confirmation on this Linux style orders No/Yes
and uses different stock button icons, whereas the earlier static Qt capture
orders Yes/No. The form controls retain their reference layout, but this native
message appearance is not claimed as exact final parity. Consent/Cancel semantics
are tested. Resolve the native message discrepancy before final UI acceptance.

Known preflight errors are translated. Unknown Spanish rejections show guidance
to reopen/check the destination, with the original rejection logged. Existing
execution logging/rollback remains. Copy/Move, dirty-source consent, historical
ownership and source units follow F92. This does not translate the separate main
Save/Discard/Cancel prompt or establish whole-application language completeness.

Five focused new cases cover English/Spanish actual confirmation/conflict boxes,
owned controls/tooltips, All filtering and names matching captions. The eight
existing transfer cases still cover all three tools, older history, atomic rollback
and Save/Cancel. Required gates pass 734 tests, 96.37% combined coverage, lint/format,
strict mypy on 152 source files, architecture, wheel and source builds. Extracted-
wheel Spanish consent and three-tool Copy/Move-Save preserve units/history/settings.
All 500 reference hashes and the approved lock remain unchanged.

Native artifacts/transfer-localization captures cover original/new English default,
Spanish selected Copy/Move, minimum/enlarged, empty/filter, tooltip and owned
confirmation/conflict/error/success states. Integrated native VTK, cards, captions
and bottom controls remain visible before/after Copy. Only synthetic data was used.
Evidence: f95_validation.json, artifacts/f95-check.log and archived
reference/f95-capture.py.txt, f95-tooltip.py.txt and f95-verify.py.txt.

Next usable workflow is original View camera animation/preferences. Other dialog /
main-prompt / stock-control localization and native message parity remain recorded.
Project details/sidecars, scientific gates, PLOT/JROT, legacy import and final copied-
project/platform acceptance remain. No validated overall percentage or finish date.
