from app.domain.catalog import CATALOG


WORKFLOW_SIGNALS = {
    "invoice_notification": (
        "invoice",
        "invoices",
        "bill",
        "billing",
    ),
    "database_notification": (
        "database",
        "db",
        "postgresql",
        "postgres",
        "mysql",
        "sql server",
        "customer record",
        "customer records",
        "new customer",
        "customer is added",
        "customer added",
        "new record",
        "record added",
        "record is added",
        "records added",
        "table",
    ),
    "scheduled_report": (
        "weekdays",
        "every day",
        "daily",
        "weekly",
        "monthly",
        "scheduled",
        "schedule",
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
        "report",
    ),
}


CATEGORY_SIGNALS = {
    "email": (
        "email",
        "emails",
        "mail",
        "inbox",
    ),
    "database": (
        "database",
        "db",
        "postgresql",
        "postgres",
        "mysql",
        "sql server",
        "table",
        "record",
        "records",
        "customer",
        "customers",
    ),
    "scheduled": (
        "scheduled",
        "schedule",
        "daily",
        "weekly",
        "monthly",
        "weekdays",
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
    ),
}


class WorkflowTypeResolver:

    def _score(self, message: str, signals: tuple[str, ...]) -> int:
        lower = message.lower()
        return sum(1 for signal in signals if signal in lower)

    def resolve(self, message: str) -> str | None:
        lower = message.lower()

        scores = {}

        for workflow_type, signals in WORKFLOW_SIGNALS.items():
            if workflow_type not in CATALOG:
                continue

            score = self._score(lower, signals)

            if score > 0:
                scores[workflow_type] = score

        if not scores:
            return None

        highest = max(scores.values())

        winners = [
            workflow_type
            for workflow_type, score in scores.items()
            if score == highest
        ]

        # Never guess when two workflow types have equal evidence.
        if len(winners) != 1:
            return None

        return winners[0]

    def category(self, message: str) -> str | None:
        lower = message.lower()

        scores = {
            name: self._score(lower, signals)
            for name, signals in CATEGORY_SIGNALS.items()
        }

        scores = {
            name: score
            for name, score in scores.items()
            if score > 0
        }

        if not scores:
            return None

        highest = max(scores.values())

        winners = [
            name
            for name, score in scores.items()
            if score == highest
        ]

        if len(winners) != 1:
            return None

        return winners[0]