"""Task-name catalog capability and pure metadata edits for assessment hosts.

Application layer. Sources retain independent measurements and stable row identity.
Ports borrow project lifetime and storage owns transactions. No Qt, SQL, clipboard,
calculator or separate history stack is introduced.
"""

from collections.abc import Callable
from dataclasses import dataclass, replace
from typing import ClassVar, Protocol, runtime_checkable
from unicodedata import normalize

from ergotools.application.session import DocumentKey
from ergotools.domain.assessments.document import AssessmentDraft
from ergotools.domain.assessments.duet_draft import DuetDraft
from ergotools.domain.assessments.lifft_draft import LifftDraft
from ergotools.domain.task_catalog import TaskDefinition, validate_task_label


@runtime_checkable
class TaskCatalogRepository(Protocol):
    """Project-scoped reusable labels with expected-state transactional replacement."""

    def load_task_definitions(self) -> tuple[TaskDefinition, ...]:
        """Read definitions without creating storage or changing assessment sources.

        Args:
            None.

        Returns:
            Stable ID-ordered definitions; equal labels do not imply equal identity.
        """
        ...

    def replace_task_definitions(
        self,
        expected: tuple[TaskDefinition, ...],
        replacement: tuple[TaskDefinition, ...],
    ) -> None:
        """Replace exactly the expected catalog while protecting referenced identities.

        Args:
            expected: Latest catalog shown by the caller; stale edits are rejected.
            replacement: Complete desired definitions, without changing measurements.

        Returns:
            None after one atomic accepted project edit; Main Save publishes it.
        """
        ...


def label_assessment_task(
    source: AssessmentDraft, task_id: str, name: str | None, definition_id: str | None
) -> AssessmentDraft:
    """Replace one occurrence's descriptive fields while retaining exact inputs.

    Args:
        source: Immutable worker or Job source in its recorded units.
        task_id: Existing source-row identity; a definition ID is not a row ID.
        name: Literal fallback name, or absent for an unnamed row.
        definition_id: Optional explicitly selected reusable definition.

    Returns:
        Same tool/source metadata and numeric fields with only the row label changed.

    Raises:
        ValueError: Label/reference is invalid or the exact row does not exist.
    """
    validate_task_label(name, definition_id)
    if not any(t.task_id == task_id for t in source.tasks):
        raise ValueError("Task row no longer exists.")
    if isinstance(source, LifftDraft):
        return replace(
            source,
            tasks=tuple(
                replace(t, task_name=name, task_definition_id=definition_id)
                if t.task_id == task_id
                else t
                for t in source.tasks
            ),
        )
    if isinstance(source, DuetDraft):
        return replace(
            source,
            tasks=tuple(
                replace(t, task_name=name, task_definition_id=definition_id)
                if t.task_id == task_id
                else t
                for t in source.tasks
            ),
        )
    return replace(
        source,
        tasks=tuple(
            replace(t, task_name=name, task_definition_id=definition_id)
            if t.task_id == task_id
            else t
            for t in source.tasks
        ),
    )


@dataclass(frozen=True, slots=True)
class ReplaceAssessmentSource:
    """Atomic source replacement for name changes and validated clipboard batches.

    Attributes:
        document: Exact project/document session owner.
        expected: Complete source captured when preparing this edit.
        replacement: Complete same-tool source after validation.
        label_key: Localizable operation key carried into existing session history.
    """

    document: DocumentKey
    expected: AssessmentDraft
    replacement: AssessmentDraft
    label_key: str = "assessment.task_name"
    # Maximum worker assessment capacity, matching the existing count command.
    maximum_tasks: ClassVar[int] = 100

    def apply(self, state: AssessmentDraft) -> AssessmentDraft:
        """Reject stale/tool-changing/oversized sources before accepting a batch.

        Args:
            state: Current exact committed immutable session source.

        Returns:
            Validated replacement; equal no-ops remain the session engine's concern.

        Raises:
            ValueError: Expected source is stale, tool changed or capacity is invalid.
        """
        if (
            state != self.expected
            or type(state) is not type(self.replacement)
            or not 1 <= len(self.replacement.tasks) <= self.maximum_tasks
        ):
            raise ValueError("Assessment edit is stale or has invalid tool/capacity.")
        return self.replacement


# Source acceptance stays with the exact worker/Job editor; no GUI objects cross here.
TaskSourceAcceptor = Callable[[AssessmentDraft, AssessmentDraft, str, bool], bool]


def reusable_pasted_names(
    source: AssessmentDraft,
    task_ids: frozenset[str],
    definitions: tuple[TaskDefinition, ...],
    new_identity: Callable[[], str],
) -> tuple[AssessmentDraft, tuple[TaskDefinition, ...]]:
    """Link only pasted name cells to reusable definitions, creating missing names.

    Args:
        source: Validated complete replacement with literal imported task names.
        task_ids: Exact destination rows whose name column was mapped in this paste.
        definitions: Current project catalog; explicit existing references are retained.
        new_identity: Injected stable-ID factory, called once per distinct new name.

    Returns:
        Detached source/catalog plan. Matching ignores surrounding whitespace, case
        and Unicode composition, preserving accents. Existing duplicate labels select
        the first stable ID; explicit linked identities remain distinct. Fallback
        source text and all numeric/task identities remain unchanged.

    Raises:
        ValueError: A pasted row or explicit reference no longer exists, or a new
            definition identity is invalid/duplicates an existing identity.
    """
    if not task_ids <= {task.task_id for task in source.tasks}:
        raise ValueError("Pasted task rows no longer exist.")
    catalog = {definition.definition_id: definition for definition in definitions}
    by_name: dict[str, TaskDefinition] = {}
    for existing in sorted(definitions, key=lambda item: item.definition_id):
        by_name.setdefault(normalize("NFC", existing.name.strip()).casefold(), existing)
    replacement = source
    for task in source.tasks:
        if task.task_id not in task_ids or task.task_name is None:
            continue
        if task.task_definition_id is not None:
            if task.task_definition_id not in catalog:
                raise ValueError("Assessment references an unknown reusable task.")
            continue
        key = normalize("NFC", task.task_name.strip()).casefold()
        definition = by_name.get(key)
        if definition is None:
            definition = TaskDefinition(new_identity(), task.task_name.strip())
            if definition.definition_id in catalog:
                raise ValueError("Reusable task identity already exists.")
            catalog[definition.definition_id] = definition
            by_name[key] = definition
        replacement = label_assessment_task(
            replacement, task.task_id, task.task_name, definition.definition_id
        )
    return replacement, tuple(
        sorted(catalog.values(), key=lambda item: item.definition_id)
    )
