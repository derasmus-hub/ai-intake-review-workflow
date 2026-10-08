from uuid import UUID

from app.models import IntakeRecord


class InMemoryIntakeStore:
    """Small process-local persistence layer for the demonstration application."""

    def __init__(self) -> None:
        self._records: dict[UUID, IntakeRecord] = {}

    def save(self, record: IntakeRecord) -> IntakeRecord:
        self._records[record.id] = record
        return record

    def get(self, intake_id: UUID) -> IntakeRecord | None:
        return self._records.get(intake_id)

    def clear(self) -> None:
        self._records.clear()


store = InMemoryIntakeStore()
