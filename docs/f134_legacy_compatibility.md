# F134 — complete destination creation and exclusive publication

Complete typed snapshots now create a validated new-format project through a
hidden same-directory file and exclusive publication. Original approved/retired
profiles, historical ownership, PLOT images/positions and saved rotation links
survive exact read-back and reopen. Next: retain complete original XML/database
and image-name evidence; ST direction choice remains required before full source
conversion. Overall completion percentage and finish date remain unvalidated.

The creation-only risk/history initializers require empty stores and an existing
owner transaction. They cannot replace populated catalogs or silently approve,
retire or promote historical records. Full snapshot validation precedes disk
creation; each source/image is encoded/decoded before any destination exists.
Hidden-file writes commit, reopen, and compare all metadata/catalogs/sources/maps/
rotations before hard-link publication. Existing destinations, racing writers and
unsupported hard-link filesystems receive errors without overwrite fallbacks.
Failed initialization or verification removes only the hidden candidate. A valid
published file survives a final reopen failure; power-loss durability is not
certified.

Thirteen focused regressions cover exact historical round-trip and backup,
invalid model/project/image/rotation inputs, existing destinations, mid-write
failure, corrupted read-back, publication races, unsupported hard links, final
open failure, and protection of already initialized risk/history records.

The extracted wheel creates and reopens an explicitly titled **LiFFT/DUET
validation subset** from a comprehensive project copy: 138 assessments/2,790 rows,
all organization/jobs/assignments/19 risk profiles, four maps, 16 anchors, 100
markers and seven schemes. This deliberately isolated acceptance test does not
claim full legacy conversion: 56 ST sources still require the owner's direction
choice and complete raw-source evidence must be persisted. No scientific model,
GUI, reference data or dependency change.

Validation: 1059 tests pass; 96.62% coverage. Ruff/format, strict mypy, architecture and builds pass. Extracted-wheel compatibility checks pass. All 500 reference hashes and the dependency lock are unchanged. No UI change. Evidence: f134_validation.json and artifacts/f134-*.log.
