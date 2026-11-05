# Test projects

The four files under `native/` use current native format 24. Each is a self-contained
SQLite `.ergprj`, including its available plant images, tasks and saved results. Use Save
As or a private file copy for experiments. No original database/image folder or converter
is needed to open these files.

| Project | Workers | Jobs | Worker assessments | Saved JROT schemes | Purpose |
|---|---:|---:|---:|---:|---|
| native/workflow_4_workers.ergprj | 7 | 10 | 12 | 34 | Original workflow records plus known-answer restriction/timing cases |
| native/jrot_workflow_demo.ergprj | 6 | 6 | 0 | 0 | Clean guided-JROT demonstration with calculated Job sources and realistic organization |
| native/comparative_risk_test.ergprj | 28 | 12 | 194 | 7 | Broad PLOT and production JROT integration |
| native/integrated_test.ergprj | 28 | 12 | 194 | 5 | Broad integrated workflows and project compatibility |

The guided-workflow example has six calculated Jobs with all three tool sources, two
Plants, four Sections, eight Lines, 24 Stations and two Shifts. Use Tools → JROT for the current persistent guided workflow.
The former disposable developer prototype has been retired.

```sh
bash tools/run.sh "test_projects/native/jrot_workflow_demo.ergprj"
```

The comprehensive fixtures retain original calculation status, including incomplete
sources; missing risk is never an invented zero. Current calculations ignore unused blank
rows but require started rows to be complete. Source units and recorded ST conventions
remain explicit. The original-to-native conversion recalculated obsolete original outputs
using the established formulas rather than retaining a second cached result archive.

Original descriptors/database/image folders are preserved separately under `originals/`;
keep their companion paths intact. They are compatibility inputs, not runtime assets.
The source archive includes fixtures; the application wheel contains application resources
only. Unsupported original schemas or invalid required metadata are reported by conversion,
not silently repaired.

The format-20 upgrade adds only an empty reusable task-name catalog to format-19 fixtures;
existing values, results, images, relationships and rotation schemes remain exact.

The native 21 upgrade added an empty optional Shift timing catalog. No existing rotation is
assigned times or breaks automatically; native 20 baseline backups are retained locally
through owner review. Production JROT behavior is unchanged by this storage capability.

The native21→23 scenario-capability upgrade changes only the marker; existing table values,
legacy rotation payloads/timestamps and timing templates remain exact. Dates/times/run
evidence are not invented for older schemes. New scenario composition follows separately.

The workflow fixture retains its historical filename. Three additional reference workers
and Jobs support [four-block restriction examples](../docs/jrot_four_block_examples.md).
Twenty-four of its 34 rotations have kept results at this checkpoint. Three additional
0/5/55% Jobs support the [six-block adjacency comparisons](../docs/jrot_adjacency_examples.md).

Demo 15–20 provides [larger fixed/excluded/timing comparisons](../docs/jrot_rule_timing_examples.md).
