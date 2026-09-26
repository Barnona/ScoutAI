"""ScoutAI research agent powered by Google's GenAI SDK + Gemma."""

import asyncio
import json
from typing import Any

from google import genai

from config.settings import GEMINI_API_KEY, GEMMA_MODEL, MAX_SEARCHES
from app.agents.prompts import RESEARCH_AGENT_INSTRUCTIONS
from app.tools.search import web_search


class ScoutAIResearchAgent:
    def __init__(self) -> None:
        if not GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY is not configured.")
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.model = GEMMA_MODEL

    def _generate(self, prompt: str) -> str:
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
        )
        text = getattr(response, "text", None)
        if not text:
            raise RuntimeError("Gemma returned an empty response.")
        return text.strip()

    @staticmethod
    def _extract_json(text: str) -> dict[str, Any]:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`").strip()
            if cleaned.startswith("json"):
                cleaned = cleaned[4:].strip()

        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end <= start:
            raise ValueError("Gemma did not return a JSON object.")

        return json.loads(cleaned[start:end + 1])

    def _plan(self, question: str) -> list[str]:
        prompt = f"""
{RESEARCH_AGENT_INSTRUCTIONS}

Create a concise research plan for the user's question.

Return ONLY valid JSON:
{{
  "queries": [
    "search query 1",
    "search query 2"
  ]
}}

Rules:
- Generate 2 to {MAX_SEARCHES} distinct queries.
- Cover different aspects of the question.
- Prefer queries that find primary, official, technical, or academic sources.
- Do not answer the question yet.

USER QUESTION:
{question}
"""
        data = self._extract_json(self._generate(prompt))
        queries = data.get("queries", [])

        if not isinstance(queries, list):
            raise ValueError("Invalid research plan returned by Gemma.")

        return [
            q.strip() for q in queries
            if isinstance(q, str) and q.strip()
        ][:MAX_SEARCHES]

    def research(self, question: str) -> str:
        queries = self._plan(question)

        if not queries:
            return "ScoutAI could not create a research plan."

        all_sources = []
        seen_urls = set()

        for query in queries:
            try:
                results = web_search(query)
            except Exception as exc:
                all_sources.append({
                    "title": f"Search error for: {query}",
                    "url": "",
                    "snippet": str(exc),
                    "source": "SerpApi",
                })
                continue

            for item in results:
                url = item.get("url", "")
                if url and url in seen_urls:
                    continue
                if url:
                    seen_urls.add(url)
                all_sources.append(item)

        evidence = "\n\n".join(
            f"SOURCE {i + 1}\n"
            f"Title: {item.get('title', '')}\n"
            f"URL: {item.get('url', '')}\n"
            f"Snippet: {item.get('snippet', '')}\n"
            f"Publisher: {item.get('source', '')}"
            for i, item in enumerate(all_sources)
        )

        synthesis_prompt = f"""
{RESEARCH_AGENT_INSTRUCTIONS}

You are now in the SYNTHESIS stage.

USER QUESTION:
{question}

RESEARCH QUERIES:
{json.dumps(queries, ensure_ascii=False, indent=2)}

WEB EVIDENCE:
{evidence}

Produce an evidence-based research report with exactly these sections:
1. Executive Summary
2. Key Findings
3. Evidence
4. Conflicting Information / Uncertainty
5. Limitations
6. Sources

Rules:
- Use only information supported by the supplied evidence.
- Never invent facts, specifications, prices, dates, or citations.
- Distinguish facts from claims and estimates.
- If sources disagree, explicitly describe the disagreement.
- Cite sources as [S1], [S2], etc., matching the source numbers above.
- If evidence is weak, say so.
"""
        return self._generate(synthesis_prompt)

    async def run(self, question: str) -> str:
        return await asyncio.to_thread(self.research, question)


research_agent = ScoutAIResearchAgent()


async def run_research(question: str) -> str:
    return await research_agent.run(question)
