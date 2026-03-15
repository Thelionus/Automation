"""
BusinessBANKER — Decision & Workflow Management Platform
FastAPI application entry point.

Run with:
    uvicorn main:app --reload

Interactive docs:
    http://localhost:8000/docs
"""
from fastapi import FastAPI
from api import api_router
from config.configuration import build_sample_configuration

app = FastAPI(
    title="BusinessBANKER",
    description=(
        "Decision and Workflow Management Platform for banking institutions. "
        "Manages the full credit lifecycle from client initiation through disbursement."
    ),
    version="1.0.0",
)

# Load sample configuration at startup
config = build_sample_configuration()

app.include_router(api_router, prefix="/api/v1")


@app.get("/", tags=["Health"])
def root():
    return {
        "system": "BusinessBANKER",
        "version": "1.0.0",
        "bank": config.bank_name,
        "workflow": config.workflow.name,
        "status": "operational",
    }


@app.get("/api/v1/config", tags=["Configuration"])
def get_config():
    """Return the active bank configuration (org units, roles, workflow)."""
    return {
        "bank_name": config.bank_name,
        "org_units": [u.model_dump() for u in config.org_units],
        "roles": [r.model_dump() for r in config.roles],
        "workflow_steps": [
            {
                "id": s.id,
                "name": s.name,
                "assigned_role": s.assigned_role_id,
                "status_label": s.status_label,
                "is_terminal": s.is_terminal,
                "transitions": [
                    {"id": t.id, "label": t.label, "target": t.target_step_id}
                    for t in s.transitions
                ],
            }
            for s in config.workflow.steps
        ],
    }
