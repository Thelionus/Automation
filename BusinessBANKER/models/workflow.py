"""
Workflow engine models for BusinessBANKER.
Steps, routing conditions, and transitions are fully configurable.
"""
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


class ConditionOperator(str, Enum):
    GT = ">"
    GTE = ">="
    LT = "<"
    LTE = "<="
    EQ = "=="
    NEQ = "!="
    IN = "in"
    NOT_IN = "not_in"


class RoutingCondition(BaseModel):
    """
    A single condition used to decide whether a step transition fires.
    Example: field="amount", operator=">", value=500000 → escalate to MD
    """
    field: str
    operator: ConditionOperator
    value: Any

    def evaluate(self, context: dict[str, Any]) -> bool:
        field_val = context.get(self.field)
        if field_val is None:
            return False
        op = self.operator
        v = self.value
        if op == ConditionOperator.GT:
            return float(field_val) > float(v)
        elif op == ConditionOperator.GTE:
            return float(field_val) >= float(v)
        elif op == ConditionOperator.LT:
            return float(field_val) < float(v)
        elif op == ConditionOperator.LTE:
            return float(field_val) <= float(v)
        elif op == ConditionOperator.EQ:
            return str(field_val) == str(v)
        elif op == ConditionOperator.NEQ:
            return str(field_val) != str(v)
        elif op == ConditionOperator.IN:
            return field_val in v
        elif op == ConditionOperator.NOT_IN:
            return field_val not in v
        return False


class StepTransition(BaseModel):
    """
    A directed edge in the workflow graph.
    If all conditions evaluate to True, the request moves to target_step_id.
    Transitions are evaluated in priority order; first match wins.
    """
    id: str
    target_step_id: str
    label: str = ""
    conditions: list[RoutingCondition] = Field(default_factory=list)
    priority: int = 0  # lower = higher priority

    def is_applicable(self, context: dict[str, Any]) -> bool:
        """Return True if all conditions pass (unconditional if no conditions)."""
        return all(c.evaluate(context) for c in self.conditions)


class SectionPermission(BaseModel):
    """Per-section, per-step access rights for a given role."""
    role_id: str
    can_read: bool = False
    can_write: bool = False


class WorkflowStep(BaseModel):
    """
    A discrete stage in the decision lifecycle.
    Each step has an assigned role, a status label, and outbound transitions.
    """
    id: str
    name: str
    assigned_role_id: str
    status_label: str  # shown on the request card in portfolio view
    transitions: list[StepTransition] = Field(default_factory=list)
    section_permissions: list[SectionPermission] = Field(default_factory=list)
    is_terminal: bool = False  # True for Disbursed / Declined / Closed

    def next_step(self, context: dict[str, Any]) -> Optional[str]:
        """
        Evaluate outbound transitions and return the target step id,
        or None if no transition is applicable.
        """
        sorted_transitions = sorted(self.transitions, key=lambda t: t.priority)
        for transition in sorted_transitions:
            if transition.is_applicable(context):
                return transition.target_step_id
        return None


class WorkflowDefinition(BaseModel):
    """The complete workflow graph for a bank configuration."""
    id: str
    name: str
    steps: list[WorkflowStep] = Field(default_factory=list)
    initial_step_id: str

    def get_step(self, step_id: str) -> Optional[WorkflowStep]:
        return next((s for s in self.steps if s.id == step_id), None)


# ---- Standard banking workflow definition ----

