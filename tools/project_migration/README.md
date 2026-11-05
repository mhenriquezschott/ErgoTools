# Optional project migration utility

The converter is separate from `src/ergotools` and excluded from the application wheel.
Use the approved interpreter with ErgoTools importable; it needs no extra dependencies.

```sh
.venv/bin/python tools/project_migration/migrate_project.py "/path/original.ergprj" --output "/path/native.ergprj"
```

Paths may contain spaces. The output must not exist and its directory must support
exclusive hard-link publication. Original XML projects need their original database and
image sidecars. Input files remain unchanged; conversion validates a private copy before
publication. An absolute script path works from any directory.

## Supported data

Inputs are supported original version-eight XML projects with sidecars, or earlier full
native formats 8–23. Output is a self-contained **format-24** `.ergprj` containing workers,
organization, embedded plant images, assessment sources/results, current Job values, PLOT
geometry and production JROT schemes. No selectable assessment versions, Job risk-profile
history/evidence, duplicate result archives or original databases remain in the output.

Format-14 through format-21 sources and matching results retain their exact values.
Older obsolete result envelopes are recalculated from saved inputs with the established
formulas, units, intrinsic rounding and ST convention. UI formatting never rounds stored
values. Selected old Job profile values become the single current Job/tool values; obsolete
profiles/evidence are removed while rotation arrangements remain. Recurring Shift event
fields and retired Station/Plant metadata are removed. Invalid retained metadata or
conflicting populated assessment owners stop conversion rather than being guessed away.
A verified empty duplicate LiFFT source can be removed under the established rule.

The format-19 upgrade adds an empty reusable task-name catalog; the format-20 upgrade
adds an empty Shift timing table. Both update the native marker while preserving every
previous table value. Names are never inferred from row position,
measurements or spelling. Current projects need no original folders or converter to open.
The maintained native fixtures are already format 24; use private copies for experiments.

## Desktop integration and errors

Open offers Migrate/Cancel and terminal guidance. The external subprocess writes temporary
native backing; the application validates it and requires first Save to choose a permanent
project file. Temporary paths never enter Recent Projects. Cancellation/failure keeps the
current workspace. The CLI publishes directly to its explicit output path.

Success writes JSON with path, format and record counts (exit 0). Conversion errors write
JSON to stderr (exit 1); invalid CLI syntax exits 2. If final reopening fails after valid
publication, inspect the existing output before retrying.

A separately supplied `ergotools-migrate` on PATH takes precedence over this source script.
The wheel installs neither command nor this directory. Removing the utility leaves current
projects usable; old-project conversion then reports the missing external tool.

The native21→23 step changes only the compatibility marker. It preserves exact older
rotation payloads/timestamps and timing templates. Older rotations remain explicitly
undated/untimed; no accepted run context or last-viewed selection is fabricated. Named
guided payloads use their own current codec when explicitly edited by the application.

Native23→24 validates the old codec capability before a marker-only exact-row upgrade.
It never promotes old run model1 evidence or rewrites old fingerprints.
