# First desktop runtime proposal — 2026-09-29

Status: approved by the owner with “ok go” in response to the exact three-version request on 2026-09-29. Installation and matching lock entries are authorized in the new project only.

## Proposed installation

Install only into the new project's existing Python 3.13.14 `.venv`, using the existing manager. Keep all approved developer-tool/transitive versions fixed. Add a Linux desktop optional dependency group with these exact versions and hashes in the project lock after approval:

| Package | Exact version | Role |
|---|---|---|
| PyQt5 | 5.15.11 | Qt Core/Gui/Widgets and bundled QtTest interfaces |
| PyQt5-Qt5 | 5.15.17 | Qt runtime required by PyQt5 |
| PyQt5-sip | 12.17.0 | Binding runtime required by PyQt5 |

Read-only distribution metadata from the original Conda environment reports these same three versions. Original Python remains 3.10.18; new-project tests remain on the already-approved 3.13.14. Matching library versions reduces migration variables but does not prove Python/runtime equivalence. No original environment modification is proposed.

Official release metadata was checked for [PyQt5](https://pypi.org/project/PyQt5/5.15.11/), [Qt runtime](https://pypi.org/project/PyQt5-Qt5/5.15.17/) and [SIP runtime](https://pypi.org/project/PyQt5-sip/12.17.0/). `reference/desktop-package-metadata.json` records requirements, selected Linux wheels, download URLs and SHA-256 hashes. PyQt5 requires SIP >=12.15,<13 and Qt >=5.15.2,<5.16.0; the proposed versions satisfy those declarations. Qt/SIP list no additional Python runtime requirements. Selected wheels total 69,582,620 bytes (~69.6 MB); installed footprint will be larger.

PyQt5's cp38-abi3 Linux wheel and SIP's cp313 wheel match the candidate interpreter/platform tags; Qt has a Python-independent Linux x86-64 wheel. This is metadata-based feasibility, not an import or rendering test. The host reports Linux x86-64/glibc 2.41 with DISPLAY and WAYLAND_DISPLAY set. Access to a usable display, platform-plugin system libraries, fonts and screenshots still requires verification after installation. No system package changes are included; missing native dependencies will be reported separately.

## Scope and limits

The first desktop slice uses Qt widgets plus the tested stdlib core. No VTK, WebEngine, solver/scientific packages, pytest-qt, packaging tool or font installation is requested. Existing QtTest and unittest/pytest can exercise widget events. VTK remains part of the eventual application, isolated behind its existing renderer port, and needs its own reviewed adapter/dependency slice before avatar acceptance. This proposal does not replace VTK.

The first screen will support a LiFFT document's task editing, history, validation, calculation, source/display units, explicit decimal convention and new-format save/open. Imperial LiFFT can evaluate; metric source remains review-required. It is a development vertical slice, not complete work-context/legacy-file support or a replacement application. See `desktop_first_slice.md` for integration and visual criteria.

Risks are native binary loading, Qt platform-plugin availability, Python 3.13 binding behavior, font substitution and platform packaging. Package metadata licenses are archived (PyQt5 GPL v3, Qt LGPL v3, SIP BSD-2-Clause); release packaging must carry applicable notices and retain the project's existing release review. No licensing or release approval is implied by local development installation.

After approval: add exact optional pins, resolve without changing existing locked versions, verify the lock diff, install only the project environment, check actual imports/versions, exercise offscreen rendering and real display availability, then implement and visually inspect the screen. If resolution needs any additional package/version changes, stop and propose those separately. Preserve the old tree/environment throughout.

Approval requested: these three exact packages, corresponding project-local dependency/lock entries and installation in the new project only. Python and all existing versions remain fixed.
