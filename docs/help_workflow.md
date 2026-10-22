# Current Help target — M11

Help opens the packaged current EN/ES HTML guide. The PDF workflow below is
a historical implementation record, superseded by the M11 section at the end.
See [current user guide](user_guide.md) and [Spanish guide](user_guide_es.md).

---

# F93 — original Help workflow

Help > User Guide and the original Help toolbar action now open the existing
`assets/reference_manual.pdf`. Help > About opens the original Authors dialog: exact
English credits and linked source attribution, original logo, white background,
600 by 700 dimensions and window-close interaction. A new owned dialog is created
on every open, avoiding the reference method's repeated layout installation on a
reused dialog. No controls or project state are changed by Help. It remains
available with no project open, and invalid pending assessment input is preserved.

The manual and authors logo are unchanged byte copies from the reference and are
included in the package resource manifest. Bootstrap reads and injects them; the
presentation layer never reaches into the reference tree or infrastructure.
The desktop launcher uses Qt's platform cache directory, QSaveFile for complete
atomic publication, and QDesktopServices with a local-file URL. There are no shell
commands, platform-specific subprocesses or dependency changes. The cache is
persistent because the external viewer may read the PDF after the call returns;
it contains the original manual only, never project data. A failed cache write or
rejected viewer request reports an owned localized error and retains the editor.

English/Spanish Help menu labels, tooltips, error messages and Authors title are
localized. The original English PDF and credits body are retained; translated
manual/credits and stock Qt wording remain part of the full-language review.
The original View command controls animated body-region camera focus. It remains
pending the documented renderer animation/preferences step rather than being
connected to an unrelated Rotate/Zoom action. PLOT/JROT remain disabled until
those workflows are migrated.

Six focused cases verify Help menu/toolbar and repeated modal About on each of
LiFFT/DUET/ST, unchanged pending/source/settings, owned cache/viewer failures and
incomplete-write rejection. Required gates pass: 725 tests, 96.33% combined
coverage, lint/format, strict mypy on 150 source files, architecture and both builds.
An isolated extracted wheel verifies manual/logo hashes, complete cached PDF bytes,
launcher requests, repeated owned About, all three tools, failure handling,
no-project availability and native VTK cleanup. All 500 reference file hashes and
the approved lock are unchanged.

Native captures in `artifacts/help-workflow/` compare the reviewed original About
builder and migrated form on the same platform/baseline at 600 by 700. Original
builder execution used only its extracted method and read-only logo; no reference
imports, writes or operational data were used. English/Spanish menu states,
owned About, error and populated/empty integrated layouts were inspected. Native
VTK, result cards, labels and bottom controls remain visible at 1550 by 1015.
The actual desktop PDF viewer was not launched by automated verification: the
platform request was controlled, with exact emitted file bytes checked. A manual
platform acceptance check still needs to open the viewer and follow the credits
link. This does not claim final Windows/macOS or whole-application parity.

Evidence: `f93_validation.json`, `artifacts/f93-check.log`, archived
`reference/f93-capture.py.txt` and `reference/f93-verify.py.txt`.
Next: complete application preference/localization and decimal-convention
persistence. Renderer View animation, original project details/sidecars,
scientific gates, PLOT/JROT, legacy import and final copied-project/platform
acceptance remain. No validated overall percentage or finish date is available.


## M11 supersedes the historical-manual target

Help now opens the package-owned current EN/ES HTML user guide through the same
atomic Qt cache/default-viewer mechanism and unchanged menu/toolbar controls.
It follows the current language without committing pending input. The unchanged
reference PDF remains a separately packaged historical asset; old claims that it
is the current user guide are superseded. No network assets/documentation framework
or dependency was added. See user_guide.md, user_guide_es.md and recovery.md.
