from fastapi import APIRouter, HTTPException

from app.domain.models import ChatRequest, ChatResponse

router = APIRouter(prefix="/api")


def configure_routes(store, engine):
    @router.post("/sessions")
    async def create_session():
        return store.create()

    @router.post("/chat", response_model=ChatResponse)
    async def chat(request: ChatRequest):
        try:
            state = store.get(request.session_id)
        except KeyError:
            raise HTTPException(status_code=404, detail="Unknown session")
        reply, ready, workflow = await engine.handle(state, request.message)
        return ChatResponse(session_id=state.session_id, reply=reply, ready=ready, state=state, workflow=workflow)

    return router
