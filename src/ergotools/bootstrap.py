"""Compose the integrated desktop from application ports and concrete adapters.

Composition-root exception to ordinary layer dependency rules: create Qt windows,
native storage, resources, settings, solver and optional renderer adapters. Project
migration is dispatched through an external-process adapter; this module never
imports conversion readers. UI interactions remain in presenters/windows and
scientific calculations remain in the domain/application layers.
"""

import argparse
import sys
from collections.abc import Callable
from dataclasses import replace
from datetime import date
from functools import partial
from pathlib import Path

from PyQt5.QtCore import QCoreApplication, QStandardPaths, QTimer
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QApplication, QWidget

from ergotools.application.assessment_export import SummaryExportRow, saved_summary_rows
from ergotools.application.contracts.body_renderer import BodyRenderer
from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.gauge_preferences import GaugeMarkerSettings
from ergotools.application.jrot_prototype import (
    PrototypeCatalog,
    read_prototype_catalog,
)
from ergotools.application.plot_access import PlotRepository
from ergotools.application.project_editing import ProjectEditingSession
from ergotools.application.project_workspace import ProjectWorkspace
from ergotools.application.rotation_access import RotationRepository
from ergotools.application.session import DocumentKey
from ergotools.application.settings import Language, SettingsStore
from ergotools.domain.assessments.document import AssessmentDraft, AssessmentKind
from ergotools.domain.assessments.lifft_draft import LifftDraft
from ergotools.domain.decimal_convention import DecimalConvention
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.project import ProjectMetadata
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.infrastructure.plant_image_import import import_plant_image
from ergotools.infrastructure.plot_csv_file import write_plot_csv
from ergotools.infrastructure.project_migration import ExternalProjectMigration
from ergotools.infrastructure.pulp_rotation_optimizer import PulpRotationOptimizer
from ergotools.infrastructure.resources import read_asset
from ergotools.infrastructure.settings_store import JsonSettingsStore
from ergotools.infrastructure.summary_export import load_summary_rows, write_summary_csv
from ergotools.presentation.desktop.job_management_dialog import JobManagementDialog
from ergotools.presentation.desktop.jrot_prototype_dialog import JrotPrototypeDialog
from ergotools.presentation.desktop.lifft_presenter import LifftPresenter
from ergotools.presentation.desktop.lifft_window import LifftWindow
from ergotools.presentation.desktop.menu_icon_style import install_menu_icon_style
from ergotools.presentation.desktop.plot_window import PlotWindow
from ergotools.presentation.desktop.rotation_dialog import RotationDialog
from ergotools.presentation.desktop.theme.dialogs import install_dialog_theme


def application_settings_path() -> Path:
    """Locate per-user Qt application configuration independently of launch folder.

    Args:
        None.

    Returns:
        Per-user settings.json path supplied by Qt, independent of cwd; no directory or
        file is created here.

    Raises:
        OSError: Qt supplies no per-user application configuration directory.
    """
    QCoreApplication.setApplicationName("ErgoTools")
    QCoreApplication.setOrganizationName("ErgoTools")
    directory = QStandardPaths.writableLocation(QStandardPaths.AppConfigLocation)
    if not directory:
        raise OSError("No per-user application configuration directory is available.")
    return Path(directory) / "settings.json"


def list_lifft_documents(location: str) -> tuple[str, ...]:
    """Read supported document identities with a separately owned closed connection.

    Args:
        location: Native project path; open a separate owned connection and close it
            before returning.

    Returns:
        Saved LiFFT document IDs in repository order; no recalculation or writes.

    Raises:
        OSError: The project cannot be opened.
        ValueError: The native project format or metadata is invalid.
    """
    with AssessmentProjectFile.open(Path(location)) as project:
        return tuple(
            entry.document.document_id
            for entry in project.list_assessments()
            if entry.kind is AssessmentKind.LIFFT
        )


