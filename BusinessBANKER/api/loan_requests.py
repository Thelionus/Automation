"""
Loan Request endpoints — creation, retrieval, section updates, and decisions.
"""
import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel

from models.loan_request import (
    LoanRequest, LoanRequestCreate, DecisionEntry,
    RequestStatus, build_default_sections,
)
from models.workflow import build_standard_workflow
from engine.workflow_engine import WorkflowEngine, WorkflowError
from api.dependencies import get_store, get_engine

router = APIRouter(prefix="/requests", tags=["Loan Requests"])


class AdvanceRequest(BaseModel):
    transition_id: str
    performed_by: str
    notes: str = ""


class SectionUpdateRequest(BaseModel):
    data: dict


@router.post("/", response_model=LoanRequest, status_code=201)
def create_loan_request(payload: LoanRequestCreate, store=Depends(get_store)):
    if payload.client_number not in store["clients"]:
        raise HTTPException(status_code=404, detail="Client not found.")

    workflow = build_standard_workflow()
    request = LoanRequest(
        id=str(uuid.uuid4()),
        **payload.model_dump(),
        current_step_id=workflow.initial_step_id,
        sections=build_default_sections(),
        created_by="system",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    store["requests"][request.id] = request
    return request


@router.get("/", response_model=list[LoanRequest])
def list_requests(
    client_number: str | None = Query(None),
    store=Depends(get_store),
):
    requests = list(store["requests"].values())
    if client_number:
        requests = [r for r in requests if r.client_number == client_number]
    return requests


@router.get("/portfolio", response_model=list[LoanRequest])
def portfolio_view(
    role_id: str = Query(..., description="Role of the requesting user"),
    org_unit_id: str = Query(..., description="Branch / org unit of the requesting user"),
    store=Depends(get_store),
    engine: WorkflowEngine = Depends(get_engine),
):
    """
    Returns the filtered portfolio for a given role and branch (spec §5).
    """
    all_requests = list(store["requests"].values())
    return engine.get_portfolio(all_requests, role_id, org_unit_id)


@router.get("/{request_id}", response_model=LoanRequest)
def get_request(request_id: str, store=Depends(get_store)):
    req = store["requests"].get(request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found.")
    return req


@router.get("/{request_id}/transitions")
def get_transitions(
    request_id: str,
    store=Depends(get_store),
    engine: WorkflowEngine = Depends(get_engine),
):
    req = store["requests"].get(request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found.")
    return engine.available_transitions(req)


@router.post("/{request_id}/advance", response_model=LoanRequest)
def advance_request(
    request_id: str,
    payload: AdvanceRequest,
    store=Depends(get_store),
    engine: WorkflowEngine = Depends(get_engine),
):
    req = store["requests"].get(request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found.")
    try:
        updated = engine.advance(req, payload.transition_id, payload.performed_by, payload.notes)
    except WorkflowError as e:
        raise HTTPException(status_code=400, detail=str(e))
    store["requests"][request_id] = updated
    return updated


@router.patch("/{request_id}/sections/{section_id}", response_model=LoanRequest)
def update_section(
    request_id: str,
    section_id: str,
    payload: SectionUpdateRequest,
    store=Depends(get_store),
):
    req = store["requests"].get(request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found.")
    section = next((s for s in req.sections if s.id == section_id), None)
    if not section:
        raise HTTPException(status_code=404, detail="Section not found.")
    section.data.update(payload.data)
    req.updated_at = datetime.utcnow()
    return req


@router.post("/{request_id}/decisions", response_model=LoanRequest)
def record_decision(
    request_id: str,
    decision: DecisionEntry,
    store=Depends(get_store),
):
    req = store["requests"].get(request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found.")
    req.decisions.append(decision)
    req.updated_at = datetime.utcnow()
    return req
