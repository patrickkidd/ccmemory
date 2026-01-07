"""Pydantic schemas for LLM detection outputs."""

import enum
from pydantic import BaseModel


class DetectionType(enum.StrEnum):
    Decision = "decision"
    Correction = "correction"
    Exception = "exception"
    Insight = "insight"
    Question = "question"
    FailedApproach = "failed_approach"
    Reference = "reference"
    ProjectFact = "project_fact"


class Severity(enum.StrEnum):
    Minor = "minor"
    Significant = "significant"
    Critical = "critical"


class ExceptionScope(enum.StrEnum):
    OneTime = "one-time"
    Conditional = "conditional"
    NewPrecedent = "new-precedent"


class InsightCategory(enum.StrEnum):
    Realization = "realization"
    Analysis = "analysis"
    Strategy = "strategy"
    Personal = "personal"
    Synthesis = "synthesis"


class FactCategory(enum.StrEnum):
    Tool = "tool"
    Pattern = "pattern"
    Convention = "convention"
    Environment = "environment"
    Constraint = "constraint"
    Workflow = "workflow"


class ReferenceType(enum.StrEnum):
    Url = "url"
    FilePath = "file_path"


class Decision(BaseModel):
    confidence: float
    description: str
    rationale: str | None = None
    revisitTrigger: str | None = None


class Correction(BaseModel):
    confidence: float
    wrongBelief: str
    rightBelief: str
    severity: Severity = Severity.Significant


class Exception_(BaseModel):
    confidence: float
    ruleBroken: str
    justification: str
    scope: ExceptionScope = ExceptionScope.OneTime


class Insight(BaseModel):
    confidence: float
    category: InsightCategory = InsightCategory.Realization
    summary: str
    implications: str | None = None


class Question(BaseModel):
    confidence: float
    question: str
    answer: str
    context: str | None = None


class FailedApproach(BaseModel):
    confidence: float
    approach: str
    outcome: str
    lesson: str | None = None


class ProjectFact(BaseModel):
    confidence: float
    category: FactCategory = FactCategory.Convention
    fact: str
    context: str | None = None


class Reference(BaseModel):
    type: ReferenceType
    uri: str


class ReferenceData(BaseModel):
    references: list[Reference]


class DetectionOutput(BaseModel):
    decisions: list[Decision] = []
    corrections: list[Correction] = []
    exceptions: list[Exception_] = []
    insights: list[Insight] = []
    questions: list[Question] = []
    failedApproaches: list[FailedApproach] = []
    projectFacts: list[ProjectFact] = []


class Detection(BaseModel):
    type: DetectionType
    confidence: float
    data: Decision | Correction | Exception_ | Insight | Question | FailedApproach | ProjectFact | ReferenceData


class RerankResult(BaseModel):
    indices: list[int]
