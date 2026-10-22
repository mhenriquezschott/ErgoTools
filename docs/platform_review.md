# M12 frontend platform review

Linux XCB on Ubuntu 25.04 x86-64 is executed and validated. This review is source
inspection and a native-target checklist, not evidence that Windows/macOS ran.
Existing system libvirt Windows VMs are shut off; no validated new-application
Windows baseline has been prepared. No macOS test target is configured. No VM
was booted or modified. The owner explicitly deferred native acceptance on 2026-10-11 and confirmed
Linux as the migration completion target; no milestone or weight was added.
Windows/macOS tests remain NOT RUN and are later follow-up.

| Concern | Current implementation / evidence | Native follow-up |
|---|---|---|
| Assets and paths | importlib.resources package bytes, pathlib paths, QUrl.fromLocalFile; installed-only asset hashes and non-ASCII/space launch folder pass | Windows drive/Unicode paths, case sensitivity and bundle layout |
| Configuration | Qt QStandardPaths AppConfigLocation in composition root; explicit --settings supported | Verify actual per-user locations/permissions and installed launcher |
| Fonts, layout, DPI | Existing reference-derived layouts, stretch regions, synchronized task headers, font-metric text fitting and owned native viewport captures | Windows scaling 100/125/150/200%, macOS Retina, font fallback, full VTK/cards/bottom controls |
| Menus/shortcuts | Qt actions and standard Undo/Redo bindings; localized menus remain intact on Linux | macOS menu placement/roles and Cmd shortcuts; native dialog button order |
| Threads and lifetime | Solver thread publishes validated outcomes, UI stays GUI-owned; modal close/cancel and VTK teardown already accepted | Exercise close/cancel/render teardown with native event loops/drivers |
| Native binaries | CBC 2.10.3 bundled through approved PuLP, HiGHS/highspy 1.11.0, VTK 9.5.0 work in isolated installed Linux app | Approve and install exact target wheels/Qt runtime/native executables first |
| Files and transactions | Parameterized SQLite, exclusive publication, QSaveFile preferences/Help; installed backup/reopen equivalence passes | Native file locks, antivirus interference, save dialogs and permissions |

Qt 5's documented DPI support distinguishes logical coordinates and device pixels,
with OpenGL requiring attention. Fractional scales/font metrics need native visual
acceptance; changing global scaling/style without that evidence could alter the
accepted Linux layout. No speculative global DPI override was introduced.
[Qt 5.15 high-DPI documentation](https://doc.qt.io/archives/qt-5.15/highdpi.html).

Qt documents QObject/thread affinity and GUI ownership. Existing solver/renderer
boundaries retain that separation; no new cross-platform thread framework is
needed. [Qt 5.15 threads and QObjects](https://doc.qt.io/archives/qt-5.15/threads-qobject.html).

The current desktop dependency metadata intentionally has Linux markers. A pure
Python wheel tag does not certify the native dependencies or this UI on another
OS. Python 3.13.14 and target package/Qt/solver versions must be explicitly approved
before creating a different baseline. Do not remove markers, substitute Qt builds,
claim native success from Linux tests, or modify the working reference app.

Native acceptance, when authorized: boot disposable VM/copy, establish approved
versions, launch installed app, compare original/current at matching DPI/theme/
fonts, exercise project conversion/assessment/workers/jobs/PLOT/JROT/Transfer/
backup and both languages/units, check teardown, record exact results. No native
Windows/macOS success is claimed by the present source review.
