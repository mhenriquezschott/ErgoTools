# JROT rotation report

In **08 / Comparison & report**, choose **Report…** to review the displayed
optimization and **Save PDF…** to export it. Page navigation, zoom and Fit page
work inside ErgoTools. Export does not keep a preview, change the baseline or save
the project. Keep optimization result and the main project Save retain their
existing separate meanings.

The report presents:

1. Current or starting-proposal matrix and suggested matrix, with exact block
   clocks/productive durations and a Job legend.
2. Per-tool mean and maximum worker index, maximum change in percentage points
   and relative percent, and conditional practical recommendations.
3. Per-tool mean, maximum, population standard deviation and range.
4. Each worker's before/after indices and changes, flagging individual increases.
5. Intrinsically High Jobs by analyzed tool and general controls advice.

Small studies follow the two-page supervisor/detail structure on portrait A4 pages. Current and suggested matrices are stacked at full width. Larger studies use full-width matrices
in bands of four blocks and additional pages with repeated table headers. All
workers and blocks remain in the output. English/Spanish follow the application
language; user-entered names are preserved. Tables use the existing risk colors
and readable contrasting text. Ordinary prose is 11 pt; dense tables 10 pt.

## Evidence and interpretation

Reports read the displayed frozen `RotationRun`, including its recorded worker/Job
names, probabilities, timing and arrangements. They never re-solve or substitute
current Job data. The project/rotation captions identify the current owning plan.
Unkept previews and stale records are explicitly marked. Unsupported model evidence
cannot be exported as a newly interpreted comparison. Missing starting schedules
remain absent, not zero. A generated proposal is identified as a proposal.

Worker scores are time-weighted **Job-risk indices**, not individual injury
probabilities. Values are presented on the application's 0–100 scale. Changes are
After minus Before in percentage points. Relative change is
`100 × (After − Before) / Before`; a zero starting value has no defined relative
percentage. Statistics reuse the domain comparison and its unrounded values;
display rounding never changes saved evidence. The existing >50% High threshold
applies to frozen selected-tool Job values. Recommendations do not certify legal
compliance, promise a reduction in the mean or assume recovery during breaks.

## Implementation and failures

`application/rotation_report.py` validates a read-only report snapshot using the
existing domain comparison. It imports no Qt, repository or solver.
`presentation/desktop/jrot_report_document.py` owns escaped, localized HTML and
`QTextDocument` content. `jrot_report_dialog.py` renders the same document to Qt's
in-app print preview and PDF paint devices, including page numbers. This uses the
existing PyQt5 QtPrintSupport dependency; no PDF library, schema or project migration
is introduced. Nothing is stored until the user chooses a PDF destination.

PDF publication writes a sibling temporary file, validates the PDF signature and
completion trailer, then replaces the destination atomically. A failure leaves an
existing destination intact and removes staging bytes. Save cancellation writes
nothing. The dialog catches rendering/export errors and shows local feedback;
preview callbacks never let a rendering exception escape into Qt's event loop.
The native file chooser provides replacement confirmation, including when the user
omits the `.pdf` extension. External PDF files are independent of project saves.

## Validation

Focused report tests cover independently known 0/100 → 50/50 comparisons, missing
starting evidence, unsupported models, zero denominators, one/two/three selected
tools, English/Spanish two-page output, actual Qt preview/navigation/export,
cancellation, truncated render and failed atomic publication. Native Linux XCB
checks open the real step-08 Report action on private Packing trial and Demo 20
copies, compare preview/export page counts and check maintained sample hashes.
See the current STATUS checkpoint for final gate results and visual evidence.
Windows/macOS PDF preview and native Save dialogs require owner platform checks;
Linux rendering does not certify those platforms.
