import asyncio
import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse, Response

from app.agents.research_agent import run_research
from app.api.models import ResearchRequest, ResearchResponse
from app.reports.pdf import build_research_pdf

router = APIRouter(prefix="/api", tags=["research"])


@router.post("/research", response_model=ResearchResponse)
async def research(request: ResearchRequest) -> ResearchResponse:
    try:
        report = await run_research(request.question, depth=request.depth)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return ResearchResponse(question=request.question, report=report)


@router.post("/research/stream")
async def research_stream(request: ResearchRequest) -> StreamingResponse:
    async def event_stream():
        queue: asyncio.Queue[dict] = asyncio.Queue()
        loop = asyncio.get_running_loop()

        def emit(event: dict):
            loop.call_soon_threadsafe(queue.put_nowait, event)

        task = asyncio.create_task(run_research(request.question, emit=emit, depth=request.depth))

        try:
            while True:
                if task.done() and queue.empty():
                    break
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=0.25)
                except asyncio.TimeoutError:
                    continue
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

            result = await task
            yield f"data: {json.dumps({'type': 'complete', 'message': 'Research complete', 'data': {'result': result}}, ensure_ascii=False)}\n\n"
        except Exception as exc:
            if not task.done():
                task.cancel()
            yield f"data: {json.dumps({'type': 'error', 'message': str(exc), 'data': {}}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/research/pdf")
async def research_pdf(payload: dict) -> Response:
    report = payload.get("report")
    depth = payload.get("depth", "standard")

    if not isinstance(report, dict):
        raise HTTPException(status_code=400, detail="A completed research report is required.")

    try:
        pdf = await asyncio.to_thread(build_research_pdf, report, depth)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {exc}") from exc

    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="scoutai-research-report.pdf"'},
    )
