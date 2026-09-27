from app.agents.compiler import compile_workflow, validate_compiled
from app.agents.intent_gateway import IntentGateway
from app.agents.question_policy import (
    current_requirement,
    is_complete,
    next_requirement,
)
from app.agents.workflow_resolver import WorkflowTypeResolver
from app.domain.catalog import CATALOG, new_requirements
from app.domain.models import IntentType, RequirementStatus, WorkflowState
from app.services.llm import build_extractor


class ConversationEngine:
    def __init__(self, store) -> None:
        self.store = store
        self.extractor = build_extractor()
        self.intent_gateway = IntentGateway()
        self.workflow_resolver = WorkflowTypeResolver()

    async def handle(self, state: WorkflowState, message: str):
        state.messages.append(
            {"role": "user", "content": message}
        )

        workflow_selection_pending = (
            state.workflow_type is None
            and any(
                "What kind of automation would you like to build?" in question
                for question in state.asked_questions
            )
        )

        intent = self.intent_gateway.classify(
            message,
            workflow_exists=state.workflow_type is not None,
            workflow_selection_pending=workflow_selection_pending,
        )

        if intent.intent == IntentType.OUT_OF_SCOPE:
            reply = (
                "I'm focused on building automation workflows rather than "
                "answering general informational questions. "
                "If you'd like to automate something, tell me what should "
                "trigger the workflow and what should happen afterward."
            )
            state.messages.append(
                {"role": "assistant", "content": reply}
            )
            self.store.save(state)
            return reply, False, None

        if intent.intent == IntentType.AMBIGUOUS:
            reply = (
                "Are you asking me to build an automation workflow, "
                "or are you looking for a general answer?"
            )

            if reply not in state.asked_questions:
                state.asked_questions.append(reply)

            state.messages.append(
                {"role": "assistant", "content": reply}
            )
            self.store.save(state)
            return reply, False, None

        if state.workflow_type is None:
            resolved_type = self.workflow_resolver.resolve(message)

            if resolved_type:
                state.workflow_type = resolved_type
                state.requirements = new_requirements(
                    CATALOG[resolved_type]
                )

        if not state.workflow_type:
            category = self.workflow_resolver.category(message)

            if category == "email":
                reply = (
                    "What should the email automation do? "
                    "For example, monitor incoming invoices, "
                    "send notifications, or trigger an action "
                    "when a new email arrives."
                )
            elif category == "database":
                reply = (
                    "What should happen when the database changes? "
                    "For example, notify someone when a new record "
                    "is added."
                )
            elif category == "scheduled":
                reply = (
                    "What would you like to happen on a schedule? "
                    "Please include what should run and, if you know it, "
                    "how often it should run."
                )
            else:
                reply = (
                    "What kind of automation would you like to build? "
                    "For example, you can describe an email, database, "
                    "or scheduled workflow."
                )

            if reply not in state.asked_questions:
                state.asked_questions.append(reply)

            state.messages.append(
                {"role": "assistant", "content": reply}
            )
            self.store.save(state)
            return reply, False, None

        expected_requirement = current_requirement(state)

        expected_key = (
            expected_requirement.key
            if expected_requirement is not None
            else None
        )

        extraction = await self.extractor.extract(
            message,
            state.workflow_type,
            expected_key,
        )

        updated_requirements: list[str] = []

        for fact in extraction.facts:
            requirement = state.requirements.get(fact.key)

            if not requirement:
                continue

            evidence = {
                "value": fact.value,
                "source_message": message,
                "confidence": fact.confidence,
            }

            requirement.evidence.append(evidence)

            if fact.ambiguous or fact.confidence < 0.70:
                requirement.status = RequirementStatus.AMBIGUOUS
            else:
                previous_value = requirement.value

                requirement.value = fact.value
                requirement.status = RequirementStatus.SATISFIED

                if previous_value != fact.value:
                    updated_requirements.append(requirement.key)

        if is_complete(state):
            workflow = compile_workflow(state)
            validate_compiled(workflow)

            state.generated_workflow = workflow

            if intent.intent == IntentType.WORKFLOW_UPDATE:
                if updated_requirements:
                    changes = []

                    for requirement_key in updated_requirements:
                        requirement = state.requirements.get(requirement_key)

                        if requirement is None:
                            continue

                        changes.append(
                            f"{requirement.label.lower()} "
                            f"to {requirement.value}"
                        )

                    if changes:
                        reply = (
                            f"Updated {' and '.join(changes)}. "
                            "Here is the revised workflow representation."
                        )
                    else:
                        reply = (
                            "I've updated the workflow. "
                            "Here is the revised workflow representation."
                        )
                else:
                    reply = (
                        "I've updated the workflow. "
                        "Here is the revised workflow representation."
                    )
            else:
                reply = (
                    "Great — I have all required information. "
                    "Here is the workflow representation."
                )

            state.messages.append(
                {"role": "assistant", "content": reply}
            )
            self.store.save(state)
            return reply, True, workflow

        requirement = next_requirement(state)

        if requirement is None:
            reply = (
                "One of the requirements is still ambiguous. "
                "Please clarify the previous answer."
            )
        else:
            reply = requirement.question

            if reply not in state.asked_questions:
                state.asked_questions.append(reply)

        state.messages.append(
            {"role": "assistant", "content": reply}
        )
        self.store.save(state)

        return reply, False, None