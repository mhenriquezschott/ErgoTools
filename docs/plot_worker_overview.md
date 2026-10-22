# Original PLOT Worker Overview composition — F110

`PlotWorkerOverview` now composes the original selector/order/alphabet/navigation,
workplace context, worker details, assessment/job comparison, 72-pixel marker
preview, Locate and F109 visual controls. The reviewed `plant_layout.py`
`configureResponsiveLayout`, selector/navigation methods, `loadWorkerDetails`,
Locate behavior and `PlotWorkerMarkerPreview` define the source geometry/workflow.
The source search button remains styled but disabled: its original picker and
Load Into Tool/context actions are the next migration, not implemented here.
Production PLOT and full details tabs/summary composition remain disabled/pending.

## Working behavior

The selector contains selected-tool saved results, including hidden/unplaced
workers. It stores assignment IDs rather than source dataset indices or parsed
worker captions. ID/name ordering and last-name alphabet disclosure operate on
the saved snapshot without SQL reloads or writes. Unavailable initials are disabled.
Clicking a map marker synchronizes the selector and reveals All if necessary.
A surviving selected identity is retained across result replacement. Navigation
clamps first/previous/next/last. Display captions follow the source's ID/name policy.

The details/result area displays birth-year age, optional sex/body metadata,
selected branded tool, saved damage/probability, placed job and optional current
approved job risk/profile. Zero evidence remains valid. Missing/scientific-review
worker risk remains unavailable and never produces a false zero/difference.
Worker probability fractions become displayed percentages; job evidence is already
percent. Differences are percentage points. Literal labels use plain text and
profile tooltip values are escaped.

The preview preserves source dimensions/paint geometry for circle, triangle,
unknown hexagon, comparison job square and blue selection. Locate ensures a visible
existing marker is in view and pulses ten times at 190 ms. It creates no hidden
geometry, stops on selection/rebuild/close, and releases its temporary Qt item.

F109 visual settings remain the bottom region. Typed X/Y/scale drafts are now
retained per assignment when navigating between workers; Save All validates and
accepts those drafts before its one transaction. Failure retains them; successful
saves or explicit dataset clearing release the relevant drafts. No event pumping,
SQL or global main-window dependency enters the overview.

## Units, resizing and explicit differences

Canonical body measurements remain kg/cm. Metric/imperial display uses the
existing pure body projection and adds explicit kg/cm or lb/in labels. This is a
unit-clarity improvement over the original ambiguous Weight/Height captions;
changing display does not write or round the stored metadata. Original-image
marker pixels and dimensionless scale do not change with body units.

The original 500-pixel-pane alphabet dimensions are retained where space permits.
Letter buttons may shrink from 15 to 12 pixels at 390-pixel width, preventing the
original fixed row from clipping its last letters. Source root margins, subgroup
grids, spacing, minimum heights, icons and bottom controls remain. Job/difference
values can wrap instead of forcing the panel wider. Spanish empty-preview text
uses two short lines to fit the original 72-pixel preview. No broad style redesign
or final full-window visual parity is claimed. Search remains explicitly disabled.

## Validation and limitations

Three focused cases cover both languages, stable ID/name/alphabet selection,
marker synchronization, per-worker drafts and batch Save, result replacement,
body units without stored changes, Locate/hidden/clear/close, literal profile
names, optional worker names and missing/scientific risk. 857 baseline tests pass,
96.17% coverage; Ruff check/format, strict mypy (179 source files), architecture
and wheel/sdist builds pass. The extracted wheel verifies actual selector,
draft-navigation/batch-save, comparison/units/Locate, assets and saved reopen.
All 500 reference hashes and the approved dependency lock remain unchanged.

Native captures under `artifacts/plot-worker-overview` include extracted source
layout/preview fixtures and English/Spanish empty/populated, alphabet/name-order,
metric/imperial, comparison, switched/restored drafts, Locate, narrow 390×740 and
enlarged 510×900 panes. Source/new empty, individual and comparison preview images
match pixel-for-pixel. Source whole-layout captures are reviewed geometry evidence;
whole-layout pixel equality is not claimed because unit captions, search state and
narrow sizing deliberately differ. Adjacent map containment passes at 1600×900
and 1920×1200. Full PLOT cards/tabs/outcomes and final VTK/application acceptance
remain outside this component harness.

Evidence: `f110_validation.json`, `artifacts/f110-check.log`,
`artifacts/f110-wheel.log`, `artifacts/f110-native.log`; source/capture/verifier
reproduction scripts are archived as `docs/reference/f110-*.py.txt`.

Next: original worker search picker and marker context/Load Into Tool integration,
then summaries/full PLOT composition, parent close consent and remaining map
workflows. Intentional deletion composition and comprehensive-copy acceptance
remain. JROT follows PLOT: CBC single-tool, HiGHS multi-tool, no GLPK. Overall
completion percentage/finish date remain unvalidated; the old 67% is withdrawn.
