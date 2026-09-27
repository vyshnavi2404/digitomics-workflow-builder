from app.agents.question_policy import is_complete, next_requirement
from app.domain.catalog import INVOICE_NOTIFICATION, new_requirements
from app.domain.models import RequirementStatus, WorkflowState


def test_dependencies_hide_recipient_question_until_channel_known():
    state = WorkflowState(workflow_type=INVOICE_NOTIFICATION.key, requirements=new_requirements(INVOICE_NOTIFICATION))
    req = next_requirement(state)
    assert req.key == "trigger_source"
    state.requirements["trigger_source"].status = RequirementStatus.SATISFIED
    state.requirements["trigger_source"].value = "Gmail"
    req = next_requirement(state)
    assert req.key == "monitor_location"
