"""Versioned user settings with same-directory atomic replacement.

Infrastructure layer. Adapt validated application/domain values to explicit storage or
interchange formats. Use parameterized SQLite or caller-selected file paths; no Qt UI,
scientific formula changes or automatic old-project conversion. Connection ownership and
transaction boundaries are specified by each operation; I/O failures propagate unless
wrapped as a format error.
"""

import json
import os
import tempfile
from dataclasses import asdict
from pathlib import Path

from ergotools.application.assessment_columns import AssessmentColumns
from ergotools.application.assessment_import import ImportProfile
from ergotools.application.gauge_preferences import GaugeMarkerSettings
from ergotools.application.settings import DEFAULT_UNDO_LIMIT, Language, UserSettings
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.decimal_convention import DecimalConvention
from ergotools.domain.model_units import MeasurementSystem


class SettingsFormatError(ValueError):
    """Malformed or unsupported settings; never silently reset user preferences."""


def _members(pairs: list[tuple[str, object]]) -> dict[str, object]:
    """Strict decoder hook; no I/O.

    Args:
        pairs: Ordered decoded JSON object members before dictionary construction.

    Returns:
        Unique-key settings object.

    Raises:
        SettingsFormatError: A JSON member name is duplicated.
    """
    values: dict[str, object] = {}
    for key, value in pairs:
        if key in values:
            raise SettingsFormatError("Duplicate settings member.")
        values[key] = value
    return values


class JsonSettingsStore:
    """Persist to an explicitly supplied user-settings path, never a project path.

    The caller owns directory creation and platform path selection. This adapter
    is single-writer; it provides no interprocess locking. Version-one settings
    default to point.
    """

    def __init__(self, path: Path) -> None:
        """Remember the destination without creating directories or reading files.

        Args:
            path: Caller-selected per-user UTF-8 settings path; parent creation remains
                caller-owned.

        Returns:
            None; retain path without reading or writing.
        """
        self._path = path

    def load(self) -> UserSettings:
        """Return defaults only for a missing file; reject damaged/future formats.

        Args:
            None.

        Returns:
            Validated settings; defaults only for a missing file, decimal point for
            version 1, animation True before version 3, and default gauge markers
            before version 5, Undo limit 25 before version 6 and result animation True
            before version 7; import profiles default empty before version 8,
            visible columns before version9. Version10's obsolete solver-choice
            field is discarded; version11 writes no solver preference.

        Raises:
            SettingsFormatError: Encoding, fields, duplicate members, version or
                preference values are invalid.
            OSError: Reading fails for a reason other than file absence.
        """
        try:
            payload = self._path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return UserSettings()
        except UnicodeError as error:
            raise SettingsFormatError("Settings must be UTF-8.") from error
        try:
            data = json.loads(payload, object_pairs_hook=_members)
            expected = {
                "format",
                "version",
                "language",
                "default_units",
                "recent_documents",
            }
            if isinstance(data, dict) and data.get("version") in (
                2,
                3,
                4,
                5,
                6,
                7,
                8,
                9,
                10,
                11,
            ):
                expected.add("decimal_convention")
            if isinstance(data, dict) and data.get("version") in (
                3,
                4,
                5,
                6,
                7,
                8,
                9,
                10,
                11,
            ):
                expected.add("animated_body_region_focus")
            if isinstance(data, dict) and data.get("version") in (
                4,
                5,
                6,
                7,
                8,
                9,
                10,
                11,
            ):
                expected.add("assessment_contexts")
            if isinstance(data, dict) and data.get("version") in (
                5,
                6,
                7,
                8,
                9,
                10,
                11,
            ):
                expected.add("gauge_markers")
            if isinstance(data, dict) and data.get("version") in (6, 7, 8, 9, 10, 11):
                expected.add("undo_limit")
            if isinstance(data, dict) and data.get("version") in (7, 8, 9, 10, 11):
                expected.update(("animated_risk_gauge", "animated_cumulative_damage"))
            if isinstance(data, dict) and data.get("version") in (8, 9, 10, 11):
                expected.add("import_profiles")
            if isinstance(data, dict) and data.get("version") in (9, 10, 11):
                expected.add("assessment_columns")
            if isinstance(data, dict) and data.get("version") == 10:
                # Read the retired version10 field solely to discard it, never as
                # a runtime/legacy option. Version11 saves no solver-choice key.
                expected.add("highs_single_tool")
            if not isinstance(data, dict) or set(data) != expected:
                raise SettingsFormatError("Invalid settings fields.")
            if (
                data["format"] != "ergotools.user-settings"
                or type(data["version"]) is not int
                or data["version"] not in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11)
            ):
                raise SettingsFormatError("Unsupported settings version.")
            if not isinstance(data["recent_documents"], list):
                raise SettingsFormatError("Recent documents must be an array.")
            contexts = data.get("assessment_contexts", [])
            if not isinstance(contexts, list) or any(
                not isinstance(row, list) for row in contexts
            ):
                raise SettingsFormatError("Assessment contexts must be arrays.")
            markers = data.get(
                "gauge_markers",
                asdict(GaugeMarkerSettings()),
            )
            if not isinstance(markers, dict) or set(markers) != {
                "show_ticks",
                "show_labels",
                "interval",
            }:
                raise SettingsFormatError("Invalid gauge marker fields.")
            return UserSettings(
                Language(data["language"]),
                MeasurementSystem(data["default_units"]),
                tuple(data["recent_documents"]),
                DecimalConvention(data.get("decimal_convention", ".")),
                data.get("animated_body_region_focus", True),
                tuple(tuple(item) for item in contexts),
                GaugeMarkerSettings(**markers),
                data.get("undo_limit", DEFAULT_UNDO_LIMIT),
                data.get("animated_risk_gauge", True),
                data.get("animated_cumulative_damage", True),
                decode_import_profiles(data.get("import_profiles", [])),
                decode_column_preferences(data.get("assessment_columns", [])),
            )
        except (ValueError, TypeError, RecursionError) as error:
            raise SettingsFormatError("Invalid user settings.") from error

    def save(self, settings: UserSettings) -> None:
        """Flush a temporary file before replacement; keep prior data on failure.

        Validate an existing file before replacement to avoid overwriting corrupt or
        unsupported versions. Directory fsync/power-loss recovery and concurrent writers
        are outside this initial contract. No project locations are read.

        Args:
            settings: Validated immutable preferences to write as version 10; project
                contents are not opened.

        Returns:
            None after temporary-file flush/fsync and same-directory atomic replacement.

        Raises:
            SettingsFormatError: Existing settings are damaged/unsupported and cannot be
                overwritten.
            OSError: Read, temporary write/fsync, replacement or cleanup fails.
        """
        self.load()
        payload = (
            json.dumps(
                {
                    "format": "ergotools.user-settings",
                    "version": 11,
                    "assessment_columns": [
                        asdict(p) for p in settings.assessment_columns
                    ],
                    "import_profiles": [asdict(p) for p in settings.import_profiles],
                    "animated_risk_gauge": settings.animated_risk_gauge,
                    "animated_cumulative_damage": settings.animated_cumulative_damage,
                    "undo_limit": settings.undo_limit,
                    "gauge_markers": {
                        "show_ticks": settings.gauge_markers.show_ticks,
                        "show_labels": settings.gauge_markers.show_labels,
                        "interval": settings.gauge_markers.interval,
                    },
                    "assessment_contexts": settings.assessment_contexts,
                    "animated_body_region_focus": settings.animated_body_region_focus,
                    "decimal_convention": settings.decimal_convention.value,
                    "language": settings.language.value,
                    "default_units": settings.default_units.value,
                    "recent_documents": settings.recent_documents,
                },
                ensure_ascii=True,
                sort_keys=True,
                indent=2,
            )
            + "\n"
        )
        temporary: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self._path.parent,
                prefix=".ergotools-settings-",
                delete=False,
            ) as stream:
                temporary = Path(stream.name)
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self._path)
            temporary = None
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)


