import pytest

from app.core.orchestrator import ConversationEngine
from app.storage.session_store import InMemorySessionStore


@pytest.mark.asyncio
async def test_scheduled_workflow_does_not_generate_with_missing_action():
    store = InMemorySessionStore()
    engine = ConversationEngine(store)
    state = store.create()

    reply, ready, workflow = await engine.handle(
        state,
        "Every Monday at 9 AM",
    )

    assert ready is False
    assert workflow is None
    assert "what should the workflow do" in reply.lower()


@pytest.mark.asyncio
async def test_email_category_does_not_assume_invoice_workflow():
    store = InMemorySessionStore()
    engine = ConversationEngine(store)
    state = store.create()

    reply, ready, workflow = await engine.handle(
        state,
        "email regarding sales",
    )

    assert ready is False
    assert workflow is None
    assert "email automation" in reply.lower()
    assert state.workflow_type is None


@pytest.mark.asyncio
async def test_unsupported_workflow_does_not_generate():
    store = InMemorySessionStore()
    engine = ConversationEngine(store)
    state = store.create()

    reply, ready, workflow = await engine.handle(
        state,
        "Whenever something unusual happens, launch a rocket.",
    )

    assert ready is False
    assert workflow is None
    assert state.workflow_type is None
    assert "automation" in reply.lower()


@pytest.mark.asyncio
async def test_scheduled_followup_extracts_action_and_recipient():
    store = InMemorySessionStore()
    engine = ConversationEngine(store)
    state = store.create()

    _, ready, workflow = await engine.handle(
        state,
        "Every Monday at 9 AM",
    )

    assert ready is False
    assert workflow is None

    _, ready, workflow = await engine.handle(
        state,
        "send the sales report to #sales team",
    )

    assert ready is True
    assert workflow is not None

    assert workflow["nodes"][1]["description"] == "send the sales report"
    assert workflow["nodes"][2]["recipient"] == "#sales"


@pytest.mark.asyncio
async def test_workflow_correction_updates_compiled_graph():
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

    for message in messages:
        await engine.handle(state, message)

    assert state.generated_workflow is not None
    assert (
        state.generated_workflow["nodes"][-1]["recipient"]
        == "#sales"
    )

    reply, ready, workflow = await engine.handle(
        state,
        "Actually, send it to #marketing instead.",
    )

    assert ready is True
    assert workflow is not None
    assert "#marketing" in reply

    assert (
        workflow["nodes"][-1]["recipient"]
        == "#marketing"
    )

    assert (
        state.requirements["recipient"].value
        == "#marketing"
    )