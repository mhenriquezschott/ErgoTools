"""Reference worker labels with explicit IDs, independent of Qt selectors.

Presentation layer. Interpret explicit user selections and project immutable values for
controls or interchange, independently of widget construction. Persistence and source
history use injected application services. Do not infer identity from captions, units
from interface language, or missing scientific quantities from zero. Storage errors
propagate to the host for localized reporting; user data remains literal.
"""

from dataclasses import dataclass
from enum import StrEnum

from ergotools.domain.work_catalog import WorkCatalog


class WorkerOrder(StrEnum):
    """Supported ordering policies, independent of localized selector captions."""

    # Original binary stable worker-ID ordering.
    ID = "id"
    # Original null-first binary last-name ordering; equal names retain source order.
    LAST_NAME = "last_name"


@dataclass(frozen=True, slots=True)
class WorkerOption:
    """Stable worker identity coupled to a literal original-formatted caption.

    Attributes:
        worker_id: Exact worker identity; never recover it by parsing label.
        label: Worker ID alone or ID (last name, first name) when both names exist.
    """

    worker_id: str
    label: str


def worker_options(
    catalog: WorkCatalog, order: WorkerOrder
) -> tuple[WorkerOption, ...]:
    """Preserve reference formatting and binary/null-first worker ordering.

    Include both names only when both are nonempty. Equal last names keep input snapshot
    order: the reference SQL specifies no secondary ordering key.

    Args:
        catalog: Validated saved worker catalog; literal names are never translated.
        order: Explicit original binary ID or null-first last-name ordering.

    Returns:
        Stable-ID/display-label pairs; both names are shown only when both nonempty, and
        equal last names retain input order.

    Raises:
        ValueError: Worker ordering policy is untyped or unsupported.
    """
    if not isinstance(order, WorkerOrder):
        raise ValueError("Unsupported worker ordering policy.")
    if order is WorkerOrder.ID:
        workers = sorted(catalog.workers, key=lambda worker: worker.worker_id)
    else:
        workers = sorted(
            catalog.workers,
            key=lambda worker: (worker.last_name is not None, worker.last_name or ""),
        )
    return tuple(
        WorkerOption(
            worker.worker_id,
            f"{worker.worker_id} ({worker.last_name}, {worker.first_name})"
            if worker.last_name and worker.first_name
            else worker.worker_id,
        )
        for worker in workers
    )
