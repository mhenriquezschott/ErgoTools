# F143 — readable assessment selection and leading numeric digits

Integrated Open now offers tool, worker/name, complete workplace/shift and exact
version/assignment labels while keeping the stored document identity unchanged.
Narrow LiFFT/DUET/ST numeric inputs start at their leading digits, retaining full
precision and exact no-edit round trips. Existing recent-project Open, cancellation
and conversion behavior remain tested. Next: integrated comparison/visual checks
of this batch. Overall percentage and finish date remain unvalidated.

Options are loaded through an injected presentation callback composed by bootstrap;
all labels map explicitly to saved document IDs. Original historical/closed owners
remain eligible, without relabelling or rewriting stored data. Older project
formats retain their original ID selection fallback. Numeric formatting is not
rounded: only initial cursor placement changes, avoiding a trailing-digits-only
view of values such as 8.900000000000005. Focused regressions exercise identity
mapping, recent-project reopening, precision preservation and no-edit commits.

Validation: 1093 tests pass; 96.47% coverage. Ruff/format, strict mypy, architecture and builds pass. Extracted-wheel compatibility checks pass. All 500 reference hashes and the dependency lock are unchanged. UI selected/empty/populated/error states inspected in artifacts/readable-assessment-open; expanded popup rendering remains a manual visual check. Evidence: f143_validation.json and artifacts/f143-*.log.
