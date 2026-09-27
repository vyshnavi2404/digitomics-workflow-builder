import re

from app.domain.models import IntentResult, IntentType


WORKFLOW_SIGNALS = (
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
    "automate",
    "automation",
    "workflow",
    "whenever",
    "when a new",
    "when i receive",
    "when i get",
    "send a notification",
    "send notifications",
    "notify",
    "notification",
    "trigger",
    "every time",
    "each time",
    "monitor",
    "incoming",
    "if",
    "every weekday",
    "every day",
    "daily",
    "weekly",
    "monthly",
    "scheduled",
    "schedule",
    "invoice",
    "invoices",
    "bill",
    "billing",
    "email",
    "emails",
    "mail",
    "inbox",
    "database",
    "db",
    "record",
    "records",
    "customer",
    "customers",
)

GENERAL_QUESTION_SIGNALS = (
    "what is",
    "what are",
    "explain",
    "how do i",
    "how to",
    "difference between",
    "define",
    "meaning of",
    "why is",
    "why are",
)

UPDATE_SIGNALS = (
    "actually",
    "instead",
    "change",
    "don't",
    "do not",
    "replace",
    "remove",
    "use",
)


def _contains_phrase(message: str, phrase: str) -> bool:
    return re.search(
        rf"\b{re.escape(phrase)}\b",
        message.lower(),
    ) is not None


def _is_general_question(message: str) -> bool:
    return any(
        _contains_phrase(message, signal)
        for signal in GENERAL_QUESTION_SIGNALS
    )


def _is_workflow_request(message: str) -> bool:
    return any(
        _contains_phrase(message, signal)
        for signal in WORKFLOW_SIGNALS
    )


def _is_update(message: str) -> bool:
    return any(
        _contains_phrase(message, signal)
        for signal in UPDATE_SIGNALS
    )


class IntentGateway:
    def classify(
        self,
        message: str,
        workflow_exists: bool = False,
        workflow_selection_pending: bool = False,
    ) -> IntentResult:

        message = message.strip()

        # If a workflow already exists, interpret subsequent messages
        # in the context of that workflow.
        if workflow_exists:
            if _is_update(message):
                return IntentResult(
                    intent=IntentType.WORKFLOW_UPDATE,
                    confidence=0.95,
                    reason="The user appears to be correcting or modifying an existing workflow.",
                )

            if _is_general_question(message):
                return IntentResult(
                    intent=IntentType.OUT_OF_SCOPE,
                    confidence=0.96,
                    reason="The message is a general knowledge question rather than a workflow request.",
                )

            return IntentResult(
                intent=IntentType.WORKFLOW_UPDATE,
                confidence=0.90,
                reason="The conversation already contains a workflow, so the message is interpreted in that workflow context.",
            )

        # If the system is waiting for the user to select a workflow
        # category, the response belongs to that selection flow.
        if workflow_selection_pending:
            if _is_general_question(message):
                return IntentResult(
                    intent=IntentType.OUT_OF_SCOPE,
                    confidence=0.96,
                    reason="The user asked a general question instead of selecting a workflow type.",
                )

            return IntentResult(
                intent=IntentType.WORKFLOW_REQUEST,
                confidence=0.92,
                reason="The user is responding to the workflow-type selection question.",
            )

        # General questions must be checked BEFORE workflow keywords.
        # Example:
        # "What is database normalization?"
        #
        # contains "database", but is not a workflow request.
        if _is_general_question(message):
            return IntentResult(
                intent=IntentType.OUT_OF_SCOPE,
                confidence=0.96,
                reason="The message is a general knowledge question rather than an automation request.",
            )

        if _is_workflow_request(message):
            return IntentResult(
                intent=IntentType.WORKFLOW_REQUEST,
                confidence=0.90,
                reason="The message contains language associated with an automation or workflow request.",
            )

        return IntentResult(
            intent=IntentType.AMBIGUOUS,
            confidence=0.50,
            reason="The message does not clearly identify an automation request or a general question.",
        )