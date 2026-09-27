from fastapi import FastAPI
from fastapi.responses import FileResponse

from app.api.routes import configure_routes
from app.core.orchestrator import ConversationEngine
from app.storage.session_store import InMemorySessionStore

app = FastAPI(title="Digitomics Conversational Workflow Builder", version="0.1.0")
store = InMemorySessionStore()
engine = ConversationEngine(store)
app.include_router(configure_routes(store, engine))


@app.get("/", include_in_schema=False)
async def index():
    return FileResponse("web/index.html")


@app.get("/health")
async def health():
    return {"status": "ok"}
