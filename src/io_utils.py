"""Pydantic models shared by the whole project."""
import uuid
from typing import List

from pydantic import BaseModel, Field


class MinimalSource(BaseModel):
    """A character range inside a file."""

    file_path: str
    first_character_index: int
    last_character_index: int


class UnansweredQuestion(BaseModel):
    """A question without ground truth."""

    question_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question: str


class AnsweredQuestion(UnansweredQuestion):
    """A question with its sources and expected answer."""

    sources: List[MinimalSource]
    answer: str


class RagDataset(BaseModel):
    """A dataset of questions (answered or not)."""

    rag_questions: List[AnsweredQuestion | UnansweredQuestion]


class MinimalSearchResults(BaseModel):
    """Retrieved sources for one question."""

    question_id: str
    question: str
    retrieved_sources: List[MinimalSource]


class MinimalAnswer(MinimalSearchResults):
    """Search results plus the generated answer."""

    answer: str


class StudentSearchResults(BaseModel):
    """Output of search_dataset."""

    search_results: List[MinimalSearchResults]
    k: int


class StudentSearchResultsAndAnswer(BaseModel):
    """Output of answer_dataset."""

    search_results: List[MinimalAnswer]
    k: int
