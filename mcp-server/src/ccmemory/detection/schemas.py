"""Pydantic schemas for LLM detection outputs."""

from pydantic import BaseModel


class DecisionResult(BaseModel):
    isDecision: bool
    confidence: float
    description: str | None = None
    rationale: str | None = None
    revisitTrigger: str | None = None


class CorrectionResult(BaseModel):
    isCorrection: bool
    confidence: float
    wrongBelief: str | None = None
    rightBelief: str | None = None
    severity: str | None = None


class ExceptionResult(BaseModel):
    isException: bool
    confidence: float
    ruleBroken: str | None = None
    justification: str | None = None
    scope: str | None = None


class InsightResult(BaseModel):
    isInsight: bool
    confidence: float
    category: str | None = None
    summary: str | None = None
    implications: str | None = None


class QuestionResult(BaseModel):
    isQuestion: bool
    confidence: float
    question: str | None = None
    answer: str | None = None
    context: str | None = None


class FailedApproachResult(BaseModel):
    isFailedApproach: bool
    confidence: float
    approach: str | None = None
    outcome: str | None = None
    lesson: str | None = None


class RerankResult(BaseModel):
    indices: list[int]