def list_desktop_documents(location: str) -> tuple[str, ...]:
    """Read migrated LiFFT/DUET/ST document identities with an owned connection.

    Args:
        location: Native project path, opened only for the duration of this listing.

    Returns:
        Saved supported LiFFT/DUET/ST document IDs in repository order, without
        filtering historical versions.

    Raises:
        OSError: The project cannot be opened.
        ValueError: The native project format or metadata is invalid.
    """
    with AssessmentProjectFile.open(Path(location)) as project:
        return tuple(
            entry.document.document_id
            for entry in project.list_assessments()
            if entry.kind
            in (AssessmentKind.LIFFT, AssessmentKind.DUET, AssessmentKind.TST)
        )


def desktop_document_options(
    location: str, language: Language
) -> tuple[tuple[str, str], ...]:
    """Describe exact saved owners/versions in one read; preserve opaque IDs.

    Context and assignment/version distinguish repeated assessments. Unbound development
    documents retain their identity as a readable fallback. No source is recalculated,
    rewritten or relabelled in storage.

    Args:
        location: Native project path to inspect using one separately owned connection.
        language: Caller UI-language identity; original names/context identities and
            branded tool labels remain literal.

    Returns:
        Ordered pairs of opaque document ID and worker/workplace/version description;
        unbound documents use their ID as a fallback.

    Raises:
        OSError: The native project cannot be opened.
        ValueError: Native metadata or relationships are invalid.
        KeyError: An ownership link lacks its required assignment or worker record.
    """
    with AssessmentProjectFile.open(Path(location)) as project:
        entries = project.list_assessments()
        if not project.supports_assignment_history:
            return tuple(
                (e.document.document_id, e.document.document_id) for e in entries
            )
        history = {entry.document_id: entry for entry in project.load_history().entries}
        jobs = project.load_jobs()
        assignments = {a.assignment_id: a for a in jobs.assignments}
        workers = {w.worker_id: w for w in project.load_hierarchy().work.workers}
        options = []
        for entry in entries:
            identity = entry.document.document_id
            owner = history.get(identity)
            label = {
                AssessmentKind.LIFFT: "LiFFT",
                AssessmentKind.DUET: "DUET",
                AssessmentKind.TST: "ST",
            }[entry.kind] + " · "
            if owner is None:
                label += identity
            elif owner.assignment_id is None:
                label += owner.worker_id
            else:
                assignment = assignments[owner.assignment_id]
                context = assignment.worker
                worker = workers[context.worker_id]
                name = ", ".join(n for n in (worker.last_name, worker.first_name) if n)
                place = context.workplace
                label += (
                    f"{worker.worker_id} ({name}) · "
                    + "/".join(
                        (
                            place.plant_name,
                            place.section_name,
                            place.line_name,
                            place.station_id,
                            place.shift_id,
                        )
                    )
                    + f" · #{owner.assignment_id}"
                )
            options.append((identity, label))
        return tuple(options)


