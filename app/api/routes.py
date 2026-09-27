import asyncio
import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.agents.research_agent import run_research
from app.api.models import ResearchRequest, ResearchResponse

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

        task = asyncio.create_task(run_research(request.question, emit=emit))

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
