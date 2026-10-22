# F139 — original-project Open integration

The integrated main Open/recent workflow recognizes an original XML project,
asks for a separate converted-copy destination and then selects an assessment.
The destination alone enters recent history. Cancellation, existing-file and
missing-image failures retain the current workspace and unsaved source edits.
Next: comprehensive integrated copy validation. Full parity percentage and finish
date remain unvalidated.

The stdlib-only ProjectConversion port keeps storage outside presentation;
bootstrap injects LegacyProjectConversion only into the integrated application.
No new toolbar/window redesign or dependency changes. Ordinary new-format Open
keeps its existing behavior. Conversion validates all sources before exclusive
publication; original XML/database/images are never rewritten. Selecting Cancel
after successful conversion leaves the valid copy but does not switch workspaces.
Dirty Save/Discard intent is applied only after assessment selection; dirty Cancel
prevents conversion. Eight focused regressions cover these real workflows.

Native EN/ES actual styled original-file and converted-copy choosers, expanded
assessment selection, cancellation and empty/populated/error main states were
captured. Minimum/enlarged main captures include actual VTK backbuffers. The
extracted-wheel exercises the composed converter and GUI, with separate bounded
native processes for each language. Original cached-result display parity,
plant-transform parity, scientific gates and final application/platform acceptance
remain; see review_register.md. Screenshots: artifacts/desktop-legacy-open/.

Validation: 1086 tests pass; 96.55% coverage. Ruff/format, strict mypy, architecture and builds pass. Extracted-wheel compatibility checks pass. All 500 reference hashes and the dependency lock are unchanged. Open integration changes; see native visual evidence. Evidence: f139_validation.json and artifacts/f139-*.log.

Visual limitation: selected assessment text and chooser/main states are readable; the separate expanded-popup capture is blank/black under this compositor. Its text requires manual visual confirmation. Do not claim full expanded-state acceptance.
