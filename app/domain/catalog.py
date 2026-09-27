from dataclasses import dataclass

from app.domain.models import Requirement


@dataclass(frozen=True)
class WorkflowDefinition:
    key: str
    name: str
    requirements: tuple[Requirement, ...]


INVOICE_NOTIFICATION = WorkflowDefinition(
    key="invoice_notification",
    name="Invoice notification",
    requirements=(
        Requirement(
            key="trigger_source",
            label="Trigger source",
            question="Which email service should I monitor — Gmail or Outlook?",
        ),
        Requirement(
            key="monitor_location",
            label="Monitor location",
            question="Which Gmail label/folder or Outlook folder should I monitor?",
            depends_on=["trigger_source"],
        ),
        Requirement(
            key="condition",
            label="Condition",
            question=(
                "Should every invoice trigger the workflow, "
                "or only invoices above a specific amount?"
            ),
        ),
        Requirement(
            key="notification_channel",
            label="Notification channel",
            question="Where should the notification be sent — Slack or email?",
        ),
        Requirement(
            key="recipient",
            label="Recipient/channel",
            question=(
                "Which Slack channel or email address should receive "
                "the notification?"
            ),
            depends_on=["notification_channel"],
        ),
    ),
)


DATABASE_NOTIFICATION = WorkflowDefinition(
    key="database_notification",
    name="Database notification",
    requirements=(
        Requirement(
            key="database",
            label="Database",
            question=(
                "Which database should I monitor, such as PostgreSQL, "
                "MySQL, or SQL Server?"
            ),
        ),
        Requirement(
            key="table",
            label="Table",
            question="Which database table should I monitor for new records?",
            depends_on=["database"],
        ),
        Requirement(
            key="notification_channel",
            label="Notification channel",
            question="Where should the notification be sent — Slack or email?",
        ),
        Requirement(
            key="recipient",
            label="Recipient/channel",
            question=(
                "Which Slack channel or email address should receive "
                "the notification?"
            ),
            depends_on=["notification_channel"],
        ),
    ),
)


SCHEDULED_REPORT = WorkflowDefinition(
    key="scheduled_report",
    name="Scheduled report",
    requirements=(
        Requirement(
            key="schedule",
            label="Schedule",
            question=(
                "When should this workflow run? "
                "For example, every Monday at 9 AM."
            ),
        ),
        Requirement(
            key="action",
            label="Action",
            question="What should the workflow do when it runs?",
        ),
        Requirement(
            key="recipient",
            label="Recipient/destination",
            question=(
                "Where should the result be sent — for example, "
                "a Slack channel or email address?"
            ),
        ),
    ),
)


CATALOG = {
    INVOICE_NOTIFICATION.key: INVOICE_NOTIFICATION,
    DATABASE_NOTIFICATION.key: DATABASE_NOTIFICATION,
    SCHEDULED_REPORT.key: SCHEDULED_REPORT,
}


def new_requirements(
    definition: WorkflowDefinition,
) -> dict[str, Requirement]:
    return {
        requirement.key: requirement.model_copy(deep=True)
        for requirement in definition.requirements
    }