from app.domain.models import WorkflowState


def compile_workflow(state: WorkflowState) -> dict:
    """
    Compile a validated requirement state into a structured workflow graph.

    The compiler is responsible only for transforming completed workflow
    requirements into a deterministic representation. It does not decide
    whether the requirements are complete.
    """

    if state.workflow_type == "invoice_notification":
        return _compile_invoice_notification(state)

    if state.workflow_type == "database_notification":
        return _compile_database_notification(state)

    if state.workflow_type == "scheduled_report":
        return _compile_scheduled_report(state)

    raise ValueError(
        f"Unsupported workflow type: {state.workflow_type}"
    )


def _compile_invoice_notification(state: WorkflowState) -> dict:
    r = state.requirements
    condition = r["condition"].value

    return {
        "name": "Invoice notification workflow",
        "nodes": [
            {
                "id": "trigger",
                "type": f"{str(r['trigger_source'].value).lower()}_trigger",
                "event": "new_invoice",
                "location": r["monitor_location"].value,
            },
            {
                "id": "filter",
                "type": "condition",
                "expression": condition,
            },
            {
                "id": "notify",
                "type": (
                    f"{str(r['notification_channel'].value).lower()}"
                    "_notification"
                ),
                "recipient": r["recipient"].value,
            },
        ],
        "edges": [
            {"from": "trigger", "to": "filter"},
            {"from": "filter", "to": "notify", "when": "condition_met"},
        ],
    }


def _compile_database_notification(state: WorkflowState) -> dict:
    r = state.requirements

    return {
        "name": "Database notification workflow",
        "nodes": [
            {
                "id": "trigger",
                "type": "database_trigger",
                "event": "new_record",
                "database": r["database"].value,
                "table": r["table"].value,
            },
            {
                "id": "notify",
                "type": (
                    f"{str(r['notification_channel'].value).lower()}"
                    "_notification"
                ),
                "recipient": r["recipient"].value,
            },
        ],
        "edges": [
            {
                "from": "trigger",
                "to": "notify",
            }
        ],
    }


def _compile_scheduled_report(state: WorkflowState) -> dict:
    r = state.requirements

    return {
        "name": "Scheduled report workflow",
        "nodes": [
            {
                "id": "schedule",
                "type": "schedule_trigger",
                "schedule": r["schedule"].value,
            },
            {
                "id": "action",
                "type": "action",
                "description": r["action"].value,
            },
            {
                "id": "notify",
                "type": "notification",
                "recipient": r["recipient"].value,
            },
        ],
        "edges": [
            {
                "from": "schedule",
                "to": "action",
            },
            {
                "from": "action",
                "to": "notify",
            },
        ],
    }


def validate_compiled(workflow: dict) -> None:
    """
    Validate the structural integrity of a compiled workflow graph.
    """

    nodes = workflow.get("nodes", [])
    edges = workflow.get("edges", [])

    if not nodes:
        raise ValueError("Compiled workflow contains no nodes")

    ids = {node["id"] for node in nodes}

    if len(ids) != len(nodes):
        raise ValueError("Compiled workflow contains duplicate node IDs")

    for edge in edges:
        if edge["from"] not in ids or edge["to"] not in ids:
            raise ValueError("Workflow contains an invalid edge")