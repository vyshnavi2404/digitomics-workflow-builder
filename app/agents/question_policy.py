from app.domain.models import Requirement, RequirementStatus, WorkflowState


def dependency_satisfied(
    requirement: Requirement,
    state: WorkflowState,
) -> bool:
    return all(
        state.requirements.get(dep) is not None
        and state.requirements[dep].status == RequirementStatus.SATISFIED
        for dep in requirement.depends_on
    )


def current_requirement(
    state: WorkflowState,
) -> Requirement | None:
    """
    Return the first unresolved requirement whose dependencies
    are satisfied.

    Used to determine what the user's latest message is answering.
    """

    for requirement in state.requirements.values():
        if not requirement.required:
            continue

        if requirement.status == RequirementStatus.SATISFIED:
            continue

        if dependency_satisfied(requirement, state):
            return requirement

    return None


def next_requirement(
    state: WorkflowState,
) -> Requirement | None:
    """
    Return the next requirement that should be presented to the user.

    An already-asked requirement is normally skipped, unless it is
    ambiguous or its previous answer was not actually accepted.
    """

    for requirement in state.requirements.values():
        if not requirement.required:
            continue

        if requirement.status == RequirementStatus.SATISFIED:
            continue

        if not dependency_satisfied(requirement, state):
            continue

        # If the requirement is unresolved and its question was already
        # asked, we still need to surface it again. This is especially
        # important when the user provides an acknowledgement such as
        # "ok" instead of an actual value.
        if (
            requirement.status == RequirementStatus.AMBIGUOUS
            or requirement.question not in state.asked_questions
        ):
            return requirement

        # An unresolved requirement whose question was already asked
        # is still the current requirement when no later requirement
        # can be satisfied yet.
        return requirement

    return None


def is_complete(state: WorkflowState) -> bool:
    return all(
        (not requirement.required)
        or requirement.status == RequirementStatus.SATISFIED
        for requirement in state.requirements.values()
    )