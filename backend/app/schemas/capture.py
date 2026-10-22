from datetime import datetime
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.schemas.validation import NonBlank

ShortText = Annotated[NonBlank, Field(max_length=2000)]
ObservationType = Literal["learned", "understood_self_report", "difficulty", "open_question", "intended_next_step"]


class ObservationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    observation_type: ObservationType
    topic: Annotated[NonBlank, Field(max_length=255)]
    content: ShortText
    evidence: Annotated[str, Field(max_length=2000)] = ""


class Interpretation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    subject: Annotated[str, Field(max_length=255)] | None = None
    topics: list[Annotated[NonBlank, Field(max_length=255)]] = Field(default_factory=list, max_length=30)
    observations: list[ObservationInput] = Field(default_factory=list, max_length=50)
    duration_minutes: Annotated[int, Field(ge=1, strict=True)] | None = None
    duration_evidence: Annotated[str, Field(max_length=500)] | None = None
    ambiguity: Annotated[str, Field(max_length=2000)] | None = None

    @field_validator("topics")
    @classmethod
    def deduplicate(cls, topics):
        unique = {}
        for topic in topics:
            value = " ".join(topic.split())
            unique.setdefault(value.casefold(), value)
        return list(unique.values())


class AnalyzeInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: Annotated[NonBlank, Field(max_length=20000)]
    source_type: Literal["text", "voice"] = "text"
    learning_track_id: int | None = None


class ConfirmInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_version: int = Field(gt=0)
    interpretation: Interpretation
    learning_track_id: int | None = None
    create_memories: bool = False


class VersionInput(BaseModel):
    expected_version: int = Field(gt=0)


class ObservationResponse(ObservationInput):
    model_config = ConfigDict(from_attributes=True)
    id: int
    memory_id: int | None
    provenance: str


class CaptureResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    source_type: str
    original_text: str
    proposed_interpretation: Interpretation | None
    confirmed_interpretation: Interpretation | None
    status: str
    version: int
    learning_track_id: int | None
    study_log_id: int | None
    created_at: datetime
    confirmed_at: datetime | None
    observations: list[ObservationResponse] = Field(default_factory=list)
    matching_track_ids: list[int] = Field(default_factory=list)
    message: str | None = None
