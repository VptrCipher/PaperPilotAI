from typing import Annotated, Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

Intent = Literal["summary", "concepts", "slides", "viva", "clarification", "general"]
Difficulty = Literal["easy", "intermediate", "advanced"]
ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
Bullet = Annotated[ShortText, Field(max_length=125)]


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Route(Record):
    intent: Intent
    scope: Literal["broad", "targeted"]
    revision: bool
    slide_count: int = Field(ge=5, le=10)
    question_count: int = Field(ge=1, le=15)
    difficulty: Literal["mixed", "easy", "intermediate", "advanced"]
    reason: str = Field(max_length=85)
    clarification: str = Field(max_length=160)


class Decision(Record):
    action: Literal["retrieve", "reuse_context", "clarify"]
    search_query: str = Field(max_length=180)
    reason: str = Field(max_length=85)
    clarification: str = Field(max_length=160)


class Cited(Record):
    source_pages: list[int]


class Section(Cited):
    text: ShortText


class Summary(Record):
    overview: Section
    problem: Section
    objective: Section
    methodology: Section
    findings: Section
    contributions: Section
    limitations: Section
    conclusion: Section


class Concept(Cited):
    name: ShortText
    explanation: ShortText
    kind: Literal["paper", "background"]


class Slide(Cited):
    title: ShortText = Field(max_length=85)
    bullets: list[Bullet] = Field(min_length=1, max_length=4)


class VivaItem(Cited):
    question: ShortText
    answer: ShortText
    difficulty: Difficulty


class Concepts(Record):
    concepts: list[Concept] = Field(min_length=1, max_length=12)


class Slides(Record):
    slides: list[Slide] = Field(min_length=5, max_length=10)


class Viva(Record):
    questions: list[VivaItem] = Field(min_length=1, max_length=15)


class Evaluation(Record):
    """Advisory feedback on a typed viva answer. Scores are model judgments, not measurements of ability."""

    correctness: int = Field(ge=0, le=5)
    depth: int = Field(ge=0, le=5)
    clarity: int = Field(ge=0, le=5)
    feedback: ShortText = Field(max_length=600)
    next_step: ShortText = Field(max_length=250)
    source_pages: list[int] = Field(min_length=1)


Data = TypeVar("Data")


class Answer(Record, Generic[Data]):
    status: Literal["ok", "insufficient"]
    data: Data | None
    note: str
