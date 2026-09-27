import pytest

from app.services.llm import MockExtractor


@pytest.mark.asyncio
async def test_extracts_database_workflow_facts():
    extractor = MockExtractor()

    result = await extractor.extract(
        (
            "Whenever a new customer record is added to my "
            "PostgreSQL database, send a notification to #sales."
        ),
        "database_notification",
    )

    facts = {fact.key: fact.value for fact in result.facts}

    assert facts["database"] == "PostgreSQL"
    assert facts["notification_channel"] == "Slack"
    assert facts["recipient"] == "#sales"


@pytest.mark.asyncio
async def test_extracts_mysql_database():
    extractor = MockExtractor()

    result = await extractor.extract(
        "Monitor my MySQL database and notify #sales.",
        "database_notification",
    )

    facts = {fact.key: fact.value for fact in result.facts}

    assert facts["database"] == "MySQL"
    assert facts["notification_channel"] == "Slack"
    assert facts["recipient"] == "#sales"


@pytest.mark.asyncio
async def test_does_not_invent_missing_database():
    extractor = MockExtractor()

    result = await extractor.extract(
        "Whenever a new customer record is added, notify #sales.",
        "database_notification",
    )

    fact_keys = {fact.key for fact in result.facts}

    assert "database" not in fact_keys
    assert "recipient" in fact_keys