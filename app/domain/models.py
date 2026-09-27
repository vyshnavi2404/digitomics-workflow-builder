from __future__ import annotations

from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

class IntentType(str, Enum):
    WORKFLOW_REQUEST = "workflow_request"
    WORKFLOW_UPDATE = "workflow_update"
    AMBIGUOUS = "ambiguous"
    OUT_OF_SCOPE = "out_of_scope"


class IntentResult(BaseModel):
    intent: IntentType
    confidence: float = Field(ge=0, le=1)
    reason: str

class RequirementStatus(str, Enum):
    UNKNOWN = "unknown"
    SATISFIED = "satisfied"
    AMBIGUOUS = "ambiguous"


class Evidence(BaseModel):
    value: Any
    source_message: str
    confidence: float = Field(ge=0, le=1)


class Requirement(BaseModel):
    key: str
    label: str
    required: bool = True
    status: RequirementStatus = RequirementStatus.UNKNOWN
    evidence: list[Evidence] = Field(default_factory=list)
    value: Any | None = None
    question: str
    depends_on: list[str] = Field(default_factory=list)


class WorkflowState(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid4()))
    workflow_type: str | None = None
    requirements: dict[str, Requirement] = Field(default_factory=dict)
    asked_questions: list[str] = Field(default_factory=list)
    messages: list[dict[str, str]] = Field(default_factory=list)
    generated_workflow: dict[str, Any] | None = None


class ExtractedFact(BaseModel):
    key: str
    value: Any
    confidence: float = Field(ge=0, le=1)
    ambiguous: bool = False


class ExtractionResult(BaseModel):
    workflow_type: str | None = None
    facts: list[ExtractedFact] = Field(default_factory=list)


class ChatRequest(BaseModel):
    session_id: str
    message: str = Field(min_length=1)


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    ready: bool
    state: WorkflowState
    workflow: dict[str, Any] | None = None
