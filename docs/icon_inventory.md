# Desktop action and workflow icons

Current interfaces reuse packaged processed assets and small native Qt vector actions.
No external icon font or system-theme dependency is required. Original assets retain
their manifest/provenance; generated action icons use the application palette.

| Location | Current icon |
|---|---|
| JROT 01 Rotation setup | Shift |
| JROT 02 Jobs | Job |
| JROT 03 Workers | Worker management |
| JROT 04 Current assignments | Rotation/worker assignment |
| JROT 05 Tasks & validation | Calculator |
| JROT 06 Review inputs | View |
| JROT 07 Optimization | Existing all-tools optimization |
| JROT 08 Comparison & report | Comparison |
| Task + / − | Native vector task sheet with plus/minus |
| Copy / Paste / Import settings | Native vector overlapping sheets / clipboard / import arrow |
| Drawer pin / unpin | Icon-only native vector pushpin at the heading’s top right |
| Drawer notch | Full-height navy rail; handle moves with its right edge, opens on hover/click |
| Undo / Redo | Packaged undo.png / redo.png |
| Project Properties / About / Help | Existing view.png / help.png |
| Save As / backup | Existing save.png |

The drawer tints its copied step icons white for the navy background; source files are
not rewritten. Selected, hovered and keyboard-focused steps have distinct treatments.
All eight steps have icons; there are no missing required runtime assets.

Timing Select, Split, Draw break, Move/resize, Join and Remove now have native vector
icons. Work/break editing has no required missing icon assets.

## Designer artwork installed — 2026-11-04

All 41 supplied designer icons are installed and bound to their existing actions.
There are no outstanding dedicated-artwork requests from the I01–I41 list.
The package contains 145 PNG icons, including 41 designer ordinary/light pairs; existing
native task +/- and timing cursor icons remain in use.

| Previous ID | Action | Packaged filename |
|---|---|---|
| I01 | Worker restrictions | `worker_restrictions.png` |
| I02 | Fixed job | `fixed_job.png` |
| I03 | Excluded jobs | `excluded_jobs.png` |
| I04 | No adjacent high | `no_adjacent_high.png` |
| I05 | Previous rotation result | `previous_rotation_result.png` |
| I06 | Following rotation result | `following_rotation_result.png` |
| I07 | Clear result link | `clear_result_link.png` |
| I08 | Generate proposal | `generate_proposal.png` |
| I09 | Keep optimization result | `keep_optimization_result.png` |
| I10 | Rework rotation | `rework_rotation.png` |
| I11 | Duplicate rotation | `duplicate_rotation.png` |
| I12 | Replace baseline | `replace_baseline.png` |
| I13 | Task names | `task_names.png` |
| I14 | Add work block | `add_work_block.png` |
| I15 | Remove work block | `remove_work_block.png` |
| I16 | Add break | `add_break.png` |
| I17 | Remove break | `remove_break.png` |
| I18 | Equal work blocks | `equal_work_blocks.png` |
| I19 | Unequal work blocks | `unequal_work_blocks.png` |
| I20 | Equal breaks | `equal_breaks.png` |
| I21 | Unequal breaks | `unequal_breaks.png` |
| I22 | Apply timing | `apply_timing.png` |
| I23 | Select cell range | `select_cell_range.png` |
| I24 | Worksheet | `worksheet.png` |
| I25 | Validate import | `validate_import.png` |
| I26 | Remove empty rows | `remove_empty_rows.png` |
| I27 | Column mapping | `column_mapping.png` |
| I28 | Task columns | `task_columns.png` |
| I29 | Project properties | `project_properties.png` |
| I30 | About | `about.png` |
| I31 | Save as | `save_as.png` |
| I32 | Project backup | `project_backup.png` |

