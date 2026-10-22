# CR007 — restore the original Find Assessment workflow

M11 inventory found an active original UI path that has not been ported.
The original main.py searchWorkerClicked opens WorkerSearchDialog (Find
Assessment): 1080×650 opening size, 900×560 minimum, text search, surname letters,
workplace tree and tool-specific saved assessment rows. Accept returns the selected
worker and exact context. The reference source is read only.

The new main Search callback instead calls select_navigation_context, which opens
the context chooser for the already selected worker. It cannot reproduce the
original cross-worker filtered search form. Existing worker-strip filtering and
context selection are usable but do not close this original workflow gap.

## Approved bounded correction

- Port the original Find Assessment controls/layout and processed icons into
  presentation/desktop/worker_search_dialog.py, with English/Spanish text.
- Build its rows from existing owned workspace/catalog/assessment-selection
  services, preserving tool-specific saved ownership, source unit/provenance and
  no-project/empty states. No SQL in the form and no database schema change.
- Route only the main Search action to this form. Keep Select assessment context
  as the original distinct operation. Reuse current pending-input and
  Save/Discard/Cancel selection handling; cancellation retains the active source.
- Focused regressions: text/alphabet/workplace/tool filters, exact selected worker
  and context, empty/no-selection interlocks, Cancel and dirty selection choices.
  Compare the port directly with the original constructor at matching dimensions,
  inspect native selected/expanded/empty/populated EN/ES states and complete the
  required changed-code gate/build/wheel validation.

This restores one missed original form. No new feature, milestone, points,
dependency, formula, renderer or solver change. M11 remains 95.25/100 until the
inventory closes; completion still earns its existing 2.50 points to 97.75/100.
M12 is not authorized. Any further repair is reported separately.

The owner approved “Approve original Search restoration” on 2026-10-11.
Implementation and validation are recorded in m11_acceptance.md.

Approval was required by the owner's AGENTS.md scope rule: no newly discovered
defect repair may be disguised as extending an existing milestone.
