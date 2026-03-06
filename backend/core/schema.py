"""
Pydantic schemas for API request/response validation.
"""

from pydantic import BaseModel, Field
from typing import Optional


# ── Content ───────────────────────────────────────────────

class ContentItemResponse(BaseModel):
    id: int
    type: str
    title: str
    url: str
    source_name: str
    source_tier: str
    published_at: Optional[str] = None
    tags: list[str] = []
    summary: dict = {}
    content_length: int = 0


class ContentSearchResponse(BaseModel):
    items: list[ContentItemResponse]
    total: int
    disclaimer: str = "Educational content only. Not medical advice. If worried, seek professional care."


class ContentDetailResponse(ContentItemResponse):
    text: Optional[str] = None
    transcript: Optional[str] = None
    trust_card: dict = {}
    related_topics: list[dict] = []
    disclaimer: str = "Educational content only. Not medical advice. If worried, seek professional care."


class ContentQARequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=500)


class ContentQAResponse(BaseModel):
    answer: str
    grounded: bool = True
    source_title: str = ""
    source_name: str = ""
    disclaimer: str = "Educational content only. Not medical advice. If worried, seek professional care."


class ContentExplainResponse(BaseModel):
    explanation: str
    level: str = "standard"  # simple | standard | detailed
    source_title: str = ""
    disclaimer: str = "Educational content only. Not medical advice. If worried, seek professional care."


# ── Chat ────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str = Field(..., pattern=r"^(user|assistant|system)$")
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]


class ChatResponse(BaseModel):
    answer: str
    grounded: bool = True
    citations: list[dict] = []
    disclaimer: str = "Educational content only. Not medical advice. If worried, seek professional care."


# ── Family ────────────────────────────────────────────────

class CreateFamilyGroupRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class CreateFamilyGroupResponse(BaseModel):
    id: int
    name: str
    created_at: str


class MemberPreferences(BaseModel):
    content_format: str = Field(default="all", pattern=r"^(video|text|all)$")
    language: str = "en"
    length_preference: str = Field(default="any", pattern=r"^(short|long|any)$")


class AddFamilyMemberRequest(BaseModel):
    group_id: int
    name: str = ""
    age_band: str = Field(..., pattern=r"^(kid|teen|adult|senior)$")
    preferences: MemberPreferences = MemberPreferences()
    topics: list[str] = []


class FamilyMemberResponse(BaseModel):
    id: int
    group_id: int
    name: str
    age_band: str
    preferences: MemberPreferences
    topics: list[str]


class FamilyGroupDetailResponse(BaseModel):
    id: int
    name: str
    created_at: str
    members: list[FamilyMemberResponse] = []


class SaveItemRequest(BaseModel):
    group_id: int
    content_id: int


class SaveItemResponse(BaseModel):
    id: int
    group_id: int
    content_id: int
    saved_at: str


# ── Triage ────────────────────────────────────────────────

class TriageRunRequest(BaseModel):
    topic: str
    answers: dict[str, bool] = {}  # question_id -> yes/no


class TriageQuestion(BaseModel):
    id: str
    text: str


class TriageRunResponse(BaseModel):
    urgency: str  # emergency | soon | routine
    message: str
    source_refs: list[dict] = []
    specialist: dict = {}
    disclaimer: str = "Educational content only. Not medical advice. If worried, seek professional care."


class TriageQuestionsResponse(BaseModel):
    topic: str
    universal_questions: list[TriageQuestion]
    topic_questions: list[TriageQuestion]
    disclaimer: str = "Educational content only. Not medical advice. If worried, seek professional care."


# ── LLM Summary Schema ───────────────────────────────────

class LLMSummaryOutput(BaseModel):
    summary: str = ""
    key_points: list[str] = []
    warnings: list[str] = []
    topic_tags: list[str] = []


class LLMTagOutput(BaseModel):
    topic_tags: list[str] = []
