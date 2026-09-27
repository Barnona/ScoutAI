# ScoutAI — Autonomous Evidence-Based Research Agent

ScoutAI is a Python-first research agent that plans searches, retrieves current web evidence through SerpApi, cross-checks sources, challenges unresolved evidence, and produces a structured report.

## v0.3 — Adaptive Research Intelligence

This version uses:
- Google GenAI SDK
- Configurable Gemma model (the repository default is `gemma-4-31b-it`)
- SerpApi Python SDK
- FastAPI
- FAISS scaffolding for future RAG

**OpenAI and the OpenAI Agents SDK are not required.**

### Architecture

```text
User
  ↓
ScoutAI
  ↓
Gemma — research planning
  ↓
SerpApi — live web search
  ↓
Evidence collection
  ↓
Gemma — synthesis + contradiction reporting
  ↓
Cited research report
```

## Setup — Windows PowerShell

Activate your existing environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install the new dependencies:

```powershell
pip install -r requirements.txt
```

Create `.env`:

```powershell
Copy-Item .env.example .env
```

Edit `.env`:

```env
GEMINI_API_KEY=your_google_ai_studio_key
GEMMA_MODEL=gemma-4-31b-it
SERPAPI_API_KEY=your_serpapi_key
MAX_SEARCHES=5
MAX_SOURCES=12
```

## Run

```powershell
python -m scripts.run_agent
```

Example:

```text
Compare current RISC-V edge AI development boards suitable for engineering students.
```

## Live Research Trace

ScoutAI also exposes a Server-Sent Events endpoint for a live agent trace. It reports planning, searching, source collection, verification, contradiction analysis, follow-up searches, and synthesis as the research runs.

```text
POST /api/research/stream
Content-Type: application/json

{"question":"Your research question"}
```

Example event flow:

```text
planning → planning_complete → searching → sources_found
→ verifying → contradictions → followup_search
→ synthesizing → complete
```

This endpoint is intended for the upcoming React/Next.js dashboard and can also be consumed by any SSE-capable client.

## FastAPI

```powershell
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs`.

## Cost

ScoutAI no longer requires OpenAI API access. Google's Gemini API has a free tier for supported models, subject to account/model rate limits. SerpApi also has account/search limits. No paid API subscription is required for the project itself.

If `gemma-3-27b-it` is unavailable for your Google AI Studio project, change `GEMMA_MODEL` to a Gemma model that your API key exposes.

Never commit `.env` or API keys.


## Research depth

The API and web console support four evidence budgets:

| Mode | Search tasks | Source cap | Verification rounds | Follow-up queries |
|---|---:|---:|---:|---:|
| Quick | 3 | 7 | 1 | 2 |
| Standard | 5 | 12 | 2 | 4 |
| Deep | 7 | 18 | 3 | 5 |
| Investigative | 9 | 24 | 4 | 7 |

The agent can stop a verification round early when no unresolved claims or contradictions require follow-up research.

## Source quality signals

Each normalized source receives a transparent heuristic quality signal based on URL/domain and publisher indicators. The score is surfaced in the console alongside the source rather than being treated as a hidden model judgment. Claim verification still relies on the supplied evidence itself.
