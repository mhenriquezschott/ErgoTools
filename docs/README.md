# Documentation

Start with the maintained guides below. They describe the integrated desktop application,
its current native format and its supported extension boundaries.

| Audience | Guide |
|---|---|
| Users | [English user guide](user_guide.md) · [Guía en español](user_guide_es.md) |
| Installation | [Linux, Windows and macOS setup](installation.md) · [Recovery](recovery.md) · [Installation / GitHub PDF](guides/ergotools_installation_and_github_guide.pdf) · [Copyable commands](guides/installation_commands.md) · [Capture checklist](guides/desktop_capture_checklist.md) |
| Developers | [Architecture](architecture.md) · [API contracts](api_contracts.md) · [Development](development.md) · [Coding standards](coding_standards.md) |
| Data model | [Current native tables](database_tables.md) · [Shared project Save/history](single_project_save.md) · [Shift timing](rotation_timing.md) · [Rotation scenarios](rotation_scenarios.md) · [JROT guided entry](jrot_guided_entry.md) · [Weighted planning and restrictions](jrot_planning.md) · [Comparisons and rework](jrot_comparisons.md) |
| Assessments | [Ownership and navigation](assessment_context.md) · [Transfer](assessment_transfer.md) · [Task counts](task_count_integration.md) · [Reusable names](user_guide.md#reusable-task-names) · [Import / paste](assessment_import.md) |
| Jobs | [Job Management](job_management.md) · [Workers](worker_management.md) · [Organization](organization_management.md) |
| Shared widgets | [Assessment editor](shared_assessment_editor.md) · [Task column visibility](task_column_visibility.md) · [Saved-assessment search](saved_tool_data.md) |
| PLOT | [Map controls](plot_map_controls.md) · [Marker rendering](plot_marker_rendering.md) · [Worker selection](plot_worker_search.md) · [Job view](plot_job_overview.md) |
| Scientific models | [LiFFT](lifft_calculation.md) · [DUET](duet_calculation.md) · [Shoulder Tool](tst_calculation.md) |
| Images | [Screenshot conventions](images/README.md) |

Other component documents retain implementation provenance and characterization evidence.
Sections explicitly labeled historical, or headed with an F/M checkpoint identifier,
describe that checkpoint; their test counts, temporary launchers and future-work lists
are not the current release status. Use the current guides above for workflows and APIs.
Scientific equations and reference comparisons remain relevant where the model is unchanged.
Experimental design discussions and personal development notes are kept outside the public
documentation; the public overview describes the production JROT interface.

[Restriction examples and expected answers](jrot_restriction_examples.md) explain the
prepared test rotations, independent optimizer checks and synthetic reference values.

[Four-block constraint demonstrations](jrot_four_block_examples.md) cover equal and
very unequal durations with exact known answers. [Icon inventory](icon_inventory.md)
lists supplied icons and the complete dedicated-artwork backlog.

[Consecutive High at the optimum](jrot_adjacency_examples.md) explains Demo 11–14
and the equal/unequal comparisons with independently proven results.

[Four-worker rule and timing pairs](jrot_rule_timing_examples.md) compare excluded Jobs,
fixed Jobs and equal/unequal durations using eight blocks and independently proven optima.

[HiGHS optimization](highs_only.md) describes the current solver runtime, objectives
and compatibility with previously recorded results.

[Visual Settings and display diagnostics](settings_previews_and_diagnostics.md) explains
live appearance examples and collecting reports for desktop deployment tests.
