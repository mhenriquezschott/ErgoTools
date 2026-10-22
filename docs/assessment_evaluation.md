# Mixed-assessment evaluation and freshness — F19

## Preparation and outcomes

prepare_assessment accepts DocumentSession[AssessmentDraft] directly, with no unsafe narrowing of the generic session. It captures document, revision, immutable source, stable model kind and every ordered input issue using the existing model validators. The origin-session reference is retained only for identity checks. The original model-specific preparation APIs remain available for separately typed sessions.

AssessmentEvaluator evaluates complete DUET and imperial LiFFT sources using the already-characterized task and summary functions. It returns immutable AssessmentEvaluation with preparation, status, typed task-result tuple, optional model-specific summary and issue tuple. COMPLETE means all task and summary arithmetic returned successfully; it is not scientific certification. INVALID_INPUT includes every preparation issue and no results. CALCULATION_FAILED includes the known structured numeric error and no partial task results/summary, even if earlier rows calculated successfully. Complete zero-damage input has a summary with absent probability, distinct from incomplete/empty source.

Metric LiFFT is explicitly REVIEW_REQUIRED after input validation, with localized review.lifft_metric_moment. The unresolved displayed-moment conversion therefore cannot enter this assessment evaluation workflow. There is no bypass flag. The isolated metric task calculator/reference fixtures remain available for compatibility research, but do not authorize live metric workflow integration. Once scientific review is resolved, changing this gate requires a documented decision and regression evidence. DUET and imperial LiFFT evaluation preserve their reference arithmetic; independent scientific validation remains pending for both.

## Source ownership and cache behavior

The evaluator owns at most one outcome. current(actual_active_session) returns it only if origin session identity, revision and source identity match. Edits hide it; undo to the exact captured revision can make it current again if no later evaluation replaced the cache. A new branch with equal values, another document, another session reusing the same source object, close and reload do not qualify. Save without editing preserves eligibility.

Every evaluation clears the old cache before preparation/calculation. Known DraftError failures produce an explicit non-result outcome; unexpected programming exceptions propagate and leave the cache empty. There is no silent fallback to old results or partial totals. Evaluation changes no source, history, dirty state, settings or persisted rows. It performs no I/O and has no widget dependency.

The service is synchronous and owner-thread only. Callers must query current with the real active session before display and call clear on close/switch to release retained session references. It does not automatically subscribe to workspace events, update a widget or cancel background jobs. Holding an old returned immutable outcome is allowed for diagnostics but does not make it current; callers must not display it without checking freshness. Outcome construction is an internal application contract, not an untrusted-data validation boundary.

## Verification

Nine new tests compare all 91 nonempty DUET/imperial LiFFT groups from the actual-method reference fixtures through the complete evaluation service. They also cover ordered invalid inputs, metric review blocking/localization, zero results, edit/undo/redo/new branches, immutable/no-side-effect behavior, later-row LiFFT arithmetic overflow, DUET aggregate overflow, unexpected exceptions, and real mixed-project save/switch/close/reload.

214 tests pass on the approved Python 3.13.14 environment. Combined coverage is 99.50%; evaluation.py has 100% coverage. Ruff/format, strict mypy (60 files), architecture and source/wheel builds pass. Isolated package, reference-tree and dependency-lock evidence is in f19_validation.json. No schema, dependency or UI changed.

## Next work

Characterize TST task calculations and active assessment call sites in the original runtime, then extract its typed pure calculation boundary with the same provenance/rounding standards. GUI/VTK integration and approved dependency proposal, metric scientific review, remaining models, legacy migration and native packaging remain pending. The new project is still not a runnable replacement desktop application.
