"""Project-switch ownership and failure ordering with fake and real repositories.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import tempfile
import unittest
from collections.abc import Callable
from pathlib import Path

from ergotools.application.assessments.lifft_commands import AddLifftTask
from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.project_workspace import ProjectWorkspace
from ergotools.application.session import DocumentKey
from ergotools.application.settings import UserSettings
from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.project import ProjectMetadata
from ergotools.infrastructure.project_file import ProjectFile
from ergotools.infrastructure.settings_store import JsonSettingsStore
from ergotools.presentation.localization import Language, Translator


class Preferences:
    """Minimal settings adapter with observable writes and injected failure."""

    def __init__(self) -> None:
        """Start with defaults and successful persistence.

        Args:
            None.

        Returns:
            None.
        """
        self.value = UserSettings()
        self.fail = False
        self.writes = 0

    def load(self) -> UserSettings:
        """Return the last successfully persisted value.

        Args:
            None.

        Returns:
            Last successfully saved immutable UserSettings value; this read has no
            side effects and does not consult the filesystem.
        """
        return self.value

    def save(self, settings: UserSettings) -> None:
        """Fail before changing the value when requested.

        Args:
            settings: Immutable synthetic preferences/recent-locations value to persist.

        Returns:
            None.

        Raises:
            OSError: The controlled adapter/resource/publication failure is injected by
                this scenario.
        """
        if self.fail:
            raise OSError("settings failure")
        self.value = settings
        self.writes += 1


class Handle:
    """Owned project probe exposing save/close failures and load callbacks."""

    def __init__(self, project_id: str) -> None:
        """Provide two stored documents and a fresh open connection state.

        Args:
            project_id: Stable synthetic project identity; no caption-based ownership
                inference is allowed.

        Returns:
            None.
        """
        self.metadata = ProjectMetadata(
            project_id, project_id, MeasurementSystem.METRIC
        )
        self.values = {
            name: LifftDraft(MeasurementSystem.METRIC) for name in ("a", "b")
        }
        self.closed = False
        self.fail_save = False
        self.fail_close = False
        self.on_load: Callable[[], object] | None = None

    def load(self, document: DocumentKey) -> LifftDraft:
        """Read only from an open handle and invoke any injected callback.

        Args:
            document: Exact project/document key whose state is read or written in
                isolation.

        Returns:
            Known immutable LiFFT draft after the configured read callback runs;
            deliberately injected callback failures propagate to the caller.

        Raises:
            RuntimeError: The controlled reentrancy/owned-resource failure is triggered.
        """
        if self.closed:
            raise RuntimeError("closed")
        if self.on_load is not None:
            self.on_load()
        return self.values[document.document_id]

    def save(self, document: DocumentKey, state: LifftDraft) -> None:
        """Persist source state or fail without changing stored data.

        Args:
            document: Exact project/document key whose state is read or written in
                isolation.
            state: Immutable draft snapshot being validated, loaded or persisted by this
                test callback.

        Returns:
            None.

        Raises:
            OSError: The controlled adapter/resource/publication failure is injected by
                this scenario.
        """
        if self.fail_save:
            raise OSError("save failed")
        self.values[document.document_id] = state

    def close(self) -> None:
        """Close successfully or retain an open handle for a later retry.

        Args:
            None.

        Returns:
            None.

        Raises:
            OSError: The controlled adapter/resource/publication failure is injected by
                this scenario.
        """
        if self.fail_close:
            raise OSError("close failed")
        self.closed = True


class WorkspaceTests(unittest.TestCase):
    """Verify active ownership, candidate cleanup and separate post-open warnings."""

    def setUp(self) -> None:
        """Open a clean project using a factory that returns fresh owned handles.

        Args:
            None.

        Returns:
            None.
        """
        self.handles: list[Handle] = []
        self.callback: Callable[[], object] | None = None
        self.preferences = Preferences()
        self.workspace = ProjectWorkspace(self.open_handle, self.preferences)
        self.workspace.switch("first", "a")
        self.old = self.handles[0]

    def open_handle(self, location: str) -> Handle:
        """Record each acquired handle and attach configured candidate callbacks.

        Args:
            location: Disposable project location provided to the injected
                adapter/factory.

        Returns:
            Fresh owned test handle recorded for release/callback assertions; never an
            operational connection.

        Raises:
            OSError: The controlled adapter/resource/publication failure is injected by
                this scenario.
        """
        if location == "unreadable":
            raise OSError("open failure")
        handle = Handle(location)
        handle.on_load = self.callback
        self.handles.append(handle)
        return handle

    def edit(self) -> None:
        """Make a concrete LiFFT edit through the active document session.

        Args:
            None.

        Returns:
            None.
        """
        active = self.workspace.active
        active.execute(AddLifftTask(active.document, LifftTask("pending"), 0))

    def test_dirty_cancel_and_missing_consent_acquire_nothing(self) -> None:
        """Do not open targets, save preferences or close handles without consent.

        Args:
            None.

        Returns:
            None.
        """
        self.edit()
        for choice in (None, CloseChoice.CANCEL):
            self.assertFalse(
                self.workspace.switch("second", "a", choice=choice).completed
            )
            self.assertFalse(self.workspace.close(choice=choice).completed)
        self.assertEqual(len(self.handles), 1)
        self.assertEqual(self.preferences.writes, 1)
        self.assertFalse(self.old.closed)

    def test_save_switch_commits_old_draft_and_releases_old_handle(self) -> None:
        """Successful activation owns the target and starts a clean document history.

        Args:
            None.

        Returns:
            None.
        """
        self.edit()
        expected = self.workspace.active.state
        result = self.workspace.switch("second", "a", choice=CloseChoice.SAVE)
        self.assertTrue(result.completed)
        self.assertEqual(result.warning_keys, ())
        self.assertEqual(self.old.values["a"], expected)
        self.assertTrue(self.old.closed)
        self.assertEqual(self.workspace.location, "second")
        self.assertFalse(self.workspace.active.is_dirty)
        self.assertEqual(self.preferences.value.recent_documents, ("second", "first"))

    def test_discard_switch_does_not_persist_old_edit(self) -> None:
        """Discard affects only pending state and closes the prior connection.

        Args:
            None.

        Returns:
            None.
        """
        self.edit()
        self.workspace.switch("second", "a", choice=CloseChoice.DISCARD)
        self.assertEqual(self.old.values["a"].tasks, ())
        self.assertTrue(self.old.closed)

    def test_failed_factory_keeps_current_session_and_resources(self) -> None:
        """No candidate exists to clean up when opening the target fails.

        Args:
            None.

        Returns:
            None.
        """
        self.edit()
        active = self.workspace.active
        with self.assertRaises(OSError):
            self.workspace.switch("unreadable", "a", choice=CloseChoice.SAVE)
        self.assertIs(self.workspace.active, active)
        self.assertTrue(active.is_dirty)
        self.assertFalse(self.old.closed)
        self.assertEqual(self.old.values["a"].tasks, ())

    def test_failed_document_load_closes_candidate_without_saving_old(self) -> None:
        """Candidate validation must precede changes to the current document.

        Args:
            None.

        Returns:
            None.
        """
        self.edit()
        active = self.workspace.active
        with self.assertRaises(KeyError):
            self.workspace.switch("second", "missing", choice=CloseChoice.SAVE)
        self.assertTrue(self.handles[-1].closed)
        self.assertIs(self.workspace.active, active)
        self.assertTrue(active.is_dirty)
        self.assertFalse(self.old.closed)

    def test_failed_old_save_closes_candidate_and_allows_retry(self) -> None:
        """The target never becomes active until the requested save succeeds.

        Args:
            None.

        Returns:
            None.
        """
        self.edit()
        self.old.fail_save = True
        active = self.workspace.active
        with self.assertRaises(OSError):
            self.workspace.switch("second", "a", choice=CloseChoice.SAVE)
        self.assertTrue(self.handles[-1].closed)
        self.assertIs(self.workspace.active, active)
        self.assertFalse(self.old.closed)
        self.old.fail_save = False
        self.assertTrue(
            self.workspace.switch("second", "a", choice=CloseChoice.SAVE).completed
        )

    def test_same_file_selection_preserves_handle_and_same_document_history(
        self,
    ) -> None:
        """Same-file document routing must never close its shared repository.

        Args:
            None.

        Returns:
            None.
        """
        self.edit()
        active = self.workspace.active
        self.assertTrue(self.workspace.switch("first", "a").completed)
        self.assertIs(self.workspace.active, active)
        self.workspace.switch("first", "b", choice=CloseChoice.SAVE)
        self.assertEqual(len(self.handles), 1)
        self.assertFalse(self.old.closed)
        self.assertEqual(self.workspace.active.document.document_id, "b")
        with self.assertRaises(KeyError):
            self.workspace.switch("first", "missing")
        self.assertFalse(self.old.closed)

    def test_close_failure_is_a_retryable_warning_after_activation(self) -> None:
        """Do not misreport a successful switch as failed due to old-handle cleanup.

        Args:
            None.

        Returns:
            None.
        """
        self.old.fail_close = True
        self.preferences.fail = True
        outcome = self.workspace.switch("second", "a")
        self.assertTrue(outcome.completed)
        self.assertEqual(
            set(outcome.warning_keys),
            {"project.cleanup_failed", "settings.recent_update_failed"},
        )
        self.assertEqual(self.workspace.location, "second")
        self.assertEqual(self.workspace.pending_release_count, 1)
        self.assertEqual(self.workspace.retry_releases(), 1)
        self.old.fail_close = False
        self.assertEqual(self.workspace.retry_releases(), 0)
        self.assertFalse(self.handles[-1].closed)
        for language in Language:
            self.assertTrue(Translator(language).text("project.cleanup_failed"))

    def test_candidate_cleanup_failure_does_not_mask_original_error(self) -> None:
        """Retain candidate ownership for retry while propagating the load failure.

        Args:
            None.

        Returns:
            None.
        """

        def fail_candidate_close() -> None:
            """Mark the just-acquired candidate handle to fail release.

            Mark the just-acquired candidate handle to fail release, preserving the
            primary activation failure and retry ownership.

            Args:
                None.

            Returns:
                None.
            """
            self.handles[-1].fail_close = True

        self.callback = fail_candidate_close
        with self.assertRaises(KeyError):
            self.workspace.switch("second", "missing")
        self.assertEqual(self.workspace.pending_release_count, 1)
        self.assertEqual(self.workspace.location, "first")
        self.handles[-1].fail_close = False
        self.assertEqual(self.workspace.retry_releases(), 0)

    def test_close_save_failure_keeps_current_and_retry_releases_it(self) -> None:
        """Close observes the same save-before-release ordering as switch.

        Args:
            None.

        Returns:
            None.
        """
        self.edit()
        self.old.fail_save = True
        with self.assertRaises(OSError):
            self.workspace.close(choice=CloseChoice.SAVE)
        self.assertIsNotNone(self.workspace.active)
        self.old.fail_save = False
        self.assertTrue(self.workspace.close(choice=CloseChoice.SAVE).completed)
        self.assertIsNone(self.workspace.active)
        self.assertIsNone(self.workspace.location)
        self.assertTrue(self.old.closed)
        self.assertTrue(self.workspace.close().completed)

    def test_failed_close_release_retains_retry_ownership(self) -> None:
        """A detached project remains tracked if its close operation raises.

        Args:
            None.

        Returns:
            None.
        """
        self.old.fail_close = True
        outcome = self.workspace.close()
        self.assertTrue(outcome.completed)
        self.assertEqual(outcome.warning_keys, ("project.cleanup_failed",))
        self.assertIsNone(self.workspace.active)
        self.old.fail_close = False
        self.assertEqual(self.workspace.retry_releases(), 0)

    def test_invalid_inputs_and_reentrant_callbacks_do_not_replace_session(
        self,
    ) -> None:
        """Reject unknown intent and recursive resource transitions.

        Args:
            None.

        Returns:
            None.
        """
        with self.assertRaises(ValueError):
            self.workspace.switch("", "a")
        with self.assertRaises(ValueError):
            self.workspace.close(choice="discard")
        self.callback = self.workspace.close
        with self.assertRaises(RuntimeError):
            self.workspace.switch("second", "a")
        self.assertEqual(self.workspace.location, "first")
        self.assertTrue(self.handles[-1].closed)

    def test_edit_during_candidate_load_prevents_stale_discard(self) -> None:
        """A callback cannot make the prior consent apply to a newly edited draft.

        Args:
            None.

        Returns:
            None.
        """
        self.callback = self.edit
        with self.assertRaises(RuntimeError):
            self.workspace.switch("second", "a", choice=CloseChoice.DISCARD)
        self.assertEqual(self.workspace.location, "first")
        self.assertTrue(self.workspace.active.is_dirty)
        self.assertTrue(self.handles[-1].closed)

    def test_real_two_file_switch_saves_old_state_and_updates_history(self) -> None:
        """Use real project and settings files under disposable test ownership.

        Args:
            None.

        Returns:
            None.
        """
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = [root / "one.sqlite", root / "two.sqlite"]
            for index, path in enumerate(paths):
                metadata = ProjectMetadata(
                    str(index), str(index), MeasurementSystem.METRIC
                )
                with ProjectFile.create(path, metadata) as project:
                    project.save(
                        DocumentKey(str(index), "a"),
                        LifftDraft(MeasurementSystem.METRIC),
                    )
            settings = JsonSettingsStore(root / "settings.json")
            workspace = ProjectWorkspace(
                lambda location: ProjectFile.open(Path(location)), settings
            )
            try:
                workspace.switch(str(paths[0]), "a")
                active = workspace.active
                active.execute(AddLifftTask(active.document, LifftTask("saved"), 0))
                expected = active.state
                workspace.switch(str(paths[1]), "a", choice=CloseChoice.SAVE)
                with ProjectFile.open(paths[0]) as previous:
                    self.assertEqual(previous.load(DocumentKey("0", "a")), expected)
                self.assertEqual(
                    settings.load().recent_documents, (str(paths[1]), str(paths[0]))
                )
            finally:
                workspace.close(choice=CloseChoice.DISCARD)
