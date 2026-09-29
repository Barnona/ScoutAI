import asyncio
import json
import time
import uuid

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse, Response

from app.agents.research_agent import run_research
from app.api.models import ResearchRequest, ResearchResponse
from app.research.attachments import extract_attachment, AttachmentContext
from app.reports.pdf import build_research_pdf

router = APIRouter(prefix="/api", tags=["research"])

# In-memory mission registry. A Render instance keeps a mission alive even if
# the browser temporarily disconnects. Completed missions are retained briefly
# so a reconnecting client can recover the final result and trace.
MISSIONS: dict[str, dict] = {}
MISSION_TTL_SECONDS = 30 * 60


def _cleanup_missions() -> None:
    cutoff = time.time() - MISSION_TTL_SECONDS
    stale = [
        run_id
        for run_id, mission in MISSIONS.items()
        if mission.get("finished_at", 0) and mission["finished_at"] < cutoff
    ]
    for run_id in stale:
        MISSIONS.pop(run_id, None)


async def _read_attachments(files: list[UploadFile] | None) -> list[AttachmentContext]:
    attachments = []
    for file in files or []:
        data = await file.read()
        try:
            attachments.append(extract_attachment(file.filename or "attachment", data))
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    return attachments


def _create_mission(question: str, depth: str, attachments: list[AttachmentContext]) -> str:
    _cleanup_missions()
    run_id = uuid.uuid4().hex
    mission = {
        "question": question,
        "depth": depth,
        "events": [],
        "result": None,
        "error": None,
        "done": False,
        "finished_at": 0,
        "created_at": time.time(),
    }
    MISSIONS[run_id] = mission

    def emit(event: dict):
        mission["events"].append(event)

    async def runner():
        try:
            mission["result"] = await run_research(
                question,
                emit=emit,
                depth=depth,
                attachments=attachments,
            )
            mission["events"].append({
                "type": "complete",
                "message": "Research complete",
                "data": {"result": mission["result"]},
            })
        except Exception as exc:
            mission["error"] = str(exc)
            mission["events"].append({
                "type": "error",
                "message": str(exc),
                "data": {},
            })
        finally:
            mission["done"] = True
            mission["finished_at"] = time.time()

    mission["task"] = asyncio.create_task(runner())
    return run_id


def _event_stream(run_id: str) -> StreamingResponse:
    async def stream():
        mission = MISSIONS.get(run_id)
        if not mission:
            yield f"data: {json.dumps({'type': 'error', 'message': 'Research mission not found.', 'data': {}}, ensure_ascii=False)}\n\n"
            return

        cursor = 0
        while True:
            mission = MISSIONS.get(run_id)
            if not mission:
                return

            events = mission["events"]
            while cursor < len(events):
                event = dict(events[cursor])
                event["_seq"] = cursor
                cursor += 1
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

            if mission["done"] and cursor >= len(mission["events"]):
                break

            await asyncio.sleep(0.35)

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-store",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.post("/research", response_model=ResearchResponse)
async def research(
    question: str = Form(...),
    depth: str = Form("standard"),
    files: list[UploadFile] | None = File(default=None),
) -> ResearchResponse:
    request = ResearchRequest(question=question, depth=depth)
    attachments = await _read_attachments(files)
    try:
        report = await run_research(request.question, depth=request.depth, attachments=attachments)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return ResearchResponse(question=request.question, report=report)


@router.post("/research/stream")
async def research_stream(
    question: str = Form(...),
    depth: str = Form("standard"),
    run_id: str | None = Form(default=None),
    files: list[UploadFile] | None = File(default=None),
) -> StreamingResponse:
    if run_id and run_id in MISSIONS:
        return _event_stream(run_id)

    attachments = await _read_attachments(files)
    ResearchRequest(question=question, depth=depth)
    run_id = _create_mission(question, depth, attachments)
    return _event_stream(run_id)


@router.get("/research/stream/{run_id}")
async def research_reconnect(run_id: str) -> StreamingResponse:
    return _event_stream(run_id)


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
