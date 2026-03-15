"""
WorkflowEngine — orchestrates request progression through the workflow.
Handles step transitions, permission checks, and audit logging.
"""
from datetime import datetime
from typing import Optional
import uuid

from models.loan_request import LoanRequest, WorkflowHistoryEntry, RequestStatus
from models.workflow import WorkflowDefinition, WorkflowStep
from models.user import User, Role


STATUS_MAP: dict[str, RequestStatus] = {
    "initiation": RequestStatus.IN_PREPARATION,
    "credit_analysis": RequestStatus.UNDER_REVIEW,
    "adjudication": RequestStatus.PENDING_DECISION,
    "head_credit_review": RequestStatus.PENDING_DECISION,
    "md_approval": RequestStatus.PENDING_DECISION,
    "board_approval": RequestStatus.PENDING_DECISION,
    "legal": RequestStatus.LEGAL_PROCESSING,
    "disbursement": RequestStatus.PENDING_DISBURSEMENT,
    "completed": RequestStatus.DISBURSED,
    "declined": RequestStatus.DECLINED,
}


class WorkflowError(Exception):
    pass


class WorkflowEngine:
    """
    Core engine for BusinessBANKER.

    Usage:
        engine = WorkflowEngine(workflow_definition)
        engine.advance(request, transition_id, performed_by_user, user_role)
    """

    def __init__(self, workflow: WorkflowDefinition):
        self.workflow = workflow

    def get_current_step(self, request: LoanRequest) -> Optional[WorkflowStep]:
        return self.workflow.get_step(request.current_step_id)

    def available_transitions(self, request: LoanRequest) -> list[dict]:
        """
        Return the transitions available from the request's current step,
        evaluated against the request's current context.
        """
        step = self.get_current_step(request)
        if step is None or step.is_terminal:
            return []

        context = request.get_context()
        result = []
        for transition in sorted(step.transitions, key=lambda t: t.priority):
            result.append(
                {
                    "id": transition.id,
                    "label": transition.label,
                    "target_step_id": transition.target_step_id,
                    "applicable": transition.is_applicable(context),
                }
            )
        return result

    def can_act(self, request: LoanRequest, user: User, role: Role) -> bool:
        """
        Check whether the given user/role may act on the request at its current step.
        """
        step = self.get_current_step(request)
        if step is None:
            return False
        return step.assigned_role_id == role.id or role.permissions.can_configure

    def advance(
        self,
        request: LoanRequest,
        transition_id: str,
        performed_by: str,
        notes: str = "",
    ) -> LoanRequest:
        """
        Advance a request along the specified transition.
        Raises WorkflowError if the transition is not valid.
        """
        step = self.get_current_step(request)
        if step is None:
            raise WorkflowError(f"Step '{request.current_step_id}' not found in workflow.")
        if step.is_terminal:
            raise WorkflowError(f"Request is in a terminal state: '{step.id}'.")

        transition = next((t for t in step.transitions if t.id == transition_id), None)
        if transition is None:
            raise WorkflowError(
                f"Transition '{transition_id}' not found on step '{step.id}'."
            )

        context = request.get_context()
        if not transition.is_applicable(context):
            raise WorkflowError(
                f"Transition '{transition_id}' conditions are not met for this request."
            )

        target_step = self.workflow.get_step(transition.target_step_id)
        if target_step is None:
            raise WorkflowError(
                f"Target step '{transition.target_step_id}' does not exist in workflow."
            )

        # Record the history entry
        history_entry = WorkflowHistoryEntry(
            from_step_id=request.current_step_id,
            to_step_id=target_step.id,
            performed_by=performed_by,
            transition_id=transition_id,
            timestamp=datetime.utcnow(),
            notes=notes,
        )
        request.history.append(history_entry)

        # Move the request
        request.current_step_id = target_step.id
        request.current_status = STATUS_MAP.get(target_step.id, RequestStatus.UNDER_REVIEW)
        request.updated_at = datetime.utcnow()

        return request

    def auto_route(self, request: LoanRequest, performed_by: str = "system") -> LoanRequest:
        """
        Automatically advance a request by evaluating all transitions
        and firing the first applicable one. Used for AI agent steps.
        """
        step = self.get_current_step(request)
        if step is None or step.is_terminal:
            return request

        context = request.get_context()
        next_step_id = step.next_step(context)
        if next_step_id is None:
            return request  # no condition matched — needs human intervention

        applicable_transition = next(
            (t for t in sorted(step.transitions, key=lambda t: t.priority)
             if t.target_step_id == next_step_id and t.is_applicable(context)),
            None,
        )
        if applicable_transition:
            return self.advance(request, applicable_transition.id, performed_by)

        return request

    def get_portfolio(
        self,
        requests: list[LoanRequest],
        role_id: str,
        org_unit_id: str,
    ) -> list[LoanRequest]:
        """
        Filter requests for the portfolio view.
        Returns only requests at the step assigned to the given role and branch.
        (spec §5)
        """
        result = []
        for req in requests:
            step = self.workflow.get_step(req.current_step_id)
            if step and step.assigned_role_id == role_id:
                if req.branch_id == org_unit_id:
                    result.append(req)
        return result
