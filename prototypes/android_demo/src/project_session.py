"""Mobile project workspace and recent catalog, independent of Flet and Android.

Native files remain complete desktop-compatible SQLite projects. Edits target an
app-private working copy; explicit Save atomically publishes a tablet copy. System
picker import/export is a UI boundary: content URIs are never treated as paths.
The JSON catalog is application state, not a change to the ErgoTools schema.
"""

import json
import os
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from demo_service import create_project
from mobile_history import ProjectChange, SavedMarker

from ergotools.application.session import DocumentKey, DocumentSession
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.project import ProjectMetadata
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile


def atomic_write(path: Path, data: bytes) -> None:
    """Publish bytes through a flushed sibling and atomic replacement.

    Args:
        path: Owned destination whose parent exists.
        data: Complete replacement, never a partial database stream.

    Returns:
        None; failures preserve the prior destination.
    """
    temporary = path.with_name(path.name + ".pending")
    try:
        with temporary.open("wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def project_info(path: Path) -> dict:
    """Validate a current native file and project its home-screen information.

    Args:
        path: Candidate native project, including imported private staging.

    Returns:
        Project title, units, worker count and assessment count.
    """
    with AssessmentProjectFile.open(path) as project:
        entries = project.list_assessments()
        for entry in entries:
            project.load(entry.document)
        return {
            "title": project.metadata.title,
            "units": project.metadata.default_units.value,
            "workers": len(project.load_hierarchy().work.workers),
            "assessments": len(entries),
        }


class ProjectSession:
    """Own one recoverable workspace and at most ten recent tablet projects.

    Attributes:
        folder: Private mobile storage, never a user-selected external directory.
        working: Editable native copy; explicitly separate from the last Save.
        state: Persisted catalog and active identity, including unsaved status.
    """

    def __init__(self, folder: Path) -> None:
        """Restore catalog without automatically creating or saving a project.

        Args:
            folder: App-private storage retained across APK updates.

        Returns:
            None; a malformed catalog raises instead of hiding existing files.
        """
        self.folder = folder
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "projects").mkdir(exist_ok=True)
        self.working = folder / "workspace.ergprj"
        self.catalog = folder / "projects.json"
        self.state = (
            json.loads(self.catalog.read_text())
            if self.catalog.exists()
            else {"active": None, "recent": []}
        )
        if self.state["active"] and not self.working.exists():
            raise ValueError(
                "The active tablet workspace is missing. Saved "
                "projects remain in Recent projects."
            )
        self.reset_history()

    @property
    def active(self) -> dict | None:
        """Return active identity and save status, or None on first launch.

        Args:
            None.

        Returns:
            Current catalog record; callers must not mutate it directly.
        """
        return self.state["active"]

    def persist(self) -> None:
        """Atomically store app state after a successful workspace operation.

        Args:
            None.

        Returns:
            None; project data itself remains in the native workspace.
        """
        atomic_write(self.catalog, json.dumps(self.state, indent=2).encode())

    def activate(
        self,
        data: bytes,
        name: str,
        origin: str,
        *,
        saved: bool = False,
        identity: str | None = None,
    ) -> None:
        """Validate before switching, preserving the old workspace on invalid import.

        Args:
            data: Complete native file bytes from the system picker or recent copy.
            name: Human-readable file name, never used as a filesystem path.
            origin: Display-only explanation of where this tablet copy came from.
            saved: Whether these exact bytes are already saved in the tablet catalog.
            identity: Existing recent identity, otherwise a new private UUID.

        Returns:
            None; native schema and unrelated assessments remain intact.
        """
        candidate = self.folder / "candidate.ergprj"
        try:
            atomic_write(candidate, data)
            project_info(candidate)
            atomic_write(self.working, candidate.read_bytes())
        finally:
            candidate.unlink(missing_ok=True)
        # Reopening an unchanged exported file reuses its tablet entry instead of
        # accumulating identical recent copies. Different bytes remain independent.
        if identity is None and origin.startswith("Imported from "):
            for record in self.state["recent"]:
                saved_path = self.folder / "projects" / f"{record['id']}.ergprj"
                if (
                    record["name"] == Path(name).name
                    and saved_path.exists()
                    and saved_path.read_bytes() == data
                ):
                    identity, saved = record["id"], True
                    break
        self.state["active"] = {
            "id": identity or uuid4().hex,
            "name": Path(name).name,
            "origin": origin,
            "dirty": not saved,
        }
        self.persist()
        self.reset_history()

    def create(
        self, title: str, units: str = "metric", *, sample: bool = False
    ) -> None:
        """Start an unsaved empty project or an explicit fictional sample.

        Args:
            title: Nonblank project title, independent of saved file location.
            units: Existing MeasurementSystem value, metric or imperial.
            sample: Create the one-worker LiFFT example instead of empty data.

        Returns:
            None; the old workspace is replaced only after successful creation.
        """
        title = title.strip()
        if not title:
            raise ValueError("Enter a project name.")
        temporary = self.folder / "new_project.ergprj"
        temporary.unlink(missing_ok=True)
        try:
            if sample:
                create_project(temporary)
            else:
                with AssessmentProjectFile.create_empty(
                    temporary,
                    ProjectMetadata(uuid4().hex, title, MeasurementSystem(units)),
                ):
                    pass
            self.activate(
                temporary.read_bytes(), f"{title}.ergprj", "Created on this tablet"
            )
        finally:
            temporary.unlink(missing_ok=True)

    def mark_changed(self) -> None:
        """Record accepted native edits as unsaved, including across app restart.

        Args:
            None.

        Returns:
            None; Save is the only publication to the recent saved project.
        """
        if self.active:
            self.active["dirty"] = True
            if self.history is not None:
                self.history.amend_current(self.working.read_bytes())
                self.history.mark_unsaved()
            self.persist()

    def save(self, *, name: str | None = None, new_copy: bool = False) -> None:
        """Save complete workspace bytes to the managed tablet project catalog.

        Args:
            name: Optional export-selected file name for Save As.
            new_copy: Give Save As an independent recent identity.

        Returns:
            None; no recalculation, rounding, filtering or schema conversion occurs.
        """
        if not self.active:
            raise ValueError("Open or create a project first.")
        project_info(self.working)
        # Synchronize accepted legacy M01 adapter writes before the shared clean
        # marker is committed; new mobile edits use change() for chronology.
        if self.history.state != self.working.read_bytes():
            self.history.amend_current(self.working.read_bytes())
        record = dict(self.active)
        if new_copy:
            record["id"] = uuid4().hex
        if name:
            record["name"] = Path(name).name
        atomic_write(
            self.folder / "projects" / f"{record['id']}.ergprj",
            self.working.read_bytes(),
        )
        record["dirty"] = False
        record["saved_at"] = datetime.now().isoformat(timespec="seconds")
        self.state["active"] = record
        self.state["recent"] = [
            dict(record),
            *[r for r in self.state["recent"] if r["id"] != record["id"]],
        ][:10]
        self.persist()
        self.history.save(
            SavedMarker(self.folder / "projects" / f"{record['id']}.ergprj")
        )

    def open_recent(self, identity: str) -> None:
        """Restore one explicitly saved tablet project without discarding others.

        Args:
            identity: Exact UUID offered by the recent catalog, not a supplied path.

        Returns:
            None; a missing file raises and preserves the current workspace.
        """
        record = next(r for r in self.state["recent"] if r["id"] == identity)
        self.activate(
            (self.folder / "projects" / f"{identity}.ergprj").read_bytes(),
            record["name"],
            record["origin"],
            saved=True,
            identity=identity,
        )

    def discard(self) -> None:
        """Discard current edits, restoring the saved version when one exists.

        Args:
            None.

        Returns:
            None; an unsaved new/imported project closes, saved projects reopen.
        """
        if self.active and any(
            r["id"] == self.active["id"] for r in self.state["recent"]
        ):
            self.open_recent(self.active["id"])
        else:
            self.state["active"] = None
            self.persist()
            self.working.unlink(missing_ok=True)
            self.reset_history()

    def reset_history(self) -> None:
        """Start a fresh 25-action timeline when opening or closing a project.

        Args:
            None.

        Returns:
            None; changing projects never replays another project's snapshots.
        """
        self.history = None
        if self.active:
            self.history = DocumentSession(
                DocumentKey(self.active["id"], "tablet-project"),
                self.working.read_bytes(),
                persisted=not self.active["dirty"],
            )
            self.history.set_history_limit(25)

    def change(self, label: str, mutation: Callable[[], object]) -> object:
        """Record one accepted operation and restore working bytes on failure.

        Args:
            label: User action, visible in Undo/Redo tooltips.
            mutation: Adapter operation against the private native workspace.

        Returns:
            Mutation's result; unchanged native bytes do not create a history entry.
        """
        if self.history is None:
            raise ValueError("Open a project before editing.")
        before = self.working.read_bytes()
        if self.history.state != before:
            # Legacy M01 callers can mark accepted changes outside the timeline.
            self.history.amend_current(before)
        try:
            result = mutation()
            after = self.working.read_bytes()
            self.history.execute(
                ProjectChange(self.history.document, label, before, after)
            )
        except Exception:
            atomic_write(self.working, before)
            raise
        self.active["dirty"] = self.history.is_dirty
        self.persist()
        return result

    def replay(self, *, redo: bool = False) -> None:
        """Replay the shared project timeline without changing saved project bytes.

        Args:
            redo: Replay forward instead of backward.

        Returns:
            None; failed file publication restores the original timeline cursor.
        """
        if self.history is None:
            return
        moved = self.history.redo() if redo else self.history.undo()
        if not moved:
            return
        try:
            atomic_write(self.working, self.history.state)
        except Exception:
            self.history.undo() if redo else self.history.redo()
            raise
        self.active["dirty"] = self.history.is_dirty
        self.persist()
