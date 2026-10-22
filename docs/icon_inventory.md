# Processed icon inventory — owner acceptance follow-up

Only packaged processed assets are reused. No system icon set, new artwork or
resource dependency was introduced. Alphabet/mode toggles and recent filenames
remain text controls intentionally. Future dedicated icons are supplied by the owner.

| Action/location | Current reused asset | Dedicated asset still wanted |
|---|---|---|
| New assessment | new.png | Assessment variant |
| Set current assessment / risk profile | filter_apply.png | set_current.png |
| Approve Job risk profile | filter_apply.png | approve.png |
| Retire Job risk profile | None; text remains clear | retire.png |
| Redo in main, PLOT and JROT | redo.png; saved horizontal mirror of undo.png | None |
| Project Properties | view.png | project_properties.png |
| About | help.png | about.png |
| User Guide | help.png | Optional user_guide.png |
| Save As / saved backup | save.png | Optional save_as.png / backup.png |
| Close project / Properties / saved-data dialog | close.png | None |
| Settings menu | settings.png | None |
| Animated body-region focus | body_view.png | None |
| Clear recent history / JROT Clear Cell | delete.png | None |
| Load saved assessment data | open.png | None |
| Selection-dialog Select / Cancel | filter_apply.png / cancel.png | None |
| Graph Settings Apply | filter_apply_light.png | None |

The standalone task-count diagnostic dialog is no longer a product entry point;
the unified settings form has processed Cancel/Settings assets. No wrong-direction
Undo icon is substituted for Redo, and Retire is not represented as Delete.
New owner assets must be normalized for transparent background, crop, canvas and
padding, use snake_case names, enter the resource manifest and pass visual review.


## Static Redo asset accepted

The owner authorized a static horizontal mirror of the processed Undo icon.
icons/redo.png preserves its canvas, padding and transparency; runtime code loads it
normally and performs no image transformation. Its provenance/hash are recorded under
derived_assets in the resource manifest; the 71 copied reference entries remain intact.
Redo now appears in main/PLOT/JROT toolbars and Edit menus. Retire remains the required
missing dedicated icon; the optional action-specific variants above remain optional.
