from datetime import datetime, timezone
from uuid import UUID

from fastapi import FastAPI, HTTPException, status

from app.classifier import ClassificationError, get_classifier
from app.models import (
    IntakeCreate,
    IntakeRecord,
    ReviewDecision,
    ReviewInput,
    WorkflowStatus,
)
from app.store import store


app = FastAPI(
    title="AI Intake Review Workflow",
    description="Structured request classification with human-controlled decisions.",
    version="0.3.0",
)

classifier = get_classifier()


@app.post("/intakes", response_model=IntakeRecord, status_code=status.HTTP_201_CREATED)
def create_intake(payload: IntakeCreate) -> IntakeRecord:
    record = IntakeRecord(**payload.model_dump())

    # Classification provides advice only; application code owns this transition.
    try:
        classification = classifier(record.subject, record.details)
    except ClassificationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Classification service unavailable",
        ) from exc

    record.classification = classification
    record.status = WorkflowStatus.AWAITING_REVIEW
    return store.save(record)


@app.get("/intakes/{intake_id}", response_model=IntakeRecord)
def get_intake(intake_id: UUID) -> IntakeRecord:
    record = store.get(intake_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Intake not found")
    return record


@app.post("/intakes/{intake_id}/review", response_model=IntakeRecord)
def review_intake(intake_id: UUID, payload: ReviewInput) -> IntakeRecord:
    record = store.get(intake_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Intake not found")
    if record.status != WorkflowStatus.AWAITING_REVIEW:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only intakes awaiting review can be reviewed",
        )

    record.status = (
        WorkflowStatus.APPROVED
        if payload.decision == ReviewDecision.APPROVE
        else WorkflowStatus.REJECTED
    )
    record.reviewer = payload.reviewer
    record.review_note = payload.note
    record.reviewed_at = datetime.now(timezone.utc)
    return store.save(record)
