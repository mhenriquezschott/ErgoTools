# Superseded by owner-requested restoration — 2026-10-20

The owner rejected the uniform widths as too wide and requested the previous sizing.
The exact previous source/tests are restored; see toolbar_restore_acceptance.md and
current STATUS. The original validation below is historical, not the current UI.

---

# Main-toolbar button sizing — verified, 2026-10-20

Owner requested matching top-bar button sizes because Jobs looked narrow beside
Organization. All nine visible toolbar actions now use the widest translated native
button size hint as their shared width. The established 75 logical-pixel height and
38×38 icon box remain. Current native geometry is 94×75 in English and 95×75 in Spanish;
font/style metrics determine the width rather than a hardcoded language guess. Actions,
shortcuts, enablement, tooltips, icons, shared Undo/Redo and project behavior are unchanged.

This replaces the one-off Organization minimum-width exception. The existing English/
Spanish navigation regression now checks equal button dimensions, full native size hints
and containment after language changes. No new test module, dependency, schema, data,
calculation or reference change is introduced. Both changed maintained files were
substantively reviewed and their documentation hashes explicitly renewed.

Required native Linux XCB `bash tools/check.sh`: **1,984 passed, zero failures/skips,
94.33% coverage**; Ruff/format 708 files, strict typing 273 source files, architecture,
naming, documentation structure/reviews and wheel/source builds pass. Focused source
navigation tests: 12 passed. Current wheel extracted outside source: 12 native navigation
tests pass; packaged Python/resource bytes match source. Prior Job/PLOT/JROT acceptance
is reused for unchanged behavior rather than repeating its independent 181-test run.

Eight native captures inspected: full main window and header, EN/ES, with no project
and with a private copy of the workflow project loaded. Every top-bar action/caption
fits; the header stays within the existing 1550×1015 window. VTK was omitted only for
this toolbar inspection; its code and accepted renderer evidence are unchanged.
All three maintained native fixture hashes and uv.lock remain exact.

See [validation](toolbar_uniform_size_validation.json),
[gate log](../artifacts/toolbar_uniform_size/full_gate.log),
[geometry](../artifacts/toolbar_uniform_size/native_geometry.json) and
[review hashes](../artifacts/toolbar_uniform_size/reviewed_files.json).

The separate [JROT wireframe review](jrot_wireframe_review.md) is analysis only.
Its [16 team questions](jrot_wireframe_team_questions.md) identify future design/model
choices; no JROT redesign follows from the attachments. The owner confirmed the empty
Job window in workflow_4_workers.ergprj. Job UI and earlier worker/workplace testing
remain paused at [their bookmark](workflow_testing_pause.md). Linux migration/cleanup
remains 100%; Windows/macOS acceptance stays deferred.
