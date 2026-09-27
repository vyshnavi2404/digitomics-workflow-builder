import pytest

from app.core.orchestrator import ConversationEngine
from app.storage.session_store import InMemorySessionStore


@pytest.mark.asyncio
async def test_never_generates_before_required_information():
    store = InMemorySessionStore()
    engine = ConversationEngine(store)
    state = store.create()

    reply, ready, workflow = await engine.handle(
        state,
        "Whenever I receive invoices, notify my finance team.",
    )

    assert ready is False
    assert workflow is None
    assert "Gmail" in reply or "Outlook" in reply


@pytest.mark.asyncio
async def test_generates_after_all_fields_are_collected():
    store = InMemorySessionStore()
    engine = ConversationEngine(store)
    state = store.create()

    messages = [
        "Whenever I receive invoices, notify my finance team.",
        "Gmail",
        "Finance",
        "Only invoices above $10,000",
        "Slack",
        "#finance",
    ]

    ready = False
    workflow = None

    for message in messages:
        _, ready, workflow = await engine.handle(state, message)

    assert ready is True
    assert workflow is not None
    assert workflow["nodes"][0]["type"] == "gmail_trigger"
    assert workflow["nodes"][-1]["recipient"] == "#finance"


@pytest.mark.asyncio
async def test_database_workflow_generates_after_required_information():
    store = InMemorySessionStore()
    engine = ConversationEngine(store)
    state = store.create()

    messages = [
        (
            "Whenever a new customer record is added to my "
            "PostgreSQL database, send a notification to #sales."
        ),
        "customers",
    ]

    ready = False
    workflow = None

    for message in messages:
        _, ready, workflow = await engine.handle(state, message)

    assert ready is True
    assert workflow is not None

    assert workflow["name"] == "Database notification workflow"

    assert workflow["nodes"][0] == {
        "id": "trigger",
        "type": "database_trigger",
        "event": "new_record",
        "database": "PostgreSQL",
        "table": "customers",
    }

    assert workflow["nodes"][-1] == {
        "id": "notify",
        "type": "slack_notification",
        "recipient": "#sales",
    }

    assert workflow["edges"] == [
        {
            "from": "trigger",
            "to": "notify",
        }
    ]

@pytest.mark.asyncio
async def test_acknowledgement_does_not_satisfy_database_table():
    store = InMemorySessionStore()
    engine = ConversationEngine(store)
    state = store.create()

    _, ready, workflow = await engine.handle(
        state,
        (
            "Whenever a new customer record is added to my "
            "PostgreSQL database, send a notification to #sales."
        ),
    )

    assert ready is False
    assert workflow is None

    reply, ready, workflow = await engine.handle(
        state,
        "ok",
    )

    assert ready is False
    assert workflow is None
    assert "database table" in reply.lower()

    assert state.requirements["table"].status.value == "unknown"

@pytest.mark.asyncio
async def test_scheduled_workflow_generates_after_required_information():
    store = InMemorySessionStore()
    engine = ConversationEngine(store)
    state = store.create()

    messages = [
        "Every Monday at 9 AM, send the sales report to #sales.",
    ]

    ready = False
    workflow = None

    for message in messages:
        _, ready, workflow = await engine.handle(state, message)

    assert ready is True
    assert workflow is not None

    assert workflow["name"] == "Scheduled report workflow"

    assert workflow["nodes"][0] == {
        "id": "schedule",
        "type": "schedule_trigger",
        "schedule": "every monday at 9 am",
    }

    assert workflow["nodes"][1] == {
        "id": "action",
        "type": "action",
        "description": "send the sales report",
    }

    assert workflow["nodes"][2] == {
        "id": "notify",
        "type": "notification",
        "recipient": "#sales",
    }

    assert workflow["edges"] == [
        {
            "from": "schedule",
            "to": "action",
        },
        {
            "from": "action",
            "to": "notify",
        },
    ]