Each icon uses a transparent 96×96 canvas with visible artwork contained within 80×80.
White matte removal decontaminates the edge colors; the final resized alpha bounds are
centered again to avoid faint source fringes shifting the visible glyph. Artwork and
navy/teal/red semantics are preserved. `_light` variants retain exactly the same alpha.
The asset manifest records source filename/hash, original size, crop and processed hash.
Original designer files in `tmp/icons` are never changed or read at runtime.

Buttons use icons beside descriptive text: 26–28 px for ordinary actions, 32 px for
adding/removing timing segments, 40 px for Use timing, and 48 px for the detailed timing
mode diagrams. Their existing horizontal arrangement fits both timing tables without
adding a second row of square tiles. Header icons use 28 px. Compact menu icons follow
Qt's menu sizing. Existing icon-only controls retain their tooltips.

`python -m tools.normalize_designer_icons SOURCE DESTINATION --manifest MANIFEST`
reproduces these assets with the existing approved Pillow/NumPy dependencies. The
runtime loads only packaged assets through composition; shared editors/import dialogs
receive the same mapping, including the import panel embedded in Settings.

Audit sources: bootstrap, AssessmentMenu, shared AssessmentTaskGrid/ImportPanel,
PreferencesDialog, TaskNameDialog, RotationTimingDialog and JROT dialog/planning/
comparison/restriction/neighbor controls. Retired profile/evidence controls do not return.

## Complete workflow action audit — 2026-11-04

Existing artwork is now bound consistently to Import file/range/clipboard/update/
validation/inclusion/Cancel/Paste; JROT New/Duplicate/Delete, Back/Continue/Close;
01 scope/organization/create/timing/Yes/No; 02 Job selection/management; 03 worker
selection/management/restrictions/neighbors; 04 generate/clear assignments; 05 input
modes/copy/task actions; 07 solve/cancel/discard/keep; 08 keep/rework/replace/report;
and timing Clear/Close. Page headings reuse the drawer's same step glyphs, tinted
navy for light backgrounds. Tool matrices retain the real tool icons/full titles.
State checkboxes, alphabet letters and standard disclosure arrows remain native
controls, rather than receiving decorative action icons.

Step 08 uses 44px artwork above captions on 82px-tall result actions. Ordinary JROT
commands use 28px beside text; Run/Keep use 36px. Import uses 28px actions, a compact
Preview actions group and a separate status area beside Cancel/Paste. Existing
window/data ownership and callback semantics are retained.

### Additional dedicated artwork installed — 2026-11-04

All nine follow-up designs are now installed. These replace temporary generic icons;
they introduce no new action or data behavior. There are no remaining artwork gaps
from the audited I01–I41 list.

| ID | Title | Packaged filename | Bound control |
|---|---|---|---|
| I33 | Include selected rows | `include_rows.png` | Shared import preview, including Settings |
| I34 | Skip selected rows | `skip_rows.png` | Shared import preview, including Settings |
| I35 | Include all rows | `include_all_rows.png` | Shared import preview, including Settings |
| I36 | Task inputs | `task_inputs.png` | Jobs and guided JROT input mode |
| I37 | Direct result entry | `direct_result.png` | Jobs and guided JROT input mode |
| I38 | Clear starting assignments | `clear_assignments.png` | JROT step 04 Clear assignments |
| I39 | Discard optimization preview | `discard_preview.png` | JROT step 07 Discard preview |
| I40 | Clear timing | `clear_timing.png` | Shift template/rotation timing Clear |
| I41 | Edit rotation timing | `edit_timing.png` | JROT step 01 Edit rotation timing |

The same normalization policy generates all 41 pairs: 96px transparent canvas,
centered artwork within 80px, preserved foreground colors and exact-alpha white
variants. The 32 earlier pairs and all 41 designer originals remain byte-identical.
New controls retain the established sizes: 24px mode icons, 28px import/JROT commands
and 32px timing Clear. No callback, tooltip, layout dimension or persistence changed.
Source/crop/output provenance is in the packaged manifest. Native EN/ES evidence and
verification are recorded under `artifacts/remaining_icons`.