def create_window(
    settings_path: Path,
    *,
    original_controls: bool = False,
    original_navigation: bool = False,
    enable_vtk: bool = False,
) -> LifftWindow:
    """Compose a window after QApplication exists; caller chooses preferences path.

    Args:
        settings_path: Per-user or explicit diagnostic preferences path; existing
            preferences are read during composition.
        original_controls: Enable migrated original task controls instead of the
            retained diagnostic preview controls.
        original_navigation: Enable integrated original navigation, all tools and
            optional external conversion.
        enable_vtk: Construct the native VTK body renderer; False supports isolated
            nonnative UI checks.

    Returns:
        Composed, translated and initially refreshed integrated/diagnostic window;
        caller owns showing and closing it.

    Raises:
        OSError: Preferences, packaged assets or renderer staging cannot be read.
        ValueError: Stored settings, packaged images or model meshes are invalid.

    Requires an existing QApplication on the GUI thread. The injected result-provider
    closure is used only on later saves, after window construction. Preference-control
    synchronization blocks signals before the final translation/refresh.
    """
    app = QApplication.instance()
    assert isinstance(app, QApplication)
    install_menu_icon_style(app)
    install_dialog_theme(app)
    settings_store = JsonSettingsStore(settings_path)
    preferences = settings_store.load()
    workspace: ProjectWorkspace[AssessmentDraft] = ProjectWorkspace(
        lambda location: AssessmentProjectFile.open(Path(location)),
        settings_store,
        unified_saving=original_navigation,
        # Queried only on later saves, after the window and presenters exist.
        result_provider=lambda: window.current_result_snapshot(),
        creator=lambda location, metadata, document_id, source: (
            AssessmentProjectFile.create_with_document(
                Path(location), metadata, document_id, source, format_version=19
            )
        ),
        empty_creator=lambda location, metadata: AssessmentProjectFile.create_empty(
            Path(location), metadata
        ),
    )

    def open_project_summary(
        location: str, kind: AssessmentKind
    ) -> tuple[SummaryExportRow, ...]:
        """Export accepted project-session data while keeping file readers independent.

        Args:
            location: Requested project path, compared with the open workspace.
            kind: Ergonomic model whose exact accepted inputs/results are exported.

        Returns:
            Current private summaries for this project; ordinary file summaries for
            other paths. Export never writes or commits the project.
        """
        editing = workspace.editing
        if (
            editing is not None
            and location == workspace.location
            and isinstance(editing.repository, AssessmentProjectFile)
        ):
            return saved_summary_rows(editing.repository, kind)
        return load_summary_rows(location, kind)

    renderer_factory = None
    if enable_vtk:
        from ergotools.presentation.desktop.rendering.vtk_body_renderer import (
            VtkBodyRenderer,
        )

        def renderer_factory(parent: QWidget) -> tuple[QWidget, BodyRenderer]:
            """Construct one native scene behind the injected portable renderer port.

            Args:
                parent: Qt parent that owns the viewport widget; invoke on the GUI
                    thread after QApplication exists.

            Returns:
                Viewport widget and its portable BodyRenderer port backed by one owned
                VTK scene.

            Raises:
                OSError: Packaged models or temporary staging cannot be accessed.
                ValueError: An anatomical model fails mesh decoding.
            """
            renderer = VtkBodyRenderer(
                parent, lambda name: read_asset("models/" + name)
            )
            return renderer.widget, renderer

    window = LifftWindow(
        LifftPresenter(workspace),
        load_icons(),
        list_desktop_documents if original_navigation else list_lifft_documents,
        settings_store=settings_store,
        document_options=desktop_document_options if original_navigation else None,
        project_conversion=ExternalProjectMigration() if original_navigation else None,
        user_guides={
            language: read_asset(f"documents/user_guide_{language.value}.html")
            for language in Language
        },
        authors_logo=read_asset("images/ergotools_main_logo.png"),
        summary_loader=open_project_summary,
        csv_writer=write_summary_csv,
        plot_opener=partial(
            open_plot,
            settings_store=settings_store,
            editing_provider=lambda: workspace.editing,
        ),
        rotation_opener=partial(
            open_rotation, editing_provider=lambda: workspace.editing
        ),
        developer_opener=partial(open_jrot_prototype, workspace=workspace),
        original_controls=original_controls,
        original_navigation=original_navigation,
        renderer_factory=renderer_factory,
    )
    window.presenter.system = preferences.default_units
    window.language = preferences.language
    window.presenter.convention = preferences.decimal_convention
    for combo, index in (
        (window.units, list(MeasurementSystem).index(preferences.default_units)),
        (window.languages, list(Language).index(preferences.language)),
        (window.decimal, list(DecimalConvention).index(preferences.decimal_convention)),
    ):
        combo.blockSignals(True)
        combo.setCurrentIndex(index)
        combo.blockSignals(False)
    window.translate()
    window.refresh()
    return window


