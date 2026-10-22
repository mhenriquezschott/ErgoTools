# Current JROT meeting project — 2026-10-21

`jrot_workflow_demo.ergprj` (under `native/` from the parent directory) is the owner's
explicitly requested clean format-19 example: six named/demographic workers, six Jobs,
18 calculated source/result sets with 36 task rows, two plants, four sections, eight
lines, 24 stations and two shifts. No worker assessments or saved rotations are seeded.
Use it with Developer Menu → JROT workflow prototype…. See docs/jrot_meeting_demo.md
for the walkthrough, shared placement meanings, fixture provenance and cleanup notes.
It is one new demonstration project; existing fixtures are unchanged. Descriptions of
older formats/profile storage below are historical, not the current schema contract.

---

# Self-contained test projects — M1R/M2

These are format-18 single-file projects with all plant images embedded and one
calculated result per assessment. No original folders or converter are
needed to open them. They are reference test fixtures; use Save As for experiments.
Cleanup M4/M5 are accepted; these fixtures are ready for owner acceptance testing.

| Native project | Assessments/results | Plant images | JROT schemes |
|---|---:|---:|---:|
| native/comparative_risk_test.ergprj | 194 | 4 | 7 |
| native/integrated_test.ergprj | 194 | 4 | 5 |

From the project root:

```sh
bash tools/run.sh "test_projects/native/comparative_risk_test.ergprj"
```

Original inputs remain read-only in the reference checkout's tests directory.
Byte-identical descriptors/database/image folders are also preserved separately
in `originals/`; keep their companion paths intact. They are reference evidence,
not application runtime assets. Both originals and native fixtures ship in the
source archive; only application resources ship in the wheel.
Source/output hashes and conversion counts are recorded in
`artifacts/cleanup-m1r-projects.json`; all values are checked in the package and
original-calculator acceptance reports. Each file has 91 partial and 103 complete
calculations: partial identifies unfinished grid inputs, not conversion failure.

Two additional original samples were checked but are not regenerated fixtures:
`JROT_EpiSalmonTestStudy01.ergprj` uses an unsupported original schema;
`test3.ergprj` has blank required metadata. Neither was previously a supported
comprehensive converted fixture. No source repair or broader schema support is
authorized by M1R. See the review register; M2 organization/guidance is accepted.

In each supported project, 29 original ST cached totals disagree with recalculation
by more than four-place rounding. M1R stores the result recomputed from the saved
inputs, verified against the original calculator code. No formula changes or hidden
second original result is involved. Earlier artifacts are historical evidence;
these native fixtures supersede them for subsequent workflow tests.

M2 relocation checks opened only each native file in an otherwise empty temporary
folder and compared every source/result, hierarchy, worker/job ownership, authored
risk profile, plant image/marker and rotation scheme with the fixture. No sidecars
were copied. See `artifacts/cleanup-m2-fixtures.json` for all original copy hashes
and native evidence. Main Open/CLI project launch uses native data directly; GUI
conversion of an original instead opens an unsaved copy requiring first Save.
