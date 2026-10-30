"""Settings and recent history tests without opening any listed document.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from ergotools.application.settings import RECENT_LIMIT, Language, UserSettings
from ergotools.domain.assessments.lifft_draft import LifftDraft
from ergotools.domain.model_units import MeasurementSystem
from ergotools.infrastructure.settings_store import (
    JsonSettingsStore,
    SettingsFormatError,
)
from ergotools.presentation.localization import Translator


class SettingsTests(unittest.TestCase):
    """Check immutable defaults, user intent and file replacement failures."""

    def setUp(self) -> None:
        """Keep every written settings file inside a disposable test directory.

        Args:
            None.

        Returns:
            None.
        """
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / "settings.json"
        self.store = JsonSettingsStore(self.path)

    def test_missing_file_returns_defaults_without_creating_anything(self) -> None:
        """First use must not write settings or create a document implicitly.

        Args:
            None.

        Returns:
            None.
        """
        self.assertEqual(self.store.load(), UserSettings())
        self.assertEqual(list(self.path.parent.iterdir()), [])

    def test_roundtrip_language_units_and_recent_order(self) -> None:
        """Persist settings independently of existing assessment unit metadata.

        Args:
            None.

        Returns:
            None.
        """
        draft = LifftDraft(MeasurementSystem.METRIC)
        settings = UserSettings(
            Language.SPANISH, MeasurementSystem.IMPERIAL, ("/missing/á", "/other")
        )
        self.store.save(settings)
        self.assertEqual(self.store.load(), settings)
        self.assertEqual(Translator(settings.language).text("risk.low"), "Riesgo bajo")
        self.assertEqual(draft.system, MeasurementSystem.METRIC)

    def test_recent_history_is_bounded_and_moves_existing_entry_to_front(self) -> None:
        """Record successful opens without duplicates or unlimited retention.

        Args:
            None.

        Returns:
            None.
        """
        original = UserSettings()
        settings = original
        for index in range(RECENT_LIMIT + 3):
            settings = settings.remember(f"location-{index}")
        self.assertEqual(len(settings.recent_documents), RECENT_LIMIT)
        self.assertEqual(settings.recent_documents[0], "location-12")
        self.assertNotIn("location-0", settings.recent_documents)
        moved = settings.remember("location-5")
        self.assertEqual(moved.recent_documents[0], "location-5")
        self.assertEqual(len(moved.recent_documents), RECENT_LIMIT)
        self.assertEqual(original.recent_documents, ())

    def test_forget_and_clear_only_change_recent_history(self) -> None:
        """Removing missing/moved references never deletes or probes files.

        Args:
            None.

        Returns:
            None.
        """
        settings = UserSettings(Language.SPANISH).remember("missing").remember("other")
        self.assertEqual(settings.forget("missing").recent_documents, ("other",))
        self.assertEqual(settings.forget("absent"), settings)
        self.assertEqual(settings.clear_recent(), UserSettings(Language.SPANISH))

    def test_invalid_preferences_and_recent_values_are_rejected(self) -> None:
        """Reject invalid enums, duplicates, blank locations and oversized lists.

        Args:
            None.

        Returns:
            None.
        """
        for values in (("a", "a"), (" ",), (None,), tuple(str(i) for i in range(11))):
            with self.assertRaises(ValueError):
                UserSettings(recent_documents=values)
        with self.assertRaises(ValueError):
            UserSettings(language="es")
        with self.assertRaises(ValueError):
            UserSettings(default_units="metric")
        with self.assertRaises(ValueError):
            UserSettings().remember("")

    def test_input_list_cannot_mutate_saved_snapshot(self) -> None:
        """Freeze a supplied recent collection before sharing the settings value.

        Args:
            None.

        Returns:
            None.
        """
        items = ["a"]
        settings = UserSettings(recent_documents=items)
        items.append("b")
        self.assertEqual(settings.recent_documents, ("a",))

    def test_malformed_or_future_settings_are_not_silently_reset(self) -> None:
        """Preserve bytes and surface invalid formats instead of overwriting them.

        Args:
            None.

        Returns:
            None.
        """
        self.store.save(UserSettings())
        valid = json.loads(self.path.read_text())
        cases = [
            "{",
            '{"version":1,"version":2}',
            "null",
            json.dumps({**valid, "extra": 1}),
        ]
        for key, values in {
            "version": [8, True],
            "format": ["other"],
            "language": ["unknown"],
            "default_units": [None],
            "recent_documents": ["bad", [1], ["a", "a"]],
        }.items():
            cases.extend(json.dumps({**valid, key: value}) for value in values)
        for payload in cases:
            self.path.write_text(payload)
            with self.assertRaises(SettingsFormatError):
                self.store.load()
            with self.assertRaises(SettingsFormatError):
                self.store.save(UserSettings())
            self.assertEqual(self.path.read_text(), payload)

    def test_invalid_utf8_is_rejected(self) -> None:
        """Treat malformed encoding as corrupt settings, never as missing settings.

        Args:
            None.

        Returns:
            None.
        """
        self.path.write_bytes(b"\xff")
        with self.assertRaises(SettingsFormatError):
            self.store.load()

    def test_replace_failure_preserves_old_file_and_cleans_temporary(self) -> None:
        """A failed atomic replacement cannot lose the previous preferences.

        Args:
            None.

        Returns:
            None.
        """
        initial = UserSettings().remember("old")
        self.store.save(initial)
        before = self.path.read_bytes()
        with (
            patch(
                "ergotools.infrastructure.settings_store.os.replace",
                side_effect=OSError("injected"),
            ),
            self.assertRaises(OSError),
        ):
            self.store.save(replace(initial, language=Language.SPANISH))
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(list(self.path.parent.iterdir()), [self.path])
        self.store.save(replace(initial, language=Language.SPANISH))
        self.assertEqual(self.store.load().language, Language.SPANISH)

    def test_flush_failure_preserves_previous_settings(self) -> None:
        """An fsync failure aborts before replacing the previous settings file.

        Args:
            None.

        Returns:
            None.
        """
        self.store.save(UserSettings())
        with (
            patch(
                "ergotools.infrastructure.settings_store.os.fsync",
                side_effect=OSError("injected"),
            ),
            self.assertRaises(OSError),
        ):
            self.store.save(UserSettings(Language.SPANISH))
        self.assertEqual(self.store.load(), UserSettings())
        self.assertEqual(list(self.path.parent.iterdir()), [self.path])

    def test_missing_parent_is_not_created_and_failure_is_retryable(self) -> None:
        """Platform directory creation is a caller responsibility, not a side effect.

        Args:
            None.

        Returns:
            None.
        """
        store = JsonSettingsStore(self.path.parent / "absent" / "settings.json")
        with self.assertRaises(FileNotFoundError):
            store.save(UserSettings())
        self.assertFalse((self.path.parent / "absent").exists())

    def test_loading_recent_history_does_not_access_listed_locations(self) -> None:
        """Missing/invalid project files remain visible without opening or migration.

        Args:
            None.

        Returns:
            None.
        """
        document = self.path.parent / "project.ergprj"
        document.write_bytes(b"not a valid project")
        settings = UserSettings(
            recent_documents=(str(document), str(document) + ".missing")
        )
        self.store.save(settings)
        self.assertEqual(self.store.load().recent_documents, settings.recent_documents)
        self.assertEqual(document.read_bytes(), b"not a valid project")
        self.assertFalse(Path(str(document) + ".missing").exists())


def test_context_preferences_reject_non_array_rows(tmp_path: Path) -> None:
    """Reject malformed context arrays instead of interpreting strings as identifiers.

    Args:
        tmp_path: Disposable settings directory; application preferences stay untouched.

    Returns:
        None; corrupt values are reported and never silently replaced.
    """
    path = tmp_path / "contexts.json"
    store = JsonSettingsStore(path)
    store.save(UserSettings())
    valid = json.loads(path.read_text())
    for malformed in ("abcdefgh", ["abcdefgh"], {"key": []}):
        payload = {**valid, "assessment_contexts": malformed}
        path.write_text(json.dumps(payload))
        with unittest.TestCase().assertRaises(SettingsFormatError):
            store.load()