def open_jrot_prototype(
    parent: QWidget, *, workspace: ProjectWorkspace[AssessmentDraft]
) -> None:
    """Compose a disposable developer preview from detached read-only catalogs.

    Args:
        parent: Main GUI owner; no production editor or mutation port enters the view.
        workspace: Composition-owned project session, read only to obtain a snapshot.

    Returns:
        None after modal closure and safe solver/widget cleanup. No project/settings
        write occurs; an empty workspace uses clearly labeled sample data.
    """
    metadata = workspace.project_metadata
    catalog = (
        read_prototype_catalog(
            workspace.rotation_repository(), metadata.title if metadata else "Project"
        )
        if workspace.supports_rotations
        else PrototypeCatalog("Sample workspace · no project loaded")
    )
    dialog = JrotPrototypeDialog(catalog, PulpRotationOptimizer(), load_icons(), parent)
    try:
        dialog.exec()
    finally:
        dialog.close()
        dialog.deleteLater()


def open_rotation(
    repository: RotationRepository,
    language: Language,
    parent: QWidget,
    *,
    editing_provider: Callable[[], ProjectEditingSession | None] | None = None,
) -> None:
    """Compose original modal JROT over a borrowed workspace project handle.

    The dialog owns solver workers/comparison children until actual completion. Closing
    does not close the borrowed repository or implicitly save assessments.

    Args:
        editing_provider: Optional shared private editing owner for the open project.
        repository: Borrowed workspace rotation project handle; closing the modal never
            closes this repository.
        language: Explicit UI translation language.
        parent: Owning desktop widget; all modal/solver lifecycle actions use the GUI
            thread.

    Returns:
        None after the modal workflow exits and dialog cleanup is requested; solver
        completion remains owned by the dialog.

    Raises:
        OSError: Required packaged assets cannot be loaded.
        ValueError: A packaged icon is not decodable.
    """
    dialog = RotationDialog(
        repository,
        load_icons(),
        language=language,
        optimizer=PulpRotationOptimizer(),
        parent=parent,
        editing=editing_provider() if editing_provider else None,
    )
    try:
        dialog.exec()
    finally:
        dialog.close()
        dialog.deleteLater()


def open_plot(
    repository: PlotRepository,
    language: Language,
    system: MeasurementSystem,
    load_assessment: Callable[[SummaryExportRow], bool],
    parent: QWidget,
    *,
    settings_store: SettingsStore | None = None,
    editing_provider: Callable[[], ProjectEditingSession | None] | None = None,
) -> None:
    """Compose the original modal PLOT host over a borrowed workspace connection.

    Args:
        repository: Borrowed workspace PLOT handle injected for data, image and geometry
            capabilities.
        language: Explicit UI translation language.
        system: Display units; saved body/assessment source units retain their existing
            provenance.
        load_assessment: Callback selecting the exact exported owner/version; its
            boolean result reports whether selection succeeded.
        editing_provider: Optional shared private editing owner for the open project.
        settings_store: Optional shared personal settings port; never project storage.
        parent: Owning desktop widget for this original modal PLOT workflow.

    Returns:
        None after the modal closes and dialog cleanup is requested; the borrowed
        project remains open.

    Raises:
        OSError: Packaged assets or selected plant images cannot be read.
        ValueError: A required icon or image is invalid.
    """

    def save_gauge_markers(settings: GaugeMarkerSettings) -> None:
        """Save shared gauge appearance through the injected personal preference port.

        Args:
            settings: Validated options requested by a PLOT gauge menu.

        Returns:
            None; persist only personal preferences when a store was supplied.

        Raises:
            OSError: Preference read/write fails; PLOT retains its previous appearance.
            ValueError: Existing personal settings are malformed or unsupported.
        """
        if settings_store is not None:
            settings_store.save(replace(settings_store.load(), gauge_markers=settings))

    dialog = PlotWindow(
        repository,
        repository,
        repository,
        lambda location: import_plant_image(Path(location)),
        load_icons(),
        current_year=date.today().year,
        language=language,
        system=system,
        csv_writer=write_plot_csv,
        load_assessment=load_assessment,
        parent=parent,
        gauge_markers=settings_store.load().gauge_markers if settings_store else None,
        change_gauge_markers=save_gauge_markers,
        editing=editing_provider() if editing_provider else None,
    )
    try:
        dialog.exec()
    finally:
        dialog.close()
        dialog.deleteLater()