def build_standard_workflow() -> WorkflowDefinition:
    """
    Constructs the default three-department banking workflow with
    amount-based escalation paths as described in spec §3.
    """
    steps = [
        WorkflowStep(
            id="initiation",
            name="Initiation",
            assigned_role_id="rm",
            status_label="In Preparation",
            transitions=[
                StepTransition(
                    id="t1",
                    target_step_id="credit_analysis",
                    label="Submit to Credit Analysis",
                    priority=0,
                )
            ],
        ),
        WorkflowStep(
            id="credit_analysis",
            name="Credit Analysis",
            assigned_role_id="analyst",
            status_label="Under Credit Review",
            transitions=[
                StepTransition(
                    id="t2",
                    target_step_id="adjudication",
                    label="Forward to Adjudicator",
                    priority=0,
                )
            ],
        ),
        WorkflowStep(
            id="adjudication",
            name="Adjudication",
            assigned_role_id="adjudicator",
            status_label="Pending Credit Decision",
            transitions=[
                # Escalate to Head of Credit for amounts > 500 000
                StepTransition(
                    id="t3a",
                    target_step_id="head_credit_review",
                    label="Escalate → Head of Credit",
                    conditions=[
                        RoutingCondition(field="amount", operator=ConditionOperator.GT, value=500_000)
                    ],
                    priority=0,
                ),
                # Approve within delegated authority
                StepTransition(
                    id="t3b",
                    target_step_id="legal",
                    label="Approve → Legal",
                    priority=1,
                ),
                StepTransition(
                    id="t3c",
                    target_step_id="declined",
                    label="Decline",
                    priority=2,
                ),
            ],
        ),
        WorkflowStep(
            id="head_credit_review",
            name="Head of Credit Review",
            assigned_role_id="head_credit",
            status_label="Under Head of Credit Review",
            transitions=[
                # Escalate to MD for amounts > 2 000 000
                StepTransition(
                    id="t4a",
                    target_step_id="md_approval",
                    label="Escalate → Managing Director",
                    conditions=[
                        RoutingCondition(field="amount", operator=ConditionOperator.GT, value=2_000_000)
                    ],
                    priority=0,
                ),
                StepTransition(
                    id="t4b",
                    target_step_id="legal",
                    label="Approve → Legal",
                    priority=1,
                ),
                StepTransition(
                    id="t4c",
                    target_step_id="declined",
                    label="Decline",
                    priority=2,
                ),
            ],
        ),
        WorkflowStep(
            id="md_approval",
            name="Managing Director Approval",
            assigned_role_id="md",
            status_label="Pending MD Approval",
            transitions=[
                # Board approval for very large deals > 10 000 000
                StepTransition(
                    id="t5a",
                    target_step_id="board_approval",
                    label="Escalate → Board",
                    conditions=[
                        RoutingCondition(field="amount", operator=ConditionOperator.GT, value=10_000_000)
                    ],
                    priority=0,
                ),
                StepTransition(
                    id="t5b",
                    target_step_id="legal",
                    label="Approve → Legal",
                    priority=1,
                ),
                StepTransition(
                    id="t5c",
                    target_step_id="declined",
                    label="Decline",
                    priority=2,
                ),
            ],
        ),
        WorkflowStep(
            id="board_approval",
            name="Board Approval",
            assigned_role_id="board",
            status_label="Pending Board Approval",
            transitions=[
                StepTransition(
                    id="t6a",
                    target_step_id="legal",
                    label="Board Approved → Legal",
                    priority=0,
                ),
                StepTransition(
                    id="t6b",
                    target_step_id="declined",
                    label="Decline",
                    priority=1,
                ),
            ],
        ),
        WorkflowStep(
            id="legal",
            name="Legal & Documentation",
            assigned_role_id="legal",
            status_label="Legal Processing",
            transitions=[
                StepTransition(
                    id="t7",
                    target_step_id="disbursement",
                    label="Forward to Operations",
                    priority=0,
                )
            ],
        ),
        WorkflowStep(
            id="disbursement",
            name="Disbursement",
            assigned_role_id="ops",
            status_label="Approved — Pending Disbursement",
            transitions=[
                StepTransition(
                    id="t8",
                    target_step_id="completed",
                    label="Disburse Funds",
                    priority=0,
                )
            ],
        ),
        WorkflowStep(
            id="completed",
            name="Completed",
            assigned_role_id="ops",
            status_label="Disbursed",
            is_terminal=True,
        ),
        WorkflowStep(
            id="declined",
            name="Declined",
            assigned_role_id="adjudicator",
            status_label="Declined",
            is_terminal=True,
        ),
    ]

    return WorkflowDefinition(
        id="standard_banking",
        name="Standard Banking Workflow",
        steps=steps,
        initial_step_id="initiation",
    )
