# Legacy PLOT images and geometry — F132

The comprehensive copied project now maps all four exact plant images, 16 station
anchors and 100 assignment markers, with 191 raw assessment markers and original
plant display metadata retained. Next: saved JROT schemes/provenance, followed by
explicit destination conversion and integrated copied-project validation.

Source mapping: plant_layout.py loadPlantImage uses project ImagesPath/image_name,
not the possibly stale Plant.image_path. This precedence is preserved. Encoded
PNG/JPEG bytes are decoded for integrity without recompression, crop or DPI/unit
conversion. A named missing/corrupt companion blocks complete conversion rather
than silently removing a map. Empty image names remain absent. Nonportable image
names fail explicitly. All four original companion hashes are in f132_legacy_audit.json.

PlotStationPosition and PlotWorkerAssignmentMarker map to the established typed
PlotPositions. Coordinates remain unscaled image pixels, including zero/negative
positions; station ancestry and assignment IDs remain exact. Size/scale/thickness,
locked/visible/enabled flags and position provenance remain independent. Missing
coordinates are allowed only for unplaced markers, enforced by existing domain
rules and source integrity checks. No inferred station anchors or body-unit
conversion occurs. Exact hierarchy/job links are validated before publication.

Old PlotAssessmentMarker records and Plant visual/transform fields remain immutable
raw evidence. They are not silently folded into the newer assignment-owned marker
model. Complete conversion must retain this source metadata alongside its active
map representation; this read projection is not an exporter or a final UI claim.

Focused cases cover exact original PNG bytes, image-name precedence, zero/negative
geometry, closed-owner markers, independent flags, unplaced points, missing/corrupt
companions, invalid paths and malformed geometry. Copied comprehensive and isolated
wheel checks validate all images/positions/owner links without source writes.
No Qt view or dependency changed; no new visual acceptance claim is made.
The ST direction choice remains pending while independent compatibility continues.
Overall percentage and finish date remain unvalidated.

Validation: 1039 tests pass; 96.70% coverage. Ruff/format, strict mypy, architecture and builds pass. Extracted-wheel compatibility checks pass. All 500 reference hashes and the dependency lock are unchanged. No UI change. Evidence: f132_validation.json and artifacts/f132-*.log.
