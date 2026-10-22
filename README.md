# ErgoTools

Integrated Linux desktop application for LiFFT, DUET, Shoulder Tool, PLOT and JROT.
The current codebase separates calculations, application services, native storage,
rendering and Qt presentation. It includes English/Spanish interfaces, metric/imperial
support, one main project Save, shared chronological Undo/Redo, optional assessment
organization and one current risk set per Job/tool. Current native projects use
format 19. Windows/macOS native acceptance remains deferred.

## Run and develop

Create the approved Python 3.13.14 environment using the exact versions in `uv.lock`;
see [development setup](docs/development.md). Environments, caches and build outputs
are local and are not committed. From an initialized checkout:

```bash
bash tools/run.sh
```

For an installed wheel, use `ergotools` or `python -m ergotools.launcher`.
See [Linux installation and recovery](docs/linux_delivery.md). `dist/` is generated
locally; a source checkout does not include the historical local delivery bundle.
No dependency upgrades are part of repository setup.

## Demonstration and test projects

The clean JROT meeting project has six named workers, six Jobs with populated task
inputs and results, two plants and two shifts:

```bash
bash tools/run.sh "test_projects/native/jrot_workflow_demo.ergprj"
```

Enable Settings → General → Developer Menu for this session, then open the JROT
workflow prototype from Developer Menu. This disposable English/cm/N mockup runs
real existing calculators/optimizers. Restrictions are visual only; prototype inputs
are discarded on close. See [the walkthrough](docs/jrot_meeting_demo.md).

Other native projects in `test_projects/native/` are `workflow_4_workers.ergprj`,
`comparative_risk_test.ergprj` and `integrated_test.ergprj`. Frozen original fixture
inputs are in `test_projects/originals/`; application runtime does not read that folder.

## Documentation and verification

- [Current status and actual validation](docs/STATUS.md)
- [User guide](docs/user_guide.md) / [Guía de usuario](docs/user_guide_es.md)
- [Architecture](docs/architecture.md), [coding standards](docs/coding_standards.md),
  [API contracts](docs/api_contracts.md) and [development](docs/development.md)
- [Backup and recovery](docs/recovery.md)
- [Repository access and main-only publication](docs/repository_setup.md)

`bash tools/check.sh` runs the normal standards, types, architecture, documentation,
regression/coverage and build gates. Use the documented approved environment/native
Linux display. Existing production validation and the explicitly limited prototype
checks are distinguished in STATUS; Windows/macOS or owner acceptance is not inferred.

`main` contains the current integrated codebase. Existing other branches remain
historical backups; they are not synchronized with this replacement. The old main
history remains reachable through the replacement commit's parent.

See [LICENSE.txt](LICENSE.txt), [NOTICE](NOTICE) and
[third-party notices](THIRD_PARTY_NOTICES.txt). Applicable authorship and dependency
notices are retained. Local original-reference checkout/environment remain untouched.
