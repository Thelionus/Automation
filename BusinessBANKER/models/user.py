"""
User and Role models for BusinessBANKER.
Roles can be assigned to humans or AI agents.
"""
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class RoleType(str, Enum):
    RELATIONSHIP_MANAGER = "relationship_manager"
    CREDIT_ANALYST = "credit_analyst"
    CREDIT_ADJUDICATOR = "credit_adjudicator"
    HEAD_OF_CREDIT = "head_of_credit"
    MANAGING_DIRECTOR = "managing_director"
    BOARD = "board"
    LEGAL_OFFICER = "legal_officer"
    OPERATIONS_OFFICER = "operations_officer"
    AI_AGENT = "ai_agent"


class RolePermissions(BaseModel):
    can_create_client: bool = False
    can_create_request: bool = False
    can_read_only: bool = True
    can_approve: bool = False
    can_disburse: bool = False
    can_configure: bool = False


class Role(BaseModel):
    id: str
    name: str
    role_type: RoleType
    permissions: RolePermissions
    is_ai_agent: bool = False
    description: Optional[str] = None


class OrganizationalUnit(BaseModel):
    id: str
    name: str
    code: str
    parent_id: Optional[str] = None  # None = Head Office


class User(BaseModel):
    id: str
    name: str
    email: str
    role_id: str
    org_unit_id: str
    is_active: bool = True
    is_ai_agent: bool = False


# --- Default role definitions ---

DEFAULT_ROLES: list[Role] = [
    Role(
        id="rm",
        name="Relationship Manager",
        role_type=RoleType.RELATIONSHIP_MANAGER,
        permissions=RolePermissions(
            can_create_client=True,
            can_create_request=True,
            can_read_only=False,
        ),
    ),
    Role(
        id="analyst",
        name="Credit Analyst",
        role_type=RoleType.CREDIT_ANALYST,
        permissions=RolePermissions(can_read_only=False),
    ),
    Role(
        id="adjudicator",
        name="Credit Adjudicator",
        role_type=RoleType.CREDIT_ADJUDICATOR,
        permissions=RolePermissions(can_read_only=False, can_approve=True),
    ),
    Role(
        id="head_credit",
        name="Head of Credit",
        role_type=RoleType.HEAD_OF_CREDIT,
        permissions=RolePermissions(can_read_only=False, can_approve=True),
    ),
    Role(
        id="md",
        name="Managing Director",
        role_type=RoleType.MANAGING_DIRECTOR,
        permissions=RolePermissions(can_read_only=False, can_approve=True),
    ),
    Role(
        id="board",
        name="Board of Directors",
        role_type=RoleType.BOARD,
        permissions=RolePermissions(can_read_only=False, can_approve=True),
    ),
    Role(
        id="legal",
        name="Legal / Documentation Officer",
        role_type=RoleType.LEGAL_OFFICER,
        permissions=RolePermissions(can_read_only=False),
    ),
    Role(
        id="ops",
        name="Operations / Disbursement Officer",
        role_type=RoleType.OPERATIONS_OFFICER,
        permissions=RolePermissions(can_read_only=False, can_disburse=True),
    ),
    Role(
        id="ai_workbench",
        name="AI Agent",
        role_type=RoleType.AI_AGENT,
        permissions=RolePermissions(can_read_only=False),
        is_ai_agent=True,
        description="AI-powered workflow participant for document generation and risk assessment",
    ),
]
