from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod

import httpx

from app.core.config import settings
from app.domain.models import ExtractionResult, ExtractedFact


class Extractor(ABC):
    @abstractmethod
    async def extract(
        self,
        message: str,
        workflow_type: str | None,
        expected_requirement: str | None = None,
    ) -> ExtractionResult:
        raise NotImplementedError


class MockExtractor(Extractor):
    """
    Deterministic extractor used for local demos and tests.

    Workflow type resolution is handled separately by WorkflowTypeResolver.
    This class only extracts explicit requirement values.
    """

    async def extract(
        self,
        message: str,
        workflow_type: str | None,
        expected_requirement: str | None = None,
    ) -> ExtractionResult:
        text = message.strip()
        lower = text.lower()
        facts: list[ExtractedFact] = []

        non_values = {
            "ok",
            "okay",
            "yes",
            "yeah",
            "yep",
            "sure",
            "fine",
            "done",
            "got it",
            "correct",
            "right",
            "no problem",
        }

        is_non_value = lower in non_values

        if workflow_type == "invoice_notification":
            if "gmail" in lower:
                facts.append(
                    ExtractedFact(
                        key="trigger_source",
                        value="Gmail",
                        confidence=0.99,
                    )
                )
            elif "outlook" in lower:
                facts.append(
                    ExtractedFact(
                        key="trigger_source",
                        value="Outlook",
                        confidence=0.99,
                    )
                )

            for folder in re.findall(
                r"(?:label|folder|mailbox)\s*(?:is|:)?\s*"
                r"([A-Za-z0-9_-]+)",
                text,
                re.I,
            ):
                facts.append(
                    ExtractedFact(
                        key="monitor_location",
                        value=folder,
                        confidence=0.90,
                    )
                )

            if (
                expected_requirement == "monitor_location"
                and not is_non_value
                and lower in {
                    "finance",
                    "the finance folder",
                    "finance folder",
                }
            ):
                facts.append(
                    ExtractedFact(
                        key="monitor_location",
                        value="Finance",
                        confidence=0.98,
                    )
                )

            amount = re.search(
                r"(?:above|over|greater than|more than)"
                r"\s*\$?\s*([\d,]+(?:\.\d+)?)",
                lower,
            )

            if amount:
                value = float(amount.group(1).replace(",", ""))
                facts.append(
                    ExtractedFact(
                        key="condition",
                        value={"operator": ">", "amount": value},
                        confidence=0.99,
                    )
                )
            elif "every invoice" in lower or "all invoices" in lower:
                facts.append(
                    ExtractedFact(
                        key="condition",
                        value={"operator": "all"},
                        confidence=0.98,
                    )
                )

        elif workflow_type == "database_notification":
            database_patterns = {
                "postgresql": "PostgreSQL",
                "postgres": "PostgreSQL",
                "mysql": "MySQL",
                "sql server": "SQL Server",
                "mssql": "SQL Server",
            }

            for signal, database_name in database_patterns.items():
                if signal in lower:
                    facts.append(
                        ExtractedFact(
                            key="database",
                            value=database_name,
                            confidence=0.99,
                        )
                    )
                    break

            table_match = re.search(
                r"(?:table|table name)"
                r"\s*(?:is|:)?\s*"
                r"[`'\"]?([A-Za-z_][A-Za-z0-9_]*)[`'\"]?",
                text,
                re.I,
            )

            if table_match:
                facts.append(
                    ExtractedFact(
                        key="table",
                        value=table_match.group(1),
                        confidence=0.95,
                    )
                )
            elif re.search(r"\bcustomer\s+table\b", lower):
                facts.append(
                    ExtractedFact(
                        key="table",
                        value="customers",
                        confidence=0.90,
                    )
                )
            elif (
                expected_requirement == "table"
                and not is_non_value
            ):
                simple_identifier = re.fullmatch(
                    r"[A-Za-z_][A-Za-z0-9_]*",
                    text,
                )
                if simple_identifier:
                    facts.append(
                        ExtractedFact(
                            key="table",
                            value=text,
                            confidence=0.95,
                        )
                    )

        elif workflow_type == "scheduled_report":
            schedule_patterns = (
                r"every\s+(?:monday|tuesday|wednesday|thursday|"
                r"friday|saturday|sunday)"
                r"(?:\s+at\s+\d{1,2}(?::\d{2})?\s*(?:am|pm)?)?",
                r"every\s+(?:day|week|month)"
                r"(?:\s+at\s+\d{1,2}(?::\d{2})?\s*(?:am|pm)?)?",
                r"daily(?:\s+at\s+\d{1,2}(?::\d{2})?\s*(?:am|pm)?)?",
                r"weekly(?:\s+at\s+\d{1,2}(?::\d{2})?\s*(?:am|pm)?)?",
                r"monthly(?:\s+at\s+\d{1,2}(?::\d{2})?\s*(?:am|pm)?)?",
            )

            schedule_match = None

            for pattern in schedule_patterns:
                match = re.search(pattern, lower)
                if match:
                    schedule_match = match.group(0)
                    break

            if schedule_match:
                facts.append(
                    ExtractedFact(
                        key="schedule",
                        value=schedule_match,
                        confidence=0.95,
                    )
                )

            if not is_non_value:
                action_text = text

                if schedule_match:
                    action_text = text[
                        len(schedule_match):
                    ].strip(" ,.")

                destination_match = re.search(
                    r"\s+(?:to|for)\s+"
                    r"(?:the\s+)?"
                    r"(#[A-Za-z0-9_-]+|"
                    r"[\w.+-]+@[\w-]+\.[\w.-]+)"
                    r"(?:\s+team)?"
                    r"\s*[.!]?$",
                    action_text,
                    re.I,
                )

                if destination_match:
                    recipient = destination_match.group(1)

                    facts.append(
                        ExtractedFact(
                            key="recipient",
                            value=recipient,
                            confidence=0.99,
                        )
                    )

                    action_text = action_text[
                        :destination_match.start()
                    ].strip(" ,.")

                if (
                    action_text
                    and (
                        expected_requirement == "action"
                        or schedule_match
                    )
                ):
                    facts.append(
                        ExtractedFact(
                            key="action",
                            value=action_text,
                            confidence=0.90,
                        )
                    )

        if "slack" in lower:
            facts.append(
                ExtractedFact(
                    key="notification_channel",
                    value="Slack",
                    confidence=0.99,
                )
            )

        channel = re.search(r"(#[A-Za-z0-9_-]+)", text)

        if channel:
            facts.append(
                ExtractedFact(
                    key="notification_channel",
                    value="Slack",
                    confidence=0.99,
                )
            )

            facts.append(
                ExtractedFact(
                    key="recipient",
                    value=channel.group(1),
                    confidence=0.99,
                )
            )

        email = re.search(
            r"[\w.+-]+@[\w-]+\.[\w.-]+",
            text,
        )

        if email:
            facts.append(
                ExtractedFact(
                    key="recipient",
                    value=email.group(0),
                    confidence=0.99,
                )
            )

        if workflow_type == "database_notification":
            sales_match = re.search(
                r"(?:notify|send.*to)\s+"
                r"(?:the\s+)?"
                r"([A-Za-z][A-Za-z ]*?)"
                r"(?:\s+team)?[.!]?$",
                text,
                re.I,
            )

            if sales_match:
                recipient = sales_match.group(1).strip()

                if recipient.lower() not in {
                    "the",
                    "team",
                    "user",
                }:
                    facts.append(
                        ExtractedFact(
                            key="recipient",
                            value=recipient,
                            confidence=0.80,
                        )
                    )

        return ExtractionResult(
            workflow_type=workflow_type,
            facts=facts,
        )