def load_icons() -> dict[str, QIcon]:
    """Load only the packaged processed icons used by migrated desktop controls.

    Args:
        None.

    Returns:
        Fresh mapping of stable snake_case icon identities to decoded packaged QIcons;
        no system-default icon substitution.

    Raises:
        ValueError: A packaged processed icon cannot be decoded.
        OSError: A required packaged asset cannot be read.
    """
    icons: dict[str, QIcon] = {}
    for name in (
        "ergotools_logo",
        "new",
        "open",
        "save",
        "undo",
        "redo",
        "cancel",
        "delete",
        "calculate_light",
        "job_management",
        "worker_management",
        "plant",
        "body_view",
        "view_3d_rotate_light",
        "view_3d_zoom_light",
        "view_3d_reset_light",
        "worker",
        "alphabet_order",
        "number_order",
        "transfer_worker_data",
        "transfer_worker_data_light",
        "refresh",
        "plot",
        "jrot",
        "export",
        "settings",
        "help",
        "lifft",
        "duet",
        "shoulder",
        "shift",
        "add_child",
        "section",
        "line",
        "station",
        "first",
        "previous",
        "next",
        "last",
        "search",
        "locate",
        "view",
        "close",
        "filter_reset",
        "filter_apply_light",
        "filter_apply",
        "zoom_in",
        "zoom_out",
        "actual_size",
        "opacity_transparency",
        "capture_image",
        "apply_rotation",
        "compare_rotation",
        "optimize_selected_tool",
        "optimize_all_tools",
    ):
        pixmap = QPixmap()
        if not pixmap.loadFromData(read_asset("icons/" + name + ".png")):
            raise ValueError("Packaged icon could not be decoded.")
        icons[name] = QIcon(pixmap)
    return icons


def create_job_management_demo(path: Path) -> None:
    """Create an empty synthetic management project exclusively, never overwrite.

    Args:
        path: Nonexistent separate synthetic project path; never an operational/original
            project.

    Returns:
        None after creating an empty risk-capable project plus one blank imperial LiFFT
        assessment and closing its handle.

    Raises:
        FileExistsError: The separate output path already exists.
        OSError: The synthetic destination cannot be created.
    """
    metadata = ProjectMetadata(
        "job-management-demo", "Job Management demo", MeasurementSystem.IMPERIAL
    )
    with AssessmentProjectFile.create_with_job_risks(path, metadata) as project:
        project.insert_assessment(
            DocumentKey(metadata.project_id, "assessment"),
            LifftDraft(MeasurementSystem.IMPERIAL),
        )


def run_job_management(
    path: Path,
    settings_path: Path,
    *,
    language: Language | None = None,
) -> int:
    """Own a modal management preview for an existing risk-capable new project.

    Args:
        path: Existing native project with job-risk capability and at least one
            assessment.
        settings_path: Explicit preferences path used by the diagnostic workspace.
        language: Optional language override; None uses saved per-user preferences.

    Returns:
        Zero after the modal diagnostic exits; close dialogs and discard the workspace
        reference in finally blocks.

    Raises:
        ValueError: The project lacks risk capability or any selectable assessment.
        OSError: The project, preferences or packaged assets cannot be read.
    """
    with AssessmentProjectFile.open(path) as project:
        if not project.supports_job_risk:
            raise ValueError("Job Management requires a new format-seven project.")
        entries = project.list_assessments()
        if not entries:
            raise ValueError("This preview requires a project with an assessment.")
        document_id = entries[0].document.document_id
        system = project.metadata.default_units
    workspace: ProjectWorkspace[AssessmentDraft] = ProjectWorkspace(
        lambda location: AssessmentProjectFile.open(Path(location)),
        JsonSettingsStore(settings_path),
    )
    try:
        workspace.switch(str(path), document_id)
        selected_language = (
            language
            if language is not None
            else JsonSettingsStore(settings_path).load().language
        )
        dialog = JobManagementDialog(
            workspace, load_icons(), system, language=selected_language
        )
        try:
            dialog.exec()
        finally:
            dialog.close()
            dialog.deleteLater()
    finally:
        workspace.close(choice=CloseChoice.DISCARD)
    return 0


