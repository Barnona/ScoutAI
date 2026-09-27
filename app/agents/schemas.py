"""Structured models used across ScoutAI's research pipeline."""

from pydantic import BaseModel, Field


class ResearchTask(BaseModel):
    task_id: int
    question: str
    reason: str = ""


class ResearchPlan(BaseModel):
    objective: str
    tasks: list[ResearchTask] = Field(default_factory=list)


class SourceRecord(BaseModel):
    source_id: str
    title: str = ""
    url: str = ""
    snippet: str = ""
    publisher: str = ""
    quality_score: int = 0
    quality_tier: str = "unknown"
    quality_reasons: list[str] = Field(default_factory=list)


class Evidence(BaseModel):
    claim: str
    source_ids: list[str] = Field(default_factory=list)
    supporting_text: str = ""
    confidence: str = "unknown"


class VerifiedClaim(BaseModel):
    claim: str
    status: str = "unverified"
    source_ids: list[str] = Field(default_factory=list)
    reasoning: str = ""


class Contradiction(BaseModel):
    topic: str
    claim_a: str
    claim_b: str
    source_a: list[str] = Field(default_factory=list)
    source_b: list[str] = Field(default_factory=list)
    explanation: str = ""


class ResearchResult(BaseModel):
    question: str
    plan: ResearchPlan
    sources: list[SourceRecord] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    verified_claims: list[VerifiedClaim] = Field(default_factory=list)
    contradictions: list[Contradiction] = Field(default_factory=list)
    report: str