class OpenAICompatibleExtractor(Extractor):
    """
    Minimal OpenAI-compatible HTTP boundary.

    The model extracts facts, while deterministic application logic
    remains responsible for completeness, validation, and compilation.
    """

    async def extract(
        self,
        message: str,
        workflow_type: str | None,
        expected_requirement: str | None = None,
    ) -> ExtractionResult:
        schema = {
            "type": "object",
            "properties": {
                "workflow_type": {"type": ["string", "null"]},
                "facts": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "key": {"type": "string"},
                            "value": {},
                            "confidence": {"type": "number"},
                            "ambiguous": {"type": "boolean"},
                        },
                        "required": [
                            "key",
                            "value",
                            "confidence",
                            "ambiguous",
                        ],
                        "additionalProperties": False,
                    },
                },
            },
            "required": ["workflow_type", "facts"],
            "additionalProperties": False,
        }

        prompt = (
            "Extract only explicit workflow facts from the user's "
            "message. Never infer missing information.\n"
            f"Current workflow type: {workflow_type!r}\n"
            f"Expected requirement: {expected_requirement!r}\n"
            f"Message: {message!r}\n"
            f"Return JSON matching this schema: {json.dumps(schema)}"
        )

        headers = {
            "Authorization": f"Bearer {settings.llm_api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": settings.llm_model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a strict information extractor. "
                        "Extract explicit facts only. "
                        "Never invent missing values."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "response_format": {
                "type": "json_object",
            },
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{settings.llm_base_url.rstrip('/')}/chat/completions",
                headers=headers,
                json=payload,
            )

            response.raise_for_status()

            content = response.json()[
                "choices"
            ][0]["message"]["content"]

        return ExtractionResult.model_validate_json(content)


def build_extractor() -> Extractor:
    if (
        settings.llm_provider.lower() == "mock"
        or not settings.llm_api_key
    ):
        return MockExtractor()

    return OpenAICompatibleExtractor()