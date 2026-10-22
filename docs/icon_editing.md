# Editing application icons

For this checkout, edit PNG files in **src/ergotools/resources/icons/** in the new
ErgoTools project. Do not edit the reference application's assets/ui-icons directory,
project files, test projects or generated dist/linux copies as the source of changes.

The current .venv is using this checkout's source package; infrastructure.read_asset
resolves icons with importlib.resources. bootstrap.load_icons reads packaged PNG bytes
into QPixmaps/QIcons when the window is composed. Keep the same filename and restart
ErgoTools to reliably load edited artwork. There is no icon hot-reload or image cache
stored in projects. A distributed installed wheel instead reads its own package copy;
rebuild/redeploy it to distribute artwork changes.

Preserve transparent background, original canvas dimensions, crop and visual padding,
and the existing navy/teal artwork conventions. Files use snake_case. Replacing an
existing PNG under the same identity requires no application-code change. New asset
identities additionally need explicit loader/mapping integration and an appropriate
existing menu/action binding.

After intentionally editing artwork, update its SHA-256 and provenance in
src/ergotools/resources/manifest.json, preserving the previous origin information;
verify relevant menus/windows at normal and high-DPI sizes and rerun resource checks.
The application does not reject a manual edit at runtime because of the manifest;
the development tests do flag unrecorded hash changes. Do not simply remove the check.
The local delivery packages/checksums must then be rebuilt from the source assets.

Redo is a separately saved horizontal mirror of undo.png, not dynamically generated
at runtime. If changing Undo's artwork, refresh redo.png as well to preserve that pair;
its provenance/hash lives under derived_assets. tests/test_properties_scroll.py verifies
menu dimensions; tests/test_avatar_navigation.py verifies the static Undo/Redo mirror;
tests/test_resources.py checks registered asset hashes.

Menu icons now use exactly **25 logical pixels**, only for QMenu, as requested by the
owner. Qt applies display scaling; toolbar/button icon metrics remain unchanged.
This supersedes the earlier 120% / 19-pixel menu setting. The menu-only QProxyStyle
metric is documented by Qt: https://doc.qt.io/qt-6.5/qproxystyle.html#pixelMetric .
The same API is verified against our unchanged PyQt5/Qt5 baseline. Native
Windows/macOS menu checks remain separately deferred.
