from pydantic import BaseModel, Field


class ResearchRequest(BaseModel):
    question: str = Field(min_length=3, max_length=10000)


class ResearchResponse(BaseModel):
    question: str
    report: dict


class ResearchEventResponse(BaseModel):
    type: str
    message: str
    data: dict = {}
    timestamp: str
