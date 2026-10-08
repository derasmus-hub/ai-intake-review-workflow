from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class WorkflowStatus(str, Enum):
    SUBMITTED = "submitted"
    AWAITING_REVIEW = "awaiting_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Category(str, Enum):
    FINANCE = "finance"
    IT = "it"
    HR = "hr"
    SALES = "sales"
    OPERATIONS = "operations"
    OTHER = "other"


class IntakeCreate(BaseModel):
    requester: str = Field(min_length=1, max_length=100)
    subject: str = Field(min_length=1, max_length=200)
    details: str = Field(min_length=1, max_length=5000)


class AIClassification(BaseModel):
    category: Category
    priority: Priority
    summary: str
    recommended_action: str


class ReviewDecision(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"


class ReviewInput(BaseModel):
    decision: ReviewDecision
    reviewer: str = Field(min_length=1, max_length=100)
    note: Optional[str] = Field(default=None, max_length=2000)


class IntakeRecord(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    requester: str
    subject: str
    details: str
    status: WorkflowStatus = WorkflowStatus.SUBMITTED
    classification: Optional[AIClassification] = None
    reviewer: Optional[str] = None
    review_note: Optional[str] = None
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    reviewed_at: Optional[datetime] = None
