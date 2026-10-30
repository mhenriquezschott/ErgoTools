"""Integrated menu access to existing project and assessment operations.

Presentation layer. The contracts below define owned controls/view values and injected
operations. Qt components run on the GUI thread; scientific calculations, canonical
source state and repository lifetime remain with the named application/domain ports and
host owners.
"""

from collections.abc import Callable, Mapping
from html import escape

from PyQt5.QtWidgets import QAction, QMenu, QMenuBar, QPushButton, QWidget

from ergotools.application.settings import Language


class AssessmentMenu(QMenuBar):
    """Expose existing owned actions without duplicating their input/dirty policy."""

    def __init__(
        self,
        buttons: Mapping[str, QPushButton],
        refresh_controls: Callable[[], None],
        *,
        language: Language,
        open_preferences: Callable[[], None],
        open_recent: Callable[[str], None],
        refresh_recent: Callable[[], None],
        clear_recent: Callable[[], None],
        close_project: Callable[[], None],
        save_as: Callable[[], None],
        backup: Callable[[], None],
        export_csv: Callable[[], None],
        open_guide: Callable[[], None],
        open_authors: Callable[[], None],
        camera_animation: Callable[[bool], None],
        open_properties: Callable[[], None],
        open_project_folder: Callable[[], None],
        parent: QWidget | None = None,
    ) -> None:
        """Reuse button callbacks, processed icons and shared localized captions.

        Args:
            buttons: Existing command buttons whose icon, caption and enablement the
                menu mirrors.
            refresh_controls: Callback refreshing command availability when a menu
                opens.
            language: UI language only; does not reinterpret saved names, numeric inputs
                or units.
            open_preferences: Host callback for owned application preferences.
            open_recent: Host callback receiving an explicitly selected saved project
                location.
            refresh_recent: Callback reloading recent locations when the submenu opens.
            clear_recent: Callback clearing saved recent locations without closing the
                current project.
            close_project: Callback resolving dirty intent and releasing the active
                project.
            save_as: Callback publishing a separate native project copy after explicit
                selection.
            backup: Callback copying saved project state without accepting pending
                edits.
            export_csv: Callback exporting saved assessment summaries through the host.
            open_guide: Callback opening the packaged localized user guide.
            open_authors: Callback opening the original Authors modal.
            camera_animation: Callback receiving the checked active-region camera
                preference.
            open_properties: Callback presenting saved read-only project metadata.
            open_project_folder: Callback opening the saved project's directory in
                the operating system file manager, without accepting editor drafts.
            parent: Qt owner of the new control; None leaves top-level ownership to the
                caller.

        Returns:
            None.
        """
        super().__init__(parent)
        self._buttons = buttons
        project = self.addMenu("")
        edit = self.addMenu("")
        assert project is not None and edit is not None
        self.project = project
        self.edit = edit
        self.actions_by_key: dict[str, QAction] = {}
        for menu, keys in (
            (
                self.project,
                (
                    "new",
                    "open",
                    "save",
                    "",
                    "new_assessment",
                    "assessment_context",
                ),
            ),
            (self.edit, ("undo", "redo")),
        ):
            menu.aboutToShow.connect(refresh_controls)
            for key in keys:
                if not key:
                    menu.addSeparator()
                    continue
                button = buttons[key]
                action = menu.addAction(button.icon(), button.text())
                assert action is not None
                if key not in ("undo", "redo"):
                    action.triggered.connect(button.click)
                self.actions_by_key[key] = action
        self.save_as = QAction(buttons["save"].icon(), "", self)
        self.backup = QAction(buttons["save"].icon(), "", self)
        self.save_as.triggered.connect(save_as)
        self.backup.triggered.connect(backup)
        after_save = self.project.actions()[
            self.project.actions().index(self.actions_by_key["save"]) + 1
        ]
        self.project.insertAction(after_save, self.save_as)
        self.project.insertAction(after_save, self.backup)
        self.export_csv = QAction(parent=self)
        self.export_csv.triggered.connect(export_csv)
        self.project.insertAction(after_save, self.export_csv)
        self._open_recent = open_recent
        self._clear_recent = clear_recent
        self._recent_locations: tuple[str, ...] = ()
        self._language = language
        self.recent = QMenu(self.project)
        self.recent.setToolTipsVisible(True)
        self.recent.setIcon(buttons["open"].icon())
        self.project.insertMenu(self.actions_by_key["save"], self.recent)
        self.recent.aboutToShow.connect(refresh_recent)
        self.project.addSeparator()
        self.open_project_folder = QAction(buttons["open"].icon(), "", self)
        self.open_project_folder.triggered.connect(open_project_folder)
        self.project.addAction(self.open_project_folder)
        self.properties = QAction(parent=self)
        self.properties.triggered.connect(open_properties)
        self.project.addAction(self.properties)
        close_action = self.project.addAction("")
        assert close_action is not None
        self.close_project_action = close_action
        close_action.triggered.connect(close_project)
        view = self.addMenu("")
        assert view is not None
        self.view = view
        self.camera_animation = QAction(parent=self)
        self.camera_animation.setCheckable(True)
        self.camera_animation.toggled.connect(camera_animation)
        view.addAction(self.camera_animation)
        setup = self.addMenu("")
        assert setup is not None
        self.work_setup = setup
        self.organization = QAction(buttons["organization_management"].icon(), "", self)
        self.organization.triggered.connect(buttons["organization_management"].click)
        self.jobs = QAction(buttons["job_form_title"].icon(), "", self)
        self.jobs.triggered.connect(buttons["job_form_title"].click)
        setup.addAction(self.organization)
        setup.addAction(self.jobs)
        setup.aboutToShow.connect(refresh_controls)
        tools = self.addMenu("")
        assert tools is not None
        self.tools = tools
        preferences = tools.addAction("")
        assert preferences is not None
        self.preferences = preferences
        preferences.triggered.connect(open_preferences)
        help_menu = self.addMenu("")
        assert help_menu is not None
        self.help_menu = help_menu
        guide = help_menu.addAction("")
        authors = help_menu.addAction("")
        assert guide is not None and authors is not None
        self.user_guide = guide
        self.about = authors
        guide.triggered.connect(open_guide)
        authors.triggered.connect(open_authors)
        self.translate(language)

    def translate(self, language: Language) -> None:
        """Update menu captions and action metadata from their existing owners.

        Args:
            language: UI language only; does not reinterpret saved names, numeric inputs
                or units.

        Returns:
            None.
        """
        self._language = language
        spanish = language is Language.SPANISH
        self.project.setTitle("Proyecto" if spanish else "Project")
        self.open_project_folder.setText(
            "Abrir carpeta del proyecto" if spanish else "Open project folder"
        )
        self.open_project_folder.setToolTip(
            "Abrir la carpeta del proyecto guardado en el explorador del sistema."
            if spanish
            else "Open the saved project's folder in the system file manager."
        )
        self.properties.setText("Propiedades" if spanish else "Properties")
        self.properties.setToolTip(
            "Ver los detalles del proyecto abierto."
            if spanish
            else "View the open project's details."
        )
        self.edit.setTitle("Editar" if spanish else "Edit")
        self.view.setTitle("Ver" if spanish else "View")
        self.camera_animation.setText(
            "Enfoque animado de región corporal"
            if spanish
            else "Animated body-region focus"
        )
        self.camera_animation.setStatusTip(
            "Animar la cámara hacia la región evaluada."
            if spanish
            else "Animate the 3D camera toward the body region evaluated by each tool."
        )
        self.camera_animation.setToolTip(
            "Desactive para mantener la vista de cuerpo completo."
            if spanish
            else "Disable this option to keep the original full-body "
            "camera view for every tool."
        )
        self.help_menu.setTitle("Ayuda" if spanish else "Help")
        self.user_guide.setText("Guía de usuario" if spanish else "User Guide")
        self.about.setText("Acerca de" if spanish else "About")
        self.user_guide.setToolTip(
            "Abrir el manual de Ergo Tools."
            if spanish
            else "Open the Ergo Tools user manual."
        )
        self.about.setToolTip(
            "Mostrar autores y créditos." if spanish else "Show authors and credits."
        )
        self.work_setup.setTitle("Lugar de trabajo" if spanish else "Workplace")
        self.organization.setText("Organización..." if spanish else "Organization...")
        self.organization.setToolTip(
            "Administrar plantas, secciones, líneas, estaciones y turnos."
            if spanish
            else "Manage plants, sections, lines, stations, and shifts."
        )
        self.jobs.setText("Trabajos..." if spanish else "Jobs...")
        self.jobs.setToolTip(
            "Administrar trabajos, riesgos, calculadoras y disponibilidad de puestos."
            if spanish
            else "Manage Jobs, risk values, calculators, and workplace availability."
        )
        self.tools.setTitle("Herramientas" if spanish else "Tools")
        self.preferences.setText("Configuración" if spanish else "Settings")
        self.export_csv.setText(
            "Exportar herramienta seleccionada a CSV"
            if spanish
            else "Export selected tool to CSV"
        )
        self.export_csv.setToolTip(
            "Exportar versiones actuales guardadas para todos los trabajadores."
            if spanish
            else "Export saved current versions for all workers."
        )
        self.save_as.setText("Guardar como…" if spanish else "Save As…")
        self.backup.setText(
            "Copia del proyecto guardado…" if spanish else "Backup saved project…"
        )
        self.save_as.setToolTip(
            "Copiar con las ediciones actuales sin guardar el original."
            if spanish
            else "Copy with current edits without saving the original."
        )
        self.backup.setToolTip(
            "Copiar solo los datos guardados, sin cambiar el proyecto abierto."
            if spanish
            else "Copy only saved data without changing the open project."
        )
        self.recent.setTitle("Proyectos recientes" if spanish else "Recent projects")
        self.close_project_action.setText(
            "Cerrar proyecto" if spanish else "Close project"
        )
        self.set_recent(self._recent_locations)
        self.sync()

    def set_recent(self, locations: tuple[str, ...]) -> None:
        """Render saved locations without opening, resolving or inspecting projects.

        Args:
            locations: Saved recent project paths in their settings order; not inspected
                or opened here.

        Returns:
            None; full saved paths distinguish duplicate filenames. Tooltips retain
            literal paths when a screen bounds an unusually wide native menu.
        """
        self._recent_locations = locations
        self.recent.clear()
        for number, location in enumerate(locations, 1):
            # QAction treats ampersands as mnemonics; paths remain literal display data.
            caption = location.replace("&", "&&")
            action = self.recent.addAction(f"{number}. {caption}")
            assert action is not None
            action.setData(location)
            action.setToolTip("<qt>" + escape(location) + "</qt>")
            action.triggered.connect(
                lambda checked=False, location=location: self._open_recent(location)
            )
        if not locations:
            empty = self.recent.addAction(
                "Sin proyectos recientes"
                if self._language is Language.SPANISH
                else "No recent projects"
            )
            assert empty is not None
            empty.setEnabled(False)
        self.recent.addSeparator()
        clear = self.recent.addAction(
            "Borrar historial"
            if self._language is Language.SPANISH
            else "Clear history"
        )
        assert clear is not None
        clear.setIcon(self._buttons["remove"].icon())
        clear.setEnabled(bool(locations))
        clear.triggered.connect(self._clear_recent)
        self.clear_recent_action = clear

    def sync(self) -> None:
        """Reflect command availability and captions without triggering edits.

        Args:
            None.

        Returns:
            None.
        """
        self.organization.setEnabled(
            self._buttons["organization_management"].isEnabled()
        )
        self.jobs.setEnabled(self._buttons["job_form_title"].isEnabled())
        for key, action in self.actions_by_key.items():
            button = self._buttons[key]
            action.setText(button.text())
            action.setToolTip(button.toolTip())
            action.setEnabled(button.isEnabled())
