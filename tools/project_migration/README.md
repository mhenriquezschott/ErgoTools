# Optional project migration utility

This directory is separate from `src/ergotools` and excluded from the application
wheel. It can be distributed beside the application and removed later. Use the
approved interpreter with ErgoTools installed/importable; no additional dependency
or version change is required.

```sh
.venv/bin/python tools/project_migration/migrate_project.py "/path/original.ergprj" --output "/path/native.ergprj"
```

Both paths may contain spaces. An absolute script path works from any directory;
relative input/output paths resolve from that working directory. The output must
not exist. The destination directory must exist and support exclusive hard-link
publication. Original files remain untouched. Keep original XML descriptors and
all their database/image sidecars together until conversion completes.

## Current input and output contract

Inputs are supported original version-eight XML projects with sidecars, or earlier
full native formats 8–17. Output is one self-contained **format-18** `.ergprj` with
embedded plant images, direct worker assessment ownership, optional workplace links,
PLOT geometry, Jobs/risk profiles and JROT schemes. Each assessment has one source
and one matching calculated result when evaluable. There are no alternate individual
assessment versions, duplicate results or original-database archives in the output.

Format-14/15/16/17 upgrades preserve real source/result payloads and all unrelated
rows, including JROT timestamps, exactly. The catalog upgrade removes the obsolete
Shift incident/event attributes, six owner-rejected Station fields and the redundant
editable Plant shift count. Retained dates/durations must satisfy the current typed
contract; invalid values stop instead of being inferred or rounded. Worker identity
is derived from the original assignment; organization named Default remains genuine
data and is retained. Earlier rounded or obsolete result envelopes are recalculated
from saved inputs using the unchanged approved formulas, units and ST direction
convention. Intrinsic model rounding remains; UI display formatting does not reduce
stored precision. Approved Job risk profiles and their necessary original versions
remain independent.

A proven empty duplicate old LiFFT draft may be removed under the documented rule.
Competing populated duplicate assessments stop conversion for an explicit decision;
the tool never chooses real data to discard. Missing assets, unsupported schemas,
invalid ownership or metadata are reported instead of inventing values or defaults.
Partial calculations retain their explicit status; missing risk is never zero risk.

Current format-18 files need neither the converter nor original folders. Maintained
test projects are updated in place at `test_projects/native`; no parallel fixture
folder or automatic backups are created. See
[ownership, schema and rollback](../../docs/optional_assessment_context.md).

## Desktop integration and errors

Open offers Migrate/Cancel and terminal guidance for old user projects. An external
subprocess writes application-owned temporary native backing. The app validates it
and asks for first Save to choose the permanent project file. Temporary locations
never enter Recent Projects; cancellation/failure retains the current workspace.
CLI users publish directly to their explicit `--output` destination.

Successful stdout is JSON with path, format and record counts (exit 0). Conversion
errors are JSON on stderr (exit 1); invalid CLI syntax exits 2. An already published
valid output may remain if final reopening fails; inspect it before retrying.

If separately provided on PATH, `ergotools-migrate` takes precedence over the source
script. The wheel installs neither that command nor this directory. Removing the
utility does not affect current native projects; old-project conversion then reports
that the external tool is unavailable. No runtime legacy mode is used.

Format 18 also removes the six owner-rejected Station attributes and the editable
Plant number_of_shifts cache. Remaining opening/creation dates require canonical
ISO dates; daily operational_hours remains decimal hours, 0–24 in whole minutes.
Invalid retained values stop conversion; no silent date inference or rounding.
Plant shift usage count is a live UI projection of active Jobs/worker assignments,
with no new relationship/table.
