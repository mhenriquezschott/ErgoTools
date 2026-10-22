# F92 — original worker transfer

The integrated worker strip now opens the original three-column Transfer form:
source context and tool selection, Copy/Move, destination worker/hierarchy/shift.
Its controls, margins, sizing, stylesheet and processed icons were ported from
`src/worker_transfer_window.py` in the read-only reference. It is not the separate
older `workertransferdialog.py` implementation. The form starts at 1280 by 720,
with a 1280 by 640 minimum. Native review found that the original 1080-pixel
minimum clips the alphabet label and workplace Type column; the minimum width
now retains the original opening width so the fixed controls remain visible.
Tool order, workplace expansion, filters,
selection interlocks and the complete destination preview follow the original.

Copy duplicates selected **saved current versions** under the destination owner.
It keeps source versions and pending editor text, including invalid pending text.
Save first to include edits in a Copy. Move copies those selected saved versions
and removes exactly those source current versions in the same SQLite transaction.
Older noncurrent versions, other tools/owners and job risk profiles remain intact;
no older source is automatically promoted. Both operations preserve recorded
units, task identities and source values; new document IDs belong to the destination.
The transfer does not classify a job or copy a job risk profile. It reuses the
active destination assignment or creates an unclassified one when needed.

The source is the exact historical assignment of the open assessment, including a
closed assignment. Any selected tool already current anywhere in the destination
worker/workplace/shift context rejects the whole request, including data under a
closed destination assignment. There is no overwrite. Source equals destination,
no tools, no station or no destination worker disable Transfer. Search/alphabet
filtering clears hidden worker selection. Confirmation defaults to No.

If Move removes the open current assessment, valid pending fields are first
accepted as normal editor input and the ordinary Save/Discard/Cancel decision is
required for dirty data. Cancel leaves the transfer form open and changes no
persisted transfer data. Save persists the source before transfer; if the later
transfer fails, that explicitly requested Save remains. Discard transfers the
previously saved source. A successful Move clears the removed open assessment;
it does not silently open an older version. Moving other selected tools preserves
the open assessment. Copy and closing the form do not commit pending fields.

`domain/assessment_transfer.py` plans typed immutable requests without I/O.
`application/transfer_access.py` declares the optional repository capability.
`ProjectWorkspace` coordinates consent/session changes, while
`AssessmentProjectFile` performs parameterized writes under one `BEGIN IMMEDIATE`
transaction. It rechecks membership/conflicts under the lock; any insertion,
removal or assignment failure rolls back all transfer writes. The Qt form owns
selection and messages without SQL or global window lookup. No dependency,
project schema, reference source/environment or operational dataset changed.

Validation: eight focused cases cover three-tool Copy/Move, older histories,
unchanged profiles, conflicts, a failure on the second insert, retries, filters,
actual modal Cancel/Copy/dirty-Move-Cancel, and explicit Save before Move.
The required baseline gate passes 719 tests, 96.38% combined coverage, lint/format,
strict mypy on 148 source files, architecture checks, wheel and source builds.
The extracted wheel independently exercises actual owned modal No/Copy/Move-Save,
all three tools, preserved source units/settings/location, conflict rejection,
closed-assignment history and native VTK cleanup.

Native captures in `artifacts/worker-transfer/` compare the original form and the
migration on the same platform, baseline and 1280 by 720 size, using synthetic
new/legacy fixtures only. Default, selected Copy/Move, empty source, empty filter,
minimum size, Spanish/enlarged 1600 by 900, confirmation and conflict messages were
inspected. Integrated native avatar, result cards, captions and bottom controls
remain visible at 1550 by 1015 before/after Copy. This is reviewed form evidence,
not final comprehensive-project or cross-platform acceptance.

English form controls retain the reference appearance. Principal commands,
headers, context labels and preview support Spanish. Supporting paragraphs,
several tooltips, stock Qt buttons, alphabet All and domain error wording still
need the planned full-language review; this is not complete localization.
Scientific formula gates remain unchanged. Legacy project import is not implemented
by this workflow; it operates on the migrated project format.

Evidence: `f92_validation.json`, `artifacts/f92-check.log`, archived
`reference/f92-capture.py.txt` and `reference/f92-verify.py.txt`.
Next: remaining View/Help menu operations and completion of application preferences
and localization/decimal persistence. Project details/sidecars, scientific review,
remaining renderer features, PLOT/JROT, legacy import and final copied-project/
platform acceptance remain. Overall completion percentage and finish date remain
unvalidated after withdrawal of the former 67% estimate.

F95 extends the partial transfer language coverage; supporting copy, tooltips,
owned messages and record-label protection are described in
[transfer localization](transfer_localization.md), including a native message
appearance discrepancy that remains for final UI parity acceptance.


## M10 / owner-approved CR006 — exact result preservation

Copy/Move now preserves saved and imported result snapshots as well as task
inputs. It retains original summary rounding, task outputs, unit text (including
absence) and fresh/recorded provenance in the existing atomic transaction.
Fresh version-one result payloads stay compatible; recorded copies use explicit
version two in the same optional table. Old intermediate builds are not promised
to read these newer recorded-copy payloads. Original archives remain unchanged.
Changed-source outputs are ignored and absent outputs are not manufactured.
Focused Copy/Move/reopen/CSV/rollback checks and final comprehensive integration
pass; see m10_acceptance.md. No formula or UI change.
