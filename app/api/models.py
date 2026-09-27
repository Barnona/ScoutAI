from typing import Literal
from pydantic import BaseModel, Field


class ResearchRequest(BaseModel):
    question: str = Field(min_length=3, max_length=10000)
    depth: Literal["quick", "standard", "deep", "investigative"] = "standard"


class ResearchResponse(BaseModel):
    question: str
    report: dict


class ResearchEventResponse(BaseModel):
    type: str
    message: str
    data: dict = {}
    timestamp: str