def main(argv: list[str] | None = None) -> int:
    """Launch the desktop and optionally open a project through its normal policy.

    A positional project path follows the original command-line convention. Opening
    occurs after show, through the same conversion, selection, failure reporting and
    recent-history workflow as the Project menu. No startup Save is performed.
    Diagnostic bootstrap settings remain project-local by default.

    Args:
        argv: Arguments without program name; None reads the current process command
            line.

    Returns:
        Qt application exit status, or zero after a management diagnostic. Positional
        project opening is deferred until the window is shown.

    Raises:
        SystemExit: Help or invalid command-line combinations trigger argparse's
            standard exit.
        OSError: Settings-directory creation, native project creation or packaged asset
            access fails.
        ValueError: Explicit diagnostic/project settings or required resources are
            invalid.
    """
    parser = argparse.ArgumentParser(description="ErgoTools ergonomic assessment tools")
    parser.add_argument(
        "project_file", nargs="?", type=Path, help="Open this .ergprj project"
    )
    parser.add_argument(
        "--settings", type=Path, default=Path.cwd() / ".cache/desktop_settings.json"
    )
    parser.add_argument(
        "--original-lifft-controls",
        action="store_true",
        help="Use migrated original LiFFT task controls inside the temporary preview",
    )
    parser.add_argument(
        "--integrated-preview",
        action="store_true",
        help="Use migrated original shared navigation and LiFFT controls",
    )
    management = parser.add_mutually_exclusive_group()
    management.add_argument(
        "--job-management", type=Path, help="Open a new-format Job Management project"
    )
    management.add_argument(
        "--job-management-demo",
        action="store_true",
        help="Open or create a separate synthetic Job Management demo",
    )
    parser.add_argument(
        "--job-language",
        choices=[item.value for item in Language],
        help="Job Management preview language (defaults to saved preferences)",
    )
    parser.add_argument(
        "--disable-vtk",
        action="store_true",
        help="Disable native 3D rendering for isolated UI review",
    )
    args = parser.parse_args(argv)
    if args.job_language and not (args.job_management_demo or args.job_management):
        parser.error("--job-language requires a Job Management preview option")
    if args.project_file is not None and (
        args.job_management_demo or args.job_management is not None
    ):
        parser.error("project_file cannot be combined with Job Management diagnostics")
    job_language = Language(args.job_language) if args.job_language else None
    app = QApplication(sys.argv[:1])
    install_menu_icon_style(app)
    install_dialog_theme(app)
    app.setApplicationName("ErgoTools")
    args.settings.parent.mkdir(parents=True, exist_ok=True)
    if args.job_management_demo:
        demo_path = args.settings.parent / "job-management-demo.ergprj"
        if not demo_path.exists():
            create_job_management_demo(demo_path)
        return run_job_management(demo_path, args.settings, language=job_language)
    if args.job_management is not None:
        return run_job_management(
            args.job_management, args.settings, language=job_language
        )
    window = create_window(
        args.settings,
        original_controls=args.original_lifft_controls,
        original_navigation=args.integrated_preview,
        enable_vtk=args.integrated_preview and not args.disable_vtk,
    )
    window.show()
    if args.project_file is not None:
        location = str(args.project_file.absolute())
        QTimer.singleShot(
            0, lambda: window.run(lambda: window.open_project_location(location))
        )
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
