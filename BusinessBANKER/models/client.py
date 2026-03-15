"""
Client Base File model for BusinessBANKER.
Every client is anchored by a base file; loan requests attach to it.
"""
from datetime import date
from typing import Any, Optional
from pydantic import BaseModel, Field


class ClientField(BaseModel):
    """A configurable field definition on the client profile."""
    key: str
    label: str
    field_type: str  # "text", "number", "date", "dropdown"
    required: bool = False
    options: list[str] = Field(default_factory=list)  # for dropdowns


class ClientProfile(BaseModel):
    """
    The base file for a client.
    client_number and client_name are always mandatory (spec §2.2).
    All other fields come from the configuration.
    """
    client_number: str = Field(..., description="Unique client identifier")
    client_name: str = Field(..., description="Full legal name")
    branch_id: str = Field(..., description="Originating branch / org unit")

    # Dynamic fields defined by the bank's configuration
    extra_fields: dict[str, Any] = Field(
        default_factory=dict,
        description="Bank-configured additional fields (address, DOB, sector, etc.)",
    )

    created_by: str  # user id
    created_at: date = Field(default_factory=date.today)
    is_active: bool = True


class ClientCreate(BaseModel):
    client_number: str
    client_name: str
    branch_id: str
    extra_fields: dict[str, Any] = Field(default_factory=dict)
