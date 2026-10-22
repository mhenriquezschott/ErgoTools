# JROT meeting demonstration — October 23, 2026

Load `test_projects/native/jrot_workflow_demo.ergprj`, the new clean native-format-19
project explicitly requested by the owner. It was generated from named synthetic data,
not copied from the comparative project. No schema, calculator or production optimizer
was changed. Other maintained native projects remain untouched.

```bash
bash tools/run.sh "test_projects/native/jrot_workflow_demo.ergprj"
```

Enable **Settings → General → Enable Developer Menu for this session**, Apply, then
**Developer Menu → JROT workflow prototype…**. Developer mode stays off by default on
restart. The prototype never writes any of its inputs, selections, rules or results.

## Suggested meeting walkthrough

1. Keep Yes, six workers, six Jobs and four equal blocks. Day is 06:00–14:00; Evening
   is 14:00–22:00. Choose workplace and shift opens the familiar icon/tree hierarchy;
   select a Plant, Section, Line, or All workplaces. Stations are visible as context.
2. The six real Jobs are selected initially. Job buttons open a searchable tree with
   separate Project, Sample and Entered groups. Sample activity names include S01–S12
   so repeating calculation patterns remain visually distinguishable. Names edited
   here are temporary.
3. The six real workers are selected, with names, sex and age visible. Restrictions
   are **optional**, and their empty list is explicitly labeled. Rule previews remain
   unenforced; do not present the result as satisfying them.
4. Review the current rotation matrix: six workers by four blocks. This starter is
   explicitly simulated, not read from a saved rotation or written as permanent
   worker assignments. Each block uses each of the six Jobs exactly once.
5. Visit task entry. Every real Job has **two populated task rows for each tool** and
   matching calculated totals. No direct-only values, empty calculated sources,
   imported caches or alternate profiles are hidden in this fixture. Optional task
   names remain runtime-only, as agreed; saved task identities are stable.
6. Review baseline Job risks and worker schedule averages separately. Run optimization
   calls real CBC for a selected single tool or two-stage HiGHS for all three. Then
   compare the distributions. The mean remains unchanged for the fixed workload;
   worker maxima/spread can improve. Schedule-cell percentages show the labeled first
   selected tool, while comparison covers all selected tools. Reports stay disabled.

For mixed-data testing, replace one Job with a Sample and another with an Entered
Job, enter that Job's inputs and Calculate each selected tool. This is tested through
real all-three optimization. Missing/skipped inputs remain unavailable, never zero.

All sidebar steps and Back are available for review without completing preceding
steps. Draft selections, matrix cells and task fields survive revisiting pages.
Unready baseline/comparison pages show an explanation instead of blocking navigation
or inventing results. Calculation/optimization still require valid unique selections,
complete staffing and selected-tool values. No branch remains unimplemented; its
larger No button explains that limitation. No Undo/Redo stack was added.

## Project contents

Names are fictional demonstration records, not copies of real personnel. Age uses
birth dates and the application's current date; ages below are as of October 2026.

| ID | Name | Sex | Age | Height (cm) | Weight (kg) |
|---|---|---|---:|---:|---:|
| W01 | Ana Morales | Female | 28 | 164 | 62 |
| W02 | Bruno Reyes | Male | 35 | 178 | 81 |
| W03 | Carla Soto | Female | 43 | 168 | 68 |
| W04 | Diego Navarro | Male | 51 | 175 | 79 |
| W05 | Elena Fuentes | Female | 24 | 160 | 57 |
| W06 | Felipe Rojas | Male | 39 | 182 | 86 |

Six Job definitions: J01 Label inspection, J02 Tray loading, J03 Case packing,
J04 Case sealing, J05 Pallet stacking and J06 Material replenishment. Each owns one
current LiFFT/DUET/ST source/result set. Two tasks per source give 18 calculated
measurements and 36 task rows. Inputs are metric cm/N and repetitions/day; DUET uses
the existing OMNI-RES scale. Established calculators supply the results at full saved
precision. Risks intentionally span low/high workloads rather than all being equal.

Valdivia Foods and Osorno Foods each have Fresh packing and Frozen packing sections.
Each section has Packing Line 1 and Packing Line 2, each with ST01–ST03 scoped under
its full ancestry. Total: two plants, four sections, eight lines, 24 physical stations,
two shifts. The same six packing activities are placed at every line/shift (96 valid
placements, two activities per station), so exploring another branch still offers
six real Jobs. These links do not imply simultaneous physical-station capacity rules.
Job values remain shared by their Job definition, without per-placement overrides.

There are deliberately **no worker assessments, permanent worker assignments, saved
rotation schemes or plant images**. The main assessment grid therefore starts empty;
that is expected. This fixture demonstrates the Job-based JROT workflow. Production
Job/worker workflow acceptance testing remains paused at its earlier bookmark.

## Implementation and cleanup record

Prototype refinements change only `jrot_prototype_dialog.py`, its local widgets and
its basic test. `jrot_prototype_selectors.py` owns two new temporary modal classes:
`PrototypeScopeDialog` (location/shift) and `PrototypeRecordDialog` (Job or worker),
plus `PrototypeRecordChoice` buttons. Both use existing packaged icons and the shared
dialog theme; they borrow detached values and have no writer/history/session capability.
Remove that module and its prototype host calls together when retiring the mockup.
No existing production selector or core workflow was changed for these windows.

`tools/create_jrot_demo_project.py` is a removable developer-only fixture builder.
It calls current public domain/application/native APIs, stages privately, publishes
exclusively and refuses existing targets. It is never imported by the runtime package
and introduces no tables, compatibility decoder, dependencies or backup files.
The new fixture is the only added permanent project, at the established native folder.
Temporary generator/test files are automatically removed; no duplicate fixture folder
or source-file backup exists. The older authorized comparison safety copy remains
historical QA material and can be removed after owner acceptance, as previously noted.

The previous blocker was departure-time validation plus sequential sidebar locks;
validation ran even on Back. Navigation now captures local drafts permissively and
checks readiness only for baseline/optimization. Restrictions were never required.
Duplicate participant selections now report their actual cause when solving, without
preventing review. The precise selections from the owner's earlier step-1.3 failure
were not supplied, so that exact event is not claimed reproduced.

See `jrot_prototype_meeting_validation.json` for final basic native tests, source-review
hashes, exact existing-file checks and visually inspected normal/minimum/empty/partial/
populated states. Linux migration/cleanup stays 100%; this mockup does not constitute
production JROT or Windows/macOS acceptance.


## Final verification

64 focused native cases pass, including all 18 prototype cases. The independent wheel
passes those 18 cases outside the source package; all 331 packaged files match source.
Standards, strict types (279), architecture, naming and substantive documentation
checks pass. Thirty-five native UI states are inspected. The three pre-existing native
projects, dependency files and all production hooks/calculators/optimizer/schema source
bytes remain exact. Fixture integrity and foreign keys pass. Shared table/index
definitions match existing format19 after whitespace normalization. The existing
lazy worker-result table is absent because the new project has no worker results;
no extra table is introduced merely to match a populated comprehensive fixture.
