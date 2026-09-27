from app.domain.models import WorkflowState


class InMemorySessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, WorkflowState] = {}

    def create(self) -> WorkflowState:
        state = WorkflowState()
        self._sessions[state.session_id] = state
        return state

    def get(self, session_id: str) -> WorkflowState:
        if session_id not in self._sessions:
            raise KeyError(session_id)
        return self._sessions[session_id]

    def save(self, state: WorkflowState) -> None:
        self._sessions[state.session_id] = state
