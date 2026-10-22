# M5 accepted — final Linux cleanup and delivery

**6/6 fixed cleanup milestones complete: 100%.** M1, M1R, M2, M3, M4 and M5
are accepted. Owner testing can now begin. No extra milestone, UI redesign,
formula/schema change or dependency change was introduced. This is the fixed Linux
scope; native Windows/macOS acceptance remains deferred by the owner.

## Acceptance criteria and evidence

| Fixed criterion | Result |
|---|---|
| Full regression/standards | 1,282 passed, zero failures/skips in 59.65 seconds; Ruff/format, strict mypy 250 modules, architecture/naming and both documentation gates pass |
| Documentation completeness | 401 reviewed Python/stub files, 2,672 functions including private/nested, 391 classes, 301 constants and two shell entry points; zero pending reviews/gaps |
| Uncovered-path review | All 86 files with 470 missing statements / 452 branch destinations reviewed; 96.25% combined coverage, above the unchanged 90% threshold |
| Independent current package | Approved Python 3.13.14 and 17 exact runtime libraries reused; only the application wheel refreshed without dependencies/downloads |
| Relocated projects | Both native files opened in otherwise isolated folders without original sidecars or converter imports |
| Saved results | All 194 results in each project equal fresh calculation exactly; no duplicate/archive tables |
| Save As/Backup/restore | Four new snapshots match their complete source SQL dumps and all metadata/catalog/history/risk/map/image/rotation data; integrity checks and reopening pass |
| Native desktop/resize | Integrated EN/ES LiFFT/DUET/ST/VTK/PLOT/JROT inspected; main, PLOT and JROT enlarged successfully; 16 actual captures inspected including Recent Projects |
| Solver execution | Real Qt worker threads ran real CBC single-tool and HiGHS two-stage optimization; backend/stages/schedules validated |
| Positional CLI/recency | Installed startup opened a relative spaced filename from another working directory; selection/EN/ES recent menus work; no automatic Save |
| Separate converter | Final delivered external CLI and optional wrapper converted supported original comprehensive projects; no converter inside application wheel |
| Updated delivery | Current wheel/source archive, exact requirement export, install guide, checksums, removable tool/wrapper and two native review projects in dist/linux |

[Full gate](../artifacts/cleanup-m5-check.log), [validation](cleanup_m5_validation.json),
[coverage review](cleanup_m5_coverage_review.md),
[native data/solver evidence](../artifacts/cleanup-m5-native/data_and_solvers.json),
[visual review](../artifacts/cleanup-m5-visual-review.json),
[final package proof](../artifacts/cleanup-m5-packages.json).

The main regression run remains valid for unchanged executable sources. Subsequent
edits correct English/Spanish help/recovery/launch documentation only; 16 focused
Help/resource tests and 77 subtests pass on the final guide content. Final wheel
and source archive are rebuilt after the accepted records are written, then checked
for exact reviewed sources/resources/documentation and converter separation. No
redundant full suite or screenshot cycle is needed for prose-only finalization.

## Ready-to-use projects and launch

From the new project root:

```sh
bash tools/run.sh "test_projects/native/comparative_risk_test.ergprj"
```

Or launch without a project: `bash tools/run.sh`. The second fixture is
`test_projects/native/integrated_test.ergprj`. Use Save As for a personal working
copy. Each has **194 assessments/results and four embedded plant images**; they
contain **seven and five JROT schemes** respectively. Every file is self-contained:
no database/image folders, old schema, original archive or converter is needed.

Both contain 103 complete and 91 partial results. Partial means saved input rows
are unfinished, not that conversion or testing failed. Their single calculated
result preserves calculator precision; labels format it for display. Original files
remain separately preserved in test_projects/originals. The delivered source archive
contains both reference originals and current native fixtures; the independent Linux
folder includes the two ready native files.

For independent installation, follow [Linux delivery](linux_delivery.md) or
`dist/linux/INSTALL.md`. The optional external converter lives in
`tools/project_migration` beside the wheel and is removable. Its documented wrapper
is a generated deployment entry, not code inside the application. The app can use it
when that delivery folder is explicitly added to PATH. No dependency installs occur
inside the wrapper. Native projects remain usable after both tool/wrapper are removed.

## Review limits and deferred work

- No 100% code-path execution claim: all tests pass, combined coverage is 96.25%.
  Remaining error/guard/UI/diagnostic paths and subprocess/thread measurement limits
  are individually recorded. Native solver/CLI evidence supplements that report.
- JROT_EpiSalmonTestStudy01.ergprj retains its unsupported original schema and
  test3.ergprj has blank required metadata. These were already recorded limitations,
  not converted comprehensive fixtures; no new schema repair is authorized.
- Existing original formula and ST selector conventions remain unchanged. This is
  software migration acceptance, not a new scientific validation of the models.
- Spanish long combo/button captions are tight or elided at minimum width, and PLOT
  tabs use overflow scrolling. Record these for later owner UI review; no behavior or
  layout repair was silently added. PLOT screenshot gauges can be mid-animation and
  are not numerical validation evidence; exact stored/evaluated values are checked.
- Linux XCB on the approved host is verified. Windows/macOS native VM tests, new UI
  frameworks and replacing VTK remain outside this completed scope.

All 500 reference files, 27 original copied fixture files, two current native fixtures,
71 original-manifest resources and the approved lock remain unchanged. Current Help
text alone is refreshed within the package; original assets/style remain intact.
There are no pending M5 acceptance criteria or documentation reviews. Owner testing
is now the next activity, not another implementation milestone.
