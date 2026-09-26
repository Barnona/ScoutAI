# ScoutAI — Autonomous Evidence-Based Research Agent

ScoutAI is a Python-first research agent that plans searches, retrieves current web evidence through SerpApi, cross-checks sources, and produces a structured report.

## v0.2 — Zero-OpenAI MVP

This version uses:
- Google GenAI SDK
- Gemma 3 (`gemma-3-27b-it` by default)
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
Gemma 3 — research planning
  ↓
SerpApi — live web search
  ↓
Evidence collection
  ↓
Gemma 3 — synthesis + contradiction reporting
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
GEMMA_MODEL=gemma-3-27b-it
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

## FastAPI

```powershell
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs`.

## Cost

ScoutAI no longer requires OpenAI API access. Google's Gemini API has a free tier for supported models, subject to account/model rate limits. SerpApi also has account/search limits. No paid API subscription is required for the project itself.

If `gemma-3-27b-it` is unavailable for your Google AI Studio project, change `GEMMA_MODEL` to a Gemma model that your API key exposes.

Never commit `.env` or API keys.
