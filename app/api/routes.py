from fastapi import APIRouter, HTTPException

from app.agents.research_agent import run_research
from app.api.models import ResearchRequest, ResearchResponse

router = APIRouter(prefix="/api", tags=["research"])


@router.post("/research", response_model=ResearchResponse)
async def research(request: ResearchRequest) -> ResearchResponse:
    try:
        report = await run_research(request.question)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return ResearchResponse(
        question=request.question,
        report=report,
    )