def decode_import_profiles(value: object) -> tuple[ImportProfile, ...]:
    """Decode only explicit validated per-tool mapping preferences.

    Args:
        value: JSON list; no rows, paths, ranges or user assessment data are permitted.

    Returns:
        Immutable profiles; older settings supply an empty list.

    Raises:
        ValueError: A member, field, enum or profile choice is malformed.
    """
    if not isinstance(value, list):
        raise ValueError("Import preferences must be an array.")
    result = []
    for item in value:
        if (
            not isinstance(item, dict)
            or set(item)
            != {
                "kind",
                "delimiter",
                "encoding",
                "decimal",
                "thousands",
                "units",
                "header",
                "fields",
                "configured",
                "headers",
            }
            or not isinstance(item["fields"], list)
            or not isinstance(item["headers"], list)
        ):
            raise ValueError("Invalid import preference fields.")
        result.append(
            ImportProfile(
                kind=AssessmentKind(item["kind"]),
                delimiter=item["delimiter"],
                encoding=item["encoding"],
                decimal=DecimalConvention(item["decimal"]),
                thousands=item["thousands"],
                units=MeasurementSystem(item["units"]),
                header=item["header"],
                fields=tuple(item["fields"]),
                configured=item["configured"],
                headers=tuple(item["headers"]),
            )
        )
    return tuple(result)


def decode_column_preferences(value: object) -> tuple[AssessmentColumns, ...]:
    """Decode strict personal presentation choices without dropping foreign fields.

    Args:
        value: JSON array of exact kind/hidden objects; no assessment data is present.

    Returns:
        Immutable validated per-tool optional column choices.

    Raises:
        ValueError: Payload shape, tool or optional-field choices are invalid.
    """
    if not isinstance(value, list):
        raise ValueError("Column preferences must be an array.")
    result = []
    for item in value:
        if (
            not isinstance(item, dict)
            or set(item) != {"kind", "hidden"}
            or not isinstance(item["hidden"], list)
        ):
            raise ValueError("Invalid column preference fields.")
        result.append(
            AssessmentColumns(AssessmentKind(item["kind"]), tuple(item["hidden"]))
        )
    return tuple(result)
