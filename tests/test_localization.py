"""Verify risk catalog completeness and language-independent model identity.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import unittest
from dataclasses import FrozenInstanceError

from ergotools.domain.model_units import MeasurementSystem, normalize_model_load
from ergotools.domain.risk import RiskBand, classify_probability
from ergotools.presentation.desktop.theme.risk import RISK_APPEARANCES
from ergotools.presentation.localization import Language, Translator


class LocalizationTests(unittest.TestCase):
    """Check independently selectable languages without Qt or global locale."""

    def test_every_risk_key_has_both_translations(self) -> None:
        """Require exactly the migrated message keys in every supported catalog.

        Args:
            None.

        Returns:
            None.
        """
        expected = frozenset(item.message_key for item in RISK_APPEARANCES.values())
        for language in Language:
            translator = Translator(language)
            self.assertEqual(
                frozenset(key for key in translator.keys if key.startswith("risk.")),
                expected,
            )
            for key in expected:
                self.assertTrue(translator.text(key).strip())

    def test_english_display_contract_is_unchanged(self) -> None:
        """Keep every existing English label byte-for-byte identical.

        Args:
            None.

        Returns:
            None.
        """
        for appearance in RISK_APPEARANCES.values():
            self.assertEqual(
                Translator().text(appearance.message_key), appearance.english_label
            )

    def test_languages_are_independent_contexts(self) -> None:
        """Changing one view's translator must not alter another view's language.

        Args:
            None.

        Returns:
            None.
        """
        english = Translator()
        spanish = Translator(Language.SPANISH)
        self.assertEqual(spanish.text("risk.low"), "Riesgo bajo")
        self.assertEqual(english.text("risk.low"), "Low Risk")
        with self.assertRaises(FrozenInstanceError):
            english.language = Language.SPANISH

    def test_language_does_not_change_units_or_category(self) -> None:
        """Exercise all language/unit combinations with the same model input.

        Args:
            None.

        Returns:
            None.
        """
        for language in Language:
            for system, arm, force in (
                (MeasurementSystem.IMPERIAL, 1, 1),
                (MeasurementSystem.METRIC, 2.54, 4.45),
            ):
                with self.subTest(language=language, system=system):
                    self.assertEqual(
                        normalize_model_load(arm, force, system).load_lbf, 1
                    )
                    band = classify_probability(25)
                    self.assertEqual(band, RiskBand.LOW)
                    self.assertTrue(
                        Translator(language).text(RISK_APPEARANCES[band].message_key)
                    )

    def test_missing_keys_are_not_silently_hidden(self) -> None:
        """Fail visibly when a migrated view requests an untranslated message.

        Args:
            None.

        Returns:
            None.
        """
        for language in Language:
            with self.assertRaises(KeyError):
                Translator(language).text("missing.key")

    def test_unknown_language_is_rejected(self) -> None:
        """Do not silently reinterpret an unsupported external language code.

        Args:
            None.

        Returns:
            None.
        """
        with self.assertRaises(ValueError):
            Translator("fr")
