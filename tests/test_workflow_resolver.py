from app.agents.workflow_resolver import WorkflowTypeResolver


def test_resolves_invoice_workflow():
    resolver = WorkflowTypeResolver()

    result = resolver.resolve(
        "Whenever I receive invoices, notify my finance team."
    )

    assert result == "invoice_notification"


def test_resolves_database_workflow():
    resolver = WorkflowTypeResolver()

    result = resolver.resolve(
        "Whenever a new customer record is added to my database, "
        "notify the sales team."
    )

    assert result == "database_notification"


def test_unknown_workflow_returns_none():
    resolver = WorkflowTypeResolver()

    result = resolver.resolve(
        "Whenever something unusual happens, do something automatically."
    )

    assert result is None