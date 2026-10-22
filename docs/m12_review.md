# M12 review and remaining native-platform decision

The bounded Linux delivery work is verified. A small installed console/module
launcher selects the existing integrated desktop and VTK, while the diagnostic
bootstrap keeps its established flags. Qt configuration lookup remains in the
allowed composition root; the architecture gate rejected the first placement in
the launcher and that placement was corrected without an allowlist exception.
Per-user settings avoid launch-folder dependence; explicit --settings retains
old development preferences. No project data is opened or changed by the launcher.

The clean acceptance environment has its own copied approved Python 3.13.14,
separate venv, 17 exact runtime dependencies and the built wheel; no development
tools/source editable install. Initially incomplete uv registry-cache metadata
prevented offline installation. The same approved hash-locked distributions were
downloaded and installed; no version changed. This is initial network installation
followed by disconnected operation, not an offline installation/wheelhouse claim.

The native scenario uses the installed distribution's console entry point and
runs from an unrelated folder containing spaces. All final application imports
stay inside the fresh installation; all 71 reference assets match. A separate
network namespace has only loopback, with no external interface. VTK renders,
CBC solves one-tool and HiGHS solves all-tool models. A disposable copy of M10's
validated comprehensive project opens; Backup matches the complete persisted SQL
dump and reopens with equal worker/hierarchy/jobs/history/PLOT/JROT/archive data.
Only the generated test copy/backups are used. No reference checkout is needed
for the installed scenario; the original dataset is not opened or modified.

Four final captures inspect empty, populated, fully Spanish and restored states
with VTK/sidebar/bottom controls visible. Early harness captures were mid-animation
and directly assigned language without the real refresh callback; those invalid
captures were replaced by settled gauges and the wired language change. No
application rendering/localization repair was needed. M01–M11 component and
comprehensive evidence remains valid and reused.

Final code gate: 1,226 tests, 96.42% coverage; Ruff/format/strict mypy/architecture
and builds pass. After guide-only launcher-instruction edits, the final wheel
passes 21 focused launcher/Help/resource tests and 77 subtests; all 237 package
Python files and both guide files match source. The clean environment's exact
17 package versions match the approved pins. Reference 500 files and lock unchanged.

Linux delivery files/checksums and install/run/recovery instructions are ready.
The remaining decision is explicitly bounded: defer native Windows/macOS acceptance
or keep M12 open for that work. Existing Windows VMs are off and their new-project
baseline has not been validated; no macOS target is configured. No VM changes or
different target-library installs were attempted. Source/platform review is done;
neither OS is marked passed. M12.3 requires an explicit deferral decision before
closure, so no M12 points are awarded yet. No new milestone or repeated research
is proposed. Current fixed progress remains 97.75/100.


## Final owner disposition — supersedes pending decision above

On 2026-10-11 the owner confirms Linux is the migration completion target and
defers Windows/macOS tests to later work. Linux expected behavior/original-codebase
parity remains the acceptance priority, supported by M01–M11 evidence. M12 is
closed with 2.25 existing points; total 100/100 Linux scope, 12/12 milestones.
Windows/macOS native checks remain unexecuted; platform source review is not
native acceptance. This documentation-only closure changes no code or dependency
and needs no repeat of passed regression/native checks.
