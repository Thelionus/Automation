"""
Loan Request model for BusinessBANKER.
A structured document attached to a Client Base File.
Sections are fully configurable (spec §2.3, §4.5).
"""
from datetime import date, datetime
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


class SectionType(str, Enum):
    STANDARD = "standard"          # structured field data
    TEXT = "text"                  # free-text / list narrative
    HTML = "html"                  # rich content / widgets
    DECISION = "decision"          # committee decision area


class RequestSection(BaseModel):
    """One configurable section within a loan request."""
    id: str
    title: str
    section_type: SectionType
    order: int
    data: dict[str, Any] = Field(default_factory=dict)


class DecisionEntry(BaseModel):
    """A single committee member's recorded view and determination."""
    role_id: str
    user_id: str
    decision: str          # "approve" | "decline" | "escalate" | "pending"
    comments: str = ""
    recorded_at: datetime = Field(default_factory=datetime.utcnow)


class WorkflowHistoryEntry(BaseModel):
    """Immutable audit record of each step transition."""
    from_step_id: str
    to_step_id: str
    performed_by: str       # user id
    transition_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    notes: str = ""


class RequestStatus(str, Enum):
    IN_PREPARATION = "in_preparation"
    UNDER_REVIEW = "under_review"
    PENDING_DECISION = "pending_decision"
    APPROVED = "approved"
    LEGAL_PROCESSING = "legal_processing"
    PENDING_DISBURSEMENT = "pending_disbursement"
    DISBURSED = "disbursed"
    DECLINED = "declined"


class LoanRequest(BaseModel):
    """
    The core transactional document in BusinessBANKER.
    Multiple requests can exist under a single client base file.
    """
    id: str
    client_number: str
    branch_id: str

    # Core financials
    amount: float = Field(..., description="Requested credit facility amount")
    currency: str = "USD"
    product_type: str = ""          # e.g. "term_loan", "overdraft", "mortgage"

    # Workflow state
    current_step_id: str
    current_status: RequestStatus = RequestStatus.IN_PREPARATION
    assigned_to_user_id: Optional[str] = None

    # Configurable sections (Client Info, Facilities, Collateral, etc.)
    sections: list[RequestSection] = Field(default_factory=list)

    # Decision committee entries
    decisions: list[DecisionEntry] = Field(default_factory=list)

    # Full audit trail
    history: list[WorkflowHistoryEntry] = Field(default_factory=list)

    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def get_context(self) -> dict[str, Any]:
        """
        Flatten key fields into a context dict for workflow condition evaluation.
        """
        ctx: dict[str, Any] = {
            "amount": self.amount,
            "currency": self.currency,
            "product_type": self.product_type,
            "current_step_id": self.current_step_id,
        }
        # Merge in section data so any configured field can be referenced
        for section in self.sections:
            ctx.update(section.data)
        return ctx


class LoanRequestCreate(BaseModel):
    client_number: str
    branch_id: str
    amount: float
    currency: str = "USD"
    product_type: str = ""


def build_default_sections() -> list[RequestSection]:
    """
    Returns the standard section scaffold for a new loan request (spec §2.3).
    Each bank may add or remove sections through configuration.
    """
    return [
        RequestSection(id="client_recap", title="Client Information Recap", section_type=SectionType.STANDARD, order=1),
        RequestSection(id="credit_facilities", title="Credit Facilities", section_type=SectionType.HTML, order=2),
        RequestSection(id="collateral", title="Collateral & Securities", section_type=SectionType.HTML, order=3),
        RequestSection(id="disbursement_conditions", title="Disbursement Conditions", section_type=SectionType.TEXT, order=4),
        RequestSection(id="followup_conditions", title="Follow-Up Conditions", section_type=SectionType.TEXT, order=5),
        RequestSection(id="exceptions", title="Exceptions", section_type=SectionType.TEXT, order=6),
        RequestSection(id="risk_assessment", title="Risk Assessment", section_type=SectionType.STANDARD, order=7),
        RequestSection(id="project_description", title="Project Description", section_type=SectionType.TEXT, order=8),
        RequestSection(id="decision", title="Decision", section_type=SectionType.DECISION, order=9),
    ]
