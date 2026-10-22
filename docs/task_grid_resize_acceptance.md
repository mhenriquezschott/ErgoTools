# Independent task counts and unused rows — owner-authorized correction

Owner approves implementing the task-grid audit corrections on 2026-10-18, after
confirming that counts are independent per project/worker/tool/real assignment or
standalone owner. Workplace association still requires no Job. Linux migration and
cleanup remain complete at 100%; this is a bounded owner-testing correction, without
an added milestone, dependency, schema or numerical-model change.

## Implemented behavior

Settings > Assessment shows the project, worker ID/name, active tool and standalone
or full workplace/shift/optional Job context. Its checkbox is now **Change number of
tasks on Apply**, with visible unchecked/checked/disabled indicators. Shared styling
keeps native checked ticks and supplies an explicit unchecked outline robust under
inherited dialog styles; the original transparent-background rule is removed from
checkboxes/radio buttons. Risk-gauge/avatar options retain their normal ownership.

Each assessment starts with 15 slots and supports 1-100 independently. Increasing
retains exact existing task IDs/values and appends default blank rows. Reducing keeps
the exact prefix and removes only trailing rows. Removing entered trailing values or
nondefault selectors requires explicit consent, default Cancel, identifying the row
range and context. Pending tail text, including invalid text, is included in the loss
inspection. Cancel leaves it untouched. Accepted resizing commits valid retained form
text; invalid text stays available for correction rather than being silently erased.
An unchanged count creates no source/history edit or result invalidation.

Existing shared project Undo/Redo restores exact truncated inputs, IDs, order, units,
ST direction convention and matching saved result checkpoint. Counts and data on other
workers/tools/assignments remain unchanged. Main Save is still the sole durable project
boundary. The two maintained comprehensive projects and owner workflow file are not
rewritten by this change; tests/captures use disposable projects or private copies.

Grid evaluation ignores wholly unused slots for completeness whenever at least one
row is started. It preserves slot order and missing source values. A numeric zero is
entered data; DUET's default zero scale and ST's default direction alone do not make
unused slots entered. Started rows lacking required values retain explicit partial
status/issues; invalid numeric input still blocks calculation. Entirely blank sources
claim no modeled probability. Strict preparation/evaluate APIs retain their contracts.
Calculated values, units, intrinsic rounding and formulas are unchanged. Main result
cards, PLOT and summary exports receive the consistent new grid classification.

Previously saved result-status metadata remains a historical calculation record until
Calculate and main Save refresh it. No automatic recalculation, result rewrite or schema
upgrade is performed on Open. No assessment versions or redundant results are added.

## Validation and limitations

Final required native gate: **1,449 passed, zero failures/skips, 94.30% combined
coverage**. Standards/types (265), architecture/naming, documentation/review and
wheel/source builds pass. Twenty changed maintained files substantively reviewed;
all 428 files/2,944 named functions remain reviewed with zero pending reviews/gaps.
The independent extracted wheel passes **100 native tests**; all 243 package Python
files and both bilingual guides match source. Twenty-four native captures inspected;
eighteen actual dialog-frame indicator regions independently confirm visible pixels.

Current actual gate/package/visual/protection evidence is recorded in
`artifacts/task_grid_resize_validation.json`. Both the required full code-slice gate and
independent built-wheel verification pass. Owner manual acceptance remains pending.

Focused native regressions cover all three tools, metric/imperial, growth/shrink/equal
counts, invalid/cancelled text, exact shared source/result replay and Save/reopen.
Real assigned-worker fixtures verify unchanged sources for other workers/tools/context;
additional same-worker/same-shift tests save different counts at two stations with no
Jobs for each tool. Pixel tests inspect the actual unchecked indicator in English and
Spanish, enabled/disabled, without matching stylesheet text. Existing PLOT/export and
scroll tests were updated where they deliberately expected destructive reset/partial
unused slots; no numeric assertions or guards were suppressed.

Native XCB captures include English/Spanish Settings checkbox states and context labels,
real assigned Job/no-Job contexts, Cancel-default removal dialogs, gauge/avatar options
and all three tools with one populated task among fifteen slots, including VTK, result
cards and bottom controls. Earlier audit offscreen evidence remains historical; native
display startup succeeded for implementation validation. Existing intermittent clipping
of Settings navigation/footer text in some captured states is recorded for separate
review; the changed task controls/context/count and confirmation contents remain
readable. Do not label this a blanket acceptance of every pre-existing settings detail.

The frozen `dist/linux` delivery is not republished; current root wheel/source packages
are rebuilt. Native Windows/macOS acceptance remains deferred. Prior reference-manifest
exceptions are historical; reference assets/environment and approved lock remain protected.

Next owner test: restart the app, reopen the workflow project, change Ana's row count
without re-entering retained values, Calculate and main Save. Existing one-row saved
owner data (changed by owner during prior manual reset) is retained as it currently is;
there is no automatic return to an older 15-row snapshot. Owner desktop acceptance is
pending. No unrelated improvement or new milestone is started.
