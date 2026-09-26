from pydantic import BaseModel, Field


class Evidence(BaseModel):
    claim: str
    source_title: str = ""
    source_url: str = ""
    supporting_text: str = ""
    confidence: str = "unknown"


class EvidenceSet(BaseModel):
    items: list[Evidence] = Field(default_factory=list)
