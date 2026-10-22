# Job Management language support — F70

The form now uses the shared desktop catalog for English and Spanish: labels,
buttons, tooltips, tabs, status/currentness labels, evidence-source choices,
placeholders, optional-date/sample-size text, search, confirmation, success and
validation messages. Reference English wording maps to stable `job_form_*` keys.
The former arbitrary translator callback is replaced by the explicit Language
setting used by the measurement table and nested workplace editor.

Qt message-box/search buttons are localized locally. A Spanish form uses the
es_CL widget locale for month/day names; no application-global translator or
locale mutation affects other open windows. Known backend validation messages
are translated; unrecognized validation in Spanish receives a neutral localized
review-and-retry message. Unexpected adapter failures remain logged by exception
type and shown as a localized failure message without raw filesystem details.

## Launch and preference behavior

```bash
.venv/bin/python -m ergotools.bootstrap --job-management-demo --job-language es
```

Use `--job-language en` for English. Without the option, the Job Management
preview uses the saved language preference. The explicit option affects this
preview invocation without changing saved preferences. The same option works
with `--job-management PATH`; it is rejected without a management preview option.

Display language does not translate saved job/profile names, notes, source
references, methodology, shift IDs or enum/unit identifiers. Original generated
profile names/methodology also remain record contents, not labels to rewrite.
Date display is localized, while saved dates remain ISO yyyy-MM-dd. Measurement
entry still uses the existing dot-decimal numeric contract; this does not add
locale-dependent numeric parsing or alter unit conversion/scientific formulas.
Open dialogs retain their initial language; live switching is not implemented.

## Evidence

591 tests pass (4 added), 98.05% total statement/branch coverage. New tests cover
Spanish form fields/statuses and save/approval, actual Spanish modal confirmation
and protected-history errors, stored-language selection/temporary overrides,
and matching format placeholders/error fallback. Opening a translated form does
not write project data; saved evidence retains its original names, dates and units.
Ruff/format, strict mypy, architecture and both package builds pass. The isolated
wheel runs the English lifecycle and a Spanish form save/reopen.

Native XCB inspection covers empty, approved and draft forms, both tabs at the
original 980x720 minimum, profile choices, Spanish date-picker month/day names,
search, validation, deletion confirmations and nested workplace assignments.
The bottom controls and adjacent panels fit without resizing the original window.
English empty/default, minimum, approved and approved-evidence captures are
byte-identical to F69. This is Linux native evidence; other-platform acceptance
remains outstanding. Screenshots and source/dependency hashes are recorded in
`f70_validation.json`. No dependency, schema or scientific formula change.

Remaining application integration includes the final main-window navigation,
remembered job selection, original-project import and JROT reference restrictions.
The broader application translation/units acceptance still remains; this is the
Job Management form milestone, not a claim that all ErgoTools screens are migrated.
