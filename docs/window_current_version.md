> Historical checkpoint, superseded by the owner-directed removal of assessment versions.
> See [current ownership contract](single_assessment_ownership.md). The version UI/API described below no longer exists.

# LiFFT current-version controls — F54

The temporary LiFFT window exposes Set current version for historical projects.
The picker lists numeric versions from the open assessment's exact assignment/model
group. Its prompt explains that the open assessment and unsaved edits stay unchanged.
The action uses workspace history authority and atomic expected-value comparison;
a source change or history refresh during the picker rejects the callback.

The source label now displays the open assessment's version and Current/Not current
state. Unbound sources explicitly show No assignment link. After choosing another
current version the existing editor stays open, including dirty source and undo.
Results are refreshed by the existing rendering path; source data is not saved.
Pending widget text still requires the existing Apply/Discard controls first.
Historical capability gates the action; older/default project formats are unchanged.

Labels and prompts are English/Spanish. The text-only action follows existing
text-only task controls and needs no new icon. Palette, spacing and picker styling
are reused. Native XCB inspection covered empty/current/pending/noncurrent-dirty
windows, Spanish at 960 x 680, the version picker and expanded choices. Complete
result panels, labels and bottom controls fit without visible clipping. There is
no VTK model in the temporary window. Capture script and screenshot hashes are
archived in docs/reference/f54-capture.py.txt and f54_validation.json.

Two new desktop scenarios test pending protection, preserved dirty/undo state,
unchanged saved source, visible noncurrent status, cancel, stale history/source
callbacks and unbound sources. All 471 tests pass; total coverage 98.93%.
Ruff/format, strict mypy (101 files), architecture, builds and an isolated-wheel
version-control smoke pass. All 500 reference files and the dependency lock remain
unchanged. No schema, dependency or scientific formula change occurred.

This exposes the explicit version operation added in F52; it is not evidence of
a captured equivalent reference UI action. The preview remains temporary and
LiFFT-only. Historical version creation controls, complete worker/job workflows,
legacy import and the final integrated UI remain pending. Displayed version status
refreshes on window refresh/actions, not through live external database notifications.
