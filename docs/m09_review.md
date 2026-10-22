# M09 bounded shared UI review — complete

M09 is complete following the owner's explicit CR005 approval on 2026-10-11.
All three criteria close; **94.50/100; 9/12 complete**. The fixed plan/points
remain unchanged. M10 is next, not started. See m09_acceptance.md for final results.

## Comparison and bounded correction

Reused the original-source navigation construction/style evidence in
`docs/reference/f75-main-navigation-capture.py.txt` and `docs/main_navigation.md`,
M01 original assessment/header/keyboard comparisons, M02–M06 management/PLOT
comparisons, and M07/M08 JROT comparisons. Current whole-window EN/ES native
captures cover the shared controls at 1550×1015 and 1800×1200. This is shared
closure, not a second migration of the component forms.

The explicit M09 EN/ES dialog criterion identified untranslated Authors credit
prose. The single bounded correction localizes that prose only. English bytes,
proper names, institutional attribution, external link, original logo, 600×700
size and close interaction remain unchanged. Two language regressions check
attribution and the parsed link target. Both rendered dialogs fit their original
geometry. This does not revise factual attribution or scientific content.

R011 is closed without changing layout: the original individual F155 PNG and the
current individual minimum-size Spanish ST pending PNG show the full caption.
Current Repeticiones ink spans x=1..76 in a 113-pixel content rectangle;
Momento máximo spans x=1..112. The measured horizontal advances are 78 and 113.
This conclusion uses visible pixels plus font metrics, not containment alone.

The M04 Transfer paragraph concern is also closed without a new code change.
The existing catalog translates all five explanatory paragraphs; current native
ES minimum-size capture and label records confirm their actual rendered Spanish.
User data such as project names and shift IDs remain verbatim.

## Shared matrix and valid reused evidence

| Surface | Current/reused acceptance |
| --- | --- |
| Integrated header/footer/context/worker navigation | F75 source constructors/style plus current EN/ES minimum/enlarged captures; project-caption mismatch below is resolved by approved CR005. Processed original icons and chevrons retained. |
| Menus and Settings | Current EN/ES expanded Project/Edit/View/Tools/Help and Settings/unit-list captures; packaged menu/preferences/recent/decimal tests. Existing menu/settings exceptions retained. |
| LiFFT/DUET/ST grids, context/saved picker, task count, versions | M01 original 6 tool/unit × 2-size comparisons, restored selectors-first ST keyboard order, F152/F155 picker/count/version/cancel evidence; current all-tool EN/ES × both display units. |
| Worker, Organization, Jobs/profiles/placements | M02/M03 accepted source-derived forms, EN/ES selected/expanded/empty/enlarged and canonical height/weight Save/reopen in opposite units; unchanged controls reused. |
| Project Properties/Details and lifecycle/file/dirty/delete dialogs | M04 source comparisons/current accepted native lifecycle states; current packaged Properties/Details/Help/navigation regressions. File identity, default cancellation and pending input tests remain valid. |
| Transfer | Current EN/ES selected destination/tree and minimum-size paragraphs; accepted M04 transfer/rollback/identity and source evidence reused. |
| PLOT filters/results/workplace/map/graph/settings/detail/highlight/export | M05/M06 source comparisons and accepted EN/ES controls/history states; all-tool Metric/Imperial CSV comparisons (370 original rows), map/graph exports and dimensionless risk remain valid. No changed PLOT controls. |
| JROT scope/schedule/targets/comparison | M07/M08 current EN/ES original-source and comprehensive-copy captures; recorded risk/profile units retained, dimensionless optimization unchanged. |
| Avatar and gauge | Current all-region native views and exact Rotate/Zoom/Reset camera restoration in all 12 tool/language/display-unit cases; settled gauge values, pending unavailable state, minimum/enlarged containment and visible pixels. Existing renderer lifecycle/animation and M01 keyboard evidence reused. |
| Authors/Help | Current original-size EN/ES Authors; original logo/link preserved. Owned Help launcher, repeat/cancel/error/pending edits pass. The actual updated guide is assigned to M11, not claimed complete here. |

Twelve native source/display cases explicitly Calculate/Save, toggle both display
systems, export all three saved ownership rows, and independently reopen unchanged
canonical sources. Within each tool, all CSV data except timestamp remains equal
across unit toggles. CSV's fixed English machine headers and recorded calculation
unit labels remain deliberate; DUET is unit-independent and saved rows may have
different recorded display-unit labels. They must not be rewritten as one uniform
unit merely to match a screenshot. M01/M02/M04 supply both source/body-storage unit
systems and exact opposite-unit Save/reopen evidence.

All 34 final native PNGs were inspected in labeled sheets; Spanish Authors,
Transfer and minimum-size ST pending were additionally inspected individually.
The complete intended region-specific avatar viewport, cards, task headers,
context/footer and bottom controls fit. Brand/tool proper names and user-entered
project/worker/shift names intentionally remain untranslated.

## Caption mismatch and approved disposition (CR005)

Original `src/main.py` live update at lines 4188–4194 sets:
`Current Project: <name>  •  Loaded` in the header and
`Current Project: <name>` in the footer. Current MainNavigation sets only `<name>`.
The earlier F75 geometry harness substituted a bare name in both implementations,
so it did not exercise the original live caption update. No approved exception
for that simplification was found. This is a concrete presentation gap, not new
infrastructure or a reason to add a milestone.

A reviewable patch is `docs/reference/m09-header-proposal.patch.txt`; it was applied after owner approval. It restores the original caption and empty/unsaved behavior using the
existing view/localization boundary, with Spanish equivalents and no source/data
change. Proposed verification: EN/ES empty/unsaved/saved/closed captions, pending
assessment preservation, and native long-title header/footer fit. Owner explicitly approved restoration. Four new EN/ES integration cases cover
pending input and New/first-Save/Close; existing metadata tests still assert literal
stored names. Final packaged regressions pass. Fourteen additional native captures
cover empty/unsaved/saved/closed, pending/populated, minimum/enlarged states. All
were inspected, with individual Spanish populated minimum inspection as well.
The complete caption ink fits (EN right=637/638 px, ES right=648/649 px at minimum).
The avatar/cards/context/footer/bottom controls fit; the source and independent
reopened source stay equal. Existing QToolBar manages narrower space for long titles;
Help remains available through the accepted menu. No extra milestone was added.

## Validation and harness limits

Approved Python 3.13.14; **1,184 tests, 96.40% coverage**, Ruff/format/strict mypy,
architecture and both package builds pass. Independent extracted-wheel focused
checks: **113 tests plus 60 subtests**. Final native audit also runs from the wheel;
all ErgoTools imports are asserted within extraction. All 500 reference manifest
files and uv.lock are unchanged. See m09_validation.json.

Early native harness attempts needed corrections: advance every camera segment;
never replay a cleared gauge animation; pass a Path to the repository; compare
recorded CSV units per saved row rather than assume all labels are Imperial.
These were harness assumptions, not product defects. The final corrected native
run passes; the earlier logs are retained and not claimed as successful native
runs. Focused wheel tests were not repeated after the export harness correction.
Linux XCB is validated here; Windows/macOS remain M12's deferred target checks.


Final CR005 gate is artifacts/m09-caption-check.log, final rebuilt-wheel focused
and native gate is artifacts/m09-caption-wheel.log. The earlier 34 shared images
remain evidence for unchanged controls, not final-caption screenshots. Fourteen
new images close that changed surface; total inspected is 48. Initial test edits
briefly substituted display captions into literal metadata assertions; these test
expectations were corrected without changing production storage. Final metadata
and display regressions/full gate pass. No further validation repeated after pass.
