"""
FastAPI dependency injection: in-memory store and shared engine instance.
Replace with database-backed implementations for production.
"""
from functools import lru_cache

from models.workflow import build_standard_workflow
from engine.workflow_engine import WorkflowEngine

# ---------------------------------------------------------------------------
# In-memory store (swap for a real database in production)
# ---------------------------------------------------------------------------
_store: dict = {
    "clients": {},    # client_number → ClientProfile
    "requests": {},   # request_id   → LoanRequest
    "users": {},      # user_id      → User
}


def get_store() -> dict:
    return _store


@lru_cache(maxsize=1)
def get_engine() -> WorkflowEngine:
    return WorkflowEngine(build_standard_workflow())
