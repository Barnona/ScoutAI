# ScoutAI Next.js Console

Gaming-inspired research command interface for ScoutAI.

## Run

From the repository root:

    cd frontend
    npm install
    npm run dev

Open http://localhost:3000.

The frontend expects the FastAPI backend at http://localhost:8000. Set NEXT_PUBLIC_API_URL to change it.

The dashboard consumes POST /api/research/stream and displays the live research trace, source count, contradiction count, and final report.