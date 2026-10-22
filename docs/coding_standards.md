# Coding and acceptance standards

The detailed accepted standards are in section 3 of [the plan](reference/modernization-plan.md). Use English identifiers, snake_case modules/functions/variables, PascalCase classes and UPPER_SNAKE_CASE constants. Use UTF-8, LF, four spaces and 88-column formatting. Preserve branded UI names and necessary framework override names through narrowly documented exceptions when introduced.

All maintained functions/methods/private/nested helpers require substantive
Google-style docstrings, including arguments and return/yield values; document units, errors, side effects and scientific sources where relevant.
Each file explains purpose, scope, responsibilities and architectural layer.
Constants need an adjacent explanation of meaning, scale and source when relevant.
This applies to application code, tests, tooling and the external converter.
The cleanup inventory tracks individual symbols and source hashes. Structural and
review-inventory gates run with the required checks; neither substitutes for an
accurate body/contract review. Changed files require explicit review certification. Use immutable value objects/enums for contracts and None for absence. Prefer pure arithmetic and constructor injection. No import-time I/O, global window lookup, wildcard imports, production sys.path manipulation, duplicated legacy alternatives or silent broad exception handling. SQL belongs in parameterized transactional adapters. Numeric names expose scale and dimensions.

| Automated gate | Enforced today |
|---|---|
| Ruff check | E/F, imports, naming, docstrings, modern Python, bug patterns, simplifications, Ruff-specific and annotation rules |
| Ruff format | Deterministic formatting |
| Documentation structure | All maintained modules/classes/functions, exact Args names, Returns/Yields, explicitly escaping raised errors and adjacent constant comments |
| Documentation review inventory | Exact file/symbol/signature/hash metadata; new or changed code requires renewed substantive review; regeneration cannot certify source |
| Strict mypy | All source and Python tooling; no implicit untyped boundaries |
| Architecture AST checks | Layer direction, portable core imports, VTK confinement, wildcard/dynamic imports and module naming |
| pytest and coverage | Behavior, boundary/invalid cases, asset integrity and negative architecture probes; 90% combined statement/branch coverage minimum |
| Hatchling build | Independent wheel and source archive |

These tools cannot prove scientific correctness, complete documentation quality, every variable's meaning, lack of circular imports, visual coherence or all architectural semantics. Review these explicitly. Existing tests intentionally include forbidden imports and malformed module names as strings to prove architecture failures are detected. A separate initial Ruff probe confirmed missing docstrings, invalid function naming and missing annotations are detected.

A completed component needs characterized behavior, an owned API, tests and applicable lifecycle/unit/language/history checks. Changed UI also needs visual inspection. Record discrepancies instead of silently choosing old or new behavior. The current fixture establishes reference equivalence only for finite risk-category inputs; it does not validate injury-probability models.

The architecture gate also excludes converter imports and converter-reader files
from the application package. Its negative tests cover unused files and both
direct and package-qualified imports. Conversion belongs in `tools/project_migration`.

## Maintaining complete in-code documentation

`tools/check_documentation.py` inspects every maintained `.py`/`.pyi` file under
src, tools, tests and typings, including private and nested functions. Receiver
parameters are omitted only for real instance/class methods; static arguments,
positional-only arguments and variadic names remain required. Procedures explicitly
say `Returns: None`; generators explain yielded values. Explain units, ownership,
errors, mutations and cleanup where relevant, rather than repeating a signature.
Dataclass/class documentation explains its state contract and relevant attributes.
Each constant has an adjacent meaning/units/source explanation.

`tools/check_documentation_review.py` compares generated source evidence against
`cleanup_documentation_inventory.json` and the independent reviewer decisions in
`cleanup_documentation_reviews.json`. New, changed or deleted files, signature or
symbol metadata drift and changed shell entry points fail the gate. A reviewer
must inspect the actual body and callers/tests, correct its prose, then explicitly
update that file's SHA-256 entry. Do not bulk approve files because headings pass.
After that review, regenerate metadata with:

```bash
.venv/bin/python -m tools.check_documentation_review --refresh-inventory
```

Regeneration never writes the certification map and still fails for pending files.
Both checks are source-only and execute no inspected application code. Structural
rules cannot infer every error from an injected adapter or judge semantic prose;
that remains the reviewer's responsibility. Frozen source evidence/generated files
are outside the maintained-code inventory; two developer shell entries are reviewed
for file purpose, arguments, exit behavior and effects.


## Database purpose and integrity

Every current table/column/key/relationship must support a named existing functionality
or approved configuration. Document that purpose in database_tables.md. No speculative
history tables, unused compatibility tables or alternate assessment-version feature may
be retained. A worker Job assignment/tool owns at most one assessment; scientific inputs
and the sole source-bound result are distinct responsibilities, not duplicate results.
Schema changes need exact source/result and cross-feature preservation tests, uniqueness/
foreign-key/rollback checks, and reopen/Save As/Backup acceptance. Conversion belongs to
the external tool, stages privately and never overwrites an original. Ask about ambiguous
populated data rather than guessing which values to keep. Job risks now have one current set per Job/tool; file/codec compatibility versions
remain separate functional contracts.

## Owned dialogs and system selectors

Use the shared presentation dialog palette for ErgoTools-owned forms, numeric/item
inputs and confirmations, while retaining established local styles and packaged
assets. File, color and font selectors use platform defaults, as explicitly directed
by the owner; do not force non-native variants or apply the owned-dialog helper to
them. Use standard selector APIs and preserve existing filters/save policy rather
than implementing a custom browser. Verify native responsiveness manually without
claiming a mocked chooser-boundary test establishes platform UI acceptance.
