# Original main JROT integration — F127, 2026-10-09

The integrated main toolbar now opens the original JROT form modally on a full
new-format project. CBC single-tool and HiGHS all-tool workflows are available
through that actual entry point. No new dependencies or reference changes.

## Source mapping and ownership

Reference src/main.py openRotationLayout and toolbaropenRotationLayout open
RotationLayoutWindow modally over the current project; their existing toolbar
asset, dimensions, tooltip and layout are retained. Source controls/layouts were
already mapped and visually compared in jrot_form.md, jrot_selected_optimization.md
and jrot_comparison.md. This checkpoint changes composition, not those layouts.

ProjectWorkspace supplies the runtime-checked application RotationRepository
capability, borrowing its one owned AssessmentProjectFile. Capability checks
perform no project reads/writes. The same adapter supplies PLOT. Bootstrap injects
PulpRotationOptimizer into RotationDialog; views import no concrete solver/storage.
The modal owns its worker/comparison windows, and bootstrap disposes it only when
its actual modal lifetime ends. Normal close during a solve defers until bounded
completion; the project connection stays owned and usable by the workspace.

JROT is enabled only with a supported full project and an installed opener. No
project or assessment-only format-two projects disable it. Runtime failure uses
the existing logged/localized GUI boundary and retains assessment text.

Opening JROT browses saved job risks, without parsing, calculating or saving
unfinished LiFFT/DUET/ST inputs. Explicit JROT Save writes only scheme data and
updates the borrowed adapter's format state. Subsequent reopen, PLOT access and
assessment Save retain the saved schemes. This does not introduce project-switch
callbacks or multi-user machinery while the modal is open.

## Intentional behavior and remaining parity

The reference calls ensure_jrot_schema on opening JROT. The migrated reader
continues its established non-migrating policy: only explicit first scheme Save
upgrades a supported full project to format eleven. Opening, solving, comparing,
Apply, and closing perform no scheme/schema writes. Approved historical profile
and worker/placement links and their recorded unit evidence remain unchanged.
CBC stays single-tool and HiGHS stays multi-tool; no GLPK or fallback.

Main toolbar JROT is now usable. Final menu parity remains an acceptance item
alongside legacy-project compatibility/import and comprehensive copied-project
integration. Current native validation uses isolated new-format projects, not an
operational dataset. Windows/macOS packaging and overall final UI/workflow parity
are not established by these Linux tests.

## Validation

1003 native tests pass, eleven new focused cases; 96.70% coverage.
Ruff/format (471 files), strict mypy (215 source files), architecture,
wheel and sdist pass. Focused main/JROT tests cover actual EN/ES CBC/HiGHS
Apply/Save/reopen, exact profile links, format upgrade and subsequent workspace
Save, all three tools' invalid pending input, no/missing/full-project capability,
concrete opener errors and deferred modal closure with an owned worker.

28 native images inspected: 20 window captures and eight actual VTK backbuffers.
Main no-project/open-project minimum/enlarged/return, JROT empty/populated minimum,
selected/enlarged/CBC/all-tool selected tab/applied saved are covered in EN/ES.
Main VTK, result cards, labels and bottom controls remain in their original
regions; JROT panels and bottom controls are visible. Wide empty grids retain
source horizontal scrolling. QWidget.grab omits the native VTK surface, so main
captures composite its actual backbuffer at the widget's Qt coordinates; those
raw buffers are retained separately. No whole-window pixel parity is claimed.

Independent extracted-wheel native actual main toolbar -> modal JROT -> CBC and
HiGHS comparisons -> Apply -> explicit Save -> reopen passes in EN/ES with VTK
initialized. Every imported ergotools module resolves under the wheel extraction.
All 500 reference hashes and the approved dependency lock are unchanged.
Evidence: f127_validation.json, artifacts/f127-check.log, f127-focused.log,
f127-wheel.log and artifacts/jrot-main; scripts in reference/f127-*.py.txt.

Next: audit legacy-project compatibility against a read-only source review and
isolated copies; then comprehensive copied-project cross-feature validation and
final UI/workflow/platform acceptance. No reliable overall percentage or finish
date is established yet; previous foundation estimates remain withdrawn.
