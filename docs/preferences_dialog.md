# F88 — application preferences

The owner allows improvement of the limited Settings window. Tools > Settings now
opens a styled owned form for independent language and unit choices, with packaged
Cancel/Settings icons and explicit Apply/Cancel. The existing toolbar Settings keeps
its original task-count operation; no source-clearing operation is hidden in the
preferences form. Tools/Herramientas and Settings/Configuración are localized.

The view collects typed enum selections; it does not access settings or project
storage. `LifftWindow` receives the existing `SettingsStore` through composition.
Cancel does not commit pending text. Apply validates pending input using the current
source units/convention, then saves updated language/default units while preserving
recent locations. Source units and values are retained across display projection.
UserSettings and the JSON format are unchanged. Language never implies units.
Decimal convention remains the existing session preference, not a new persisted field.
Existing blank-version/source-unit policies remain; no scientific conversion policy
or stored project metadata is silently changed.

Invalid input leaves pending text/source/preferences untouched. Settings-write
failure leaves the previous display policy; valid task text accepted during Apply
remains a normal source edit, with the editor rebound so subsequent editing remains
usable. New windows load persisted preferences through bootstrap even with no open
project. Invalid settings files propagate their existing adapter errors instead of
silently overwriting them. Preferences work independently of source availability.

Three parameterized native workflows exercise LiFFT/DUET/ST actual modal Cancel,
invalid Apply, injected settings-write failure, valid input recovery, Apply,
source-unit retention, preserved recent locations and preference restoration in a
fresh window. Required gates pass with 685 tests and 96.85% combined
coverage, strict mypy on 141 source files, lint/format, architecture and both builds.

Native captures under `artifacts/preferences/` cover default/selected dialogs,
expanded language/unit controls, Cancel with pending invalid input, invalid Apply,
Spanish/metric main layouts for all three tools and 1920 by 1200 enlargement.
Minimum layout is 1550 by 1015. Avatar, cards, labels and bottom controls remain
visible. A LiFFT footer mismatch was observed and corrected: footer units identify
the selected display system, not the recorded source system. Native VTK framebuffers
are composed using F78's capture method. Existing metric moment scientific review
and label policies remain outstanding; this is not final metric calculation acceptance.

The isolated wheel passed three-tool actual Settings Cancel/Apply, unchanged
persisted sources, language/unit restoration and native renderer cleanup. All 500
reference hashes and the lock remain unchanged. Evidence is `f88_validation.json`,
`artifacts/f88-check.log` and archived `reference/f88-capture.py.txt` /
`reference/f88-verify.py.txt`. Only synthetic project/preferences paths were used.
No dependency, reference environment or operational project was changed.

Next are remaining project/menu lifecycle operations. Full dialog/Qt-stock language
coverage, decimal preference persistence, scientific decisions and remaining
application modules still require migration; this slice is not full Settings or
whole-application parity.

F94 supersedes the earlier session-only decimal limitation: Settings now includes
persisted decimal convention and user-settings format two. See
[decimal preferences](decimal_preferences.md) for backwards compatibility and tests.
