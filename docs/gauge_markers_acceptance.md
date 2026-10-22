# Configurable assessment-gauge markers — 2026-10-17

Owner requested boundary-number labels and evenly spaced unlabeled ticks on the
existing gauge, with configurable visibility/interval. Owner selected both a
right-click menu and the existing Settings window for controls.

## Behavior and architecture

The main assessment gauge now defaults to ticks every five probability percentage
points and labels at its existing 0, 25, 37.5, 50 and 100 risk limits. Off-grid limits
remain exact, deduplicated and visibly distinct. Show tick marks and Show risk-range
limits are independent; disable both to return to the original unannotated drawing.
Right-click offers 5/10/20/25 presets and a custom integer interval from 1 to 100.
Tools > Settings > Assessment gauge markers offers the same flags and spacing.
Right-click applies/saves immediately; Settings applies on Apply and Cancel retains
current options. Changes survive restart. Spanish captions and comma boundary labels
are supported. These percentage annotations apply equally to metric/imperial sources.

GaugeMarkerSettings is an immutable validated application preference contract with
no Qt/storage imports. UserSettings owns it; JsonSettingsStore writes personal
settings format 5. Versions 1-4 load read-only with default markers, retaining prior
language, units, recency, contexts and animation choice; writes remain atomic.
Project schema remains 16; no database table/column or assessment data changes.
The rendering helper consumes existing presentation band limits and restores the
borrowed painter state. The existing host persists menu requests before applying
appearance, with its existing error boundary. Failed writes retain prior options.
Settings retains its existing source/input-resolution and project-display policy.

Existing arc dimensions, palette, needle, value formatting, calculations, units,
clamping/animation implementation, DamageScale and PLOT gauges are unchanged.
Both maintained native test fixtures stay at their established paths and their
bytes match this session's handoff. Reference and approved lock remain untouched.
No dependency, new milestone, renderer change or speculative project storage.

## Evidence

Final native XCB gate: **1,369 passed, zero failures/skips, 95.47% coverage**.
Ruff/format, strict types (261), architecture/naming, documentation (421 files),
review inventory and wheel/sdist builds pass. All eight changed packaged modules
and both HTML guides match the rebuilt wheel bytes; twelve code/test files have
current semantic reviews. Final gate results are recorded in artifacts/gauge_markers_validation.json and
artifacts/gauge_markers_final_check.log (paths relative to the project root).
Focused regression details are in artifacts/gauge_markers_focused.log and the
post-localization custom-dialog check in gauge_markers_custom_tests.log.
The independently reviewed contracts/hashes are in
artifacts/gauge_markers_documentation_review.json; the maintained review map and
symbol inventory are current. Both Markdown and packaged bilingual guides explain
control access, saving/cancellation and the main-gauge scope.

Native visual record: artifacts/gauge_markers_review/validation.json, 22 inspected
EN/ES captures plus an offscreen control-comparison diagnostic. Main LiFFT/DUET/ST,
metric/imperial, 5/10/hidden options, both menus, custom input and empty/populated
Settings fit in the checked dimensions. Native preference restart and fixture hash
preservation pass. The custom dialog's initially untranslated native Cancel button
was explicitly localized and rechecked before the final gate. Earlier standard
checks and focused regressions are not substituted for the final current-code gate.

## Separate inherited animation issue

The original _AnimatedScale can fail to interpolate when a float start and integer
end reach Qt; a 100.0 target also triggers this because the existing clamp chooses
the integer upper limit. The isolated endpoint probe retained its previous number
and needle despite target_value=100. This behavior is not visually accepted, and
no repair is included in marker work. _AnimatedScale and DamageScale ASTs match the
pre-change wheel; see artifacts/gauge_markers_original_controls.json and the review
register. Exact scientific result/source storage remains separate. Owner direction
is needed before a bounded animation correction.

Next: restart ErgoTools and compare intervals/visibility using right-click or
Settings. Migration/cleanup remain historically complete at 100%; no owner testing
of this new appearance is claimed yet. Native Windows/macOS acceptance stays deferred.
