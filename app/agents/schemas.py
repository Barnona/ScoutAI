from pydantic import BaseModel, Field


class ResearchTask(BaseModel):
    task_id: int
    question: str
    reason: str = ""


class ResearchPlan(BaseModel):
    objective: str
    tasks: list[ResearchTask] = Field(default_factory=list)
