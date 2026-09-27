# ScoutAI Web Console

The ScoutAI frontend is a responsive Next.js console for the **ScoutAI Autonomous Research & Intelligence Agent**.

It provides a command-style research interface with:

- research question input
- Quick / Standard / Deep / Investigative research depth
- live Server-Sent Events research trace
- source and evidence information
- contradiction reporting
- final Intelligence Brief / research report
- source quality signals
- light and dark themes
- responsive desktop and mobile layouts

## Stack

- Next.js 16
- React 19
- JavaScript
- CSS
- Server-Sent Events (SSE)

## Requirements

- Node.js 20+
- A running ScoutAI FastAPI backend

The backend lives in the repository root.

## Local Development

From the repository root:

```powershell
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:3000
```

The frontend defaults to:

```text
http://localhost:8000
```

for the FastAPI backend.

To override the backend URL, create `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

For a deployed backend:

```env
NEXT_PUBLIC_API_URL=https://YOUR-RENDER-SERVICE.onrender.com
```

The value must be the **base backend URL**. Do not append `/api/research`.

## Build

Create a production build:

```powershell
npm run build
```

Run the production build:

```powershell
npm start
```

## Backend Connection

The console communicates with the FastAPI backend through:

```text
POST /api/research
POST /api/research/stream
```

The streaming endpoint is used by the dashboard to display the research process while it is running.

A typical trace is:

```text
planning
→ planning_complete
→ searching
→ sources_found
→ verifying
→ contradictions
→ followup_search
→ synthesizing
→ complete
```

## Research Depth

The selector maps directly to the backend research profiles:

| Mode | Searches | Sources | Verification | Follow-ups |
|---|---:|---:|---:|---:|
| Quick | 3 | 7 | 1 | 2 |
| Standard | 5 | 12 | 2 | 4 |
| Deep | 7 | 18 | 3 | 5 |
| Investigative | 9 | 24 | 4 | 7 |

## Responsive Design

The interface is designed for both desktop and phone screens.

Mobile behaviour includes:

- compressed navigation/header
- horizontally scrollable research-depth selector
- full-width research prompt
- touch-friendly controls
- stacked evidence and contradiction sections
- mobile live-trace scrolling
- 2×2 mission statistics layout
- mobile theme selector
- responsive report typography

The desktop visual language and original Launch button styling are preserved across the responsive layout.

## Deployment — Vercel

The frontend is deployed separately from the FastAPI backend.

Recommended Vercel settings:

```text
Framework Preset: Next.js
Root Directory: frontend
Build Command: npm run build
Install Command: npm install
Output Directory: default
```

Set the Vercel environment variable:

```text
NEXT_PUBLIC_API_URL=https://YOUR-RENDER-SERVICE.onrender.com
```

Redeploy after changing this variable because it is exposed to the Next.js client at build time.

## Deployment Architecture

```text
User
  │
  ▼
Vercel
  │
  │ Next.js frontend
  ▼
Render
  │
  │ FastAPI
  ├──────────────► SerpApi
  │
  └──────────────► Google AI Studio / Gemma
```

The backend must allow the deployed Vercel origin through its `FRONTEND_ORIGINS` configuration.

## Troubleshooting

### API returns 404

Verify:

1. The Render backend is running.
2. `GET /health` returns `{"status":"ok"}`.
3. `NEXT_PUBLIC_API_URL` contains only the Render base URL.
4. Vercel was redeployed after changing the environment variable.
5. The backend's `FRONTEND_ORIGINS` contains the Vercel domain.

### API URL works in the browser but research does not

That is expected if you open `/api/research` directly. Research is a POST endpoint and requires a JSON request body.

### CORS errors

Add the deployed frontend origin to the backend's `FRONTEND_ORIGINS` environment variable.

Example:

```text
http://localhost:3000,https://your-scoutai.vercel.app
```

## Repository

The frontend is part of the main ScoutAI repository:

```text
Barnona/ScoutAI
└── frontend/
```

For backend architecture, research logic, environment configuration, testing, and deployment details, see the root [README](../README.md).
