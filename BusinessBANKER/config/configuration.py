"""
System configuration for BusinessBANKER.
Manages org structure, roles, workflow definition, and request section layout.
(spec §4)
"""
from typing import Optional
from pydantic import BaseModel, Field

from models.user import Role, OrganizationalUnit, DEFAULT_ROLES
from models.workflow import WorkflowDefinition, build_standard_workflow
from models.client import ClientField
from models.loan_request import RequestSection, build_default_sections


class BankConfiguration(BaseModel):
    """
    Top-level configuration object.
    One instance per bank deployment; loaded at startup.
    """
    bank_name: str
    org_units: list[OrganizationalUnit] = Field(default_factory=list)
    roles: list[Role] = Field(default_factory=lambda: list(DEFAULT_ROLES))
    workflow: WorkflowDefinition = Field(default_factory=build_standard_workflow)
    client_fields: list[ClientField] = Field(default_factory=list)
    request_sections: list[RequestSection] = Field(default_factory=build_default_sections)

    # Escalation thresholds (also embedded in the workflow transitions)
    escalation_head_credit_threshold: float = 500_000
    escalation_md_threshold: float = 2_000_000
    escalation_board_threshold: float = 10_000_000

    def get_role(self, role_id: str) -> Optional[Role]:
        return next((r for r in self.roles if r.id == role_id), None)

    def get_org_unit(self, unit_id: str) -> Optional[OrganizationalUnit]:
        return next((u for u in self.org_units if u.id == unit_id), None)

    def add_org_unit(self, unit: OrganizationalUnit) -> None:
        if self.get_org_unit(unit.id):
            raise ValueError(f"Org unit '{unit.id}' already exists.")
        self.org_units.append(unit)

    def add_role(self, role: Role) -> None:
        if self.get_role(role.id):
            raise ValueError(f"Role '{role.id}' already exists.")
        self.roles.append(role)


def build_sample_configuration() -> BankConfiguration:
    """
    Returns a ready-to-use sample configuration for a mid-sized bank.
    """
    config = BankConfiguration(bank_name="Sample National Bank")

    config.add_org_unit(OrganizationalUnit(id="HO", name="Head Office", code="HO"))
    config.add_org_unit(OrganizationalUnit(id="BR01", name="Downtown Branch", code="BR01", parent_id="HO"))
    config.add_org_unit(OrganizationalUnit(id="BR02", name="Uptown Branch", code="BR02", parent_id="HO"))

    config.client_fields = [
        ClientField(key="date_of_birth", label="Date of Birth", field_type="date"),
        ClientField(key="client_category", label="Client Category", field_type="dropdown",
                    options=["Individual", "SME", "Corporate", "Government"]),
        ClientField(key="industry_sector", label="Industry Sector", field_type="text"),
        ClientField(key="address", label="Address", field_type="text"),
    ]

    return config
