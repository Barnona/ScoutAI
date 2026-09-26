"""ScoutAI multi-stage research agent powered by Gemma + SerpApi."""

import asyncio
import json
from typing import Any

from google import genai

from config.settings import (GEMINI_API_KEY, GEMMA_MODEL, MAX_SEARCHES, MAX_SOURCES,\n    MAX_VERIFICATION_ROUNDS, MAX_FOLLOWUP_SEARCHES,)
from app.agents.schemas import ResearchPlan, ResearchResult, VerifiedClaim, Contradiction
from app.research.planner import parse_plan
from app.research.evidence import build_sources, compact_evidence
from app.research.verifier import verification_prompt
from app.research.contradiction import contradiction_prompt
from app.tools.search import web_search
from app.research.events import ResearchEvent


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
    def _json(text: str) -> dict[str, Any]:
        cleaned = text.strip()
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start < 0 or end <= start:
            raise ValueError("Gemma did not return a JSON object.")
        return json.loads(cleaned[start:end + 1])

    def _plan(self, question: str) -> ResearchPlan:
        prompt = f"""You are ScoutAI's research planner.

Break the user's broad question into independent research tasks.
Return ONLY valid JSON:
{{"tasks":[{{"question":"...","reason":"..."}}]}}

Rules:
- Generate 2 to {MAX_SEARCHES} tasks.
- Each task must investigate a different aspect.
- Prefer primary, official, academic, technical, or high-quality reporting sources.
- Do not answer the question.

USER QUESTION:
{question}
"""
        return parse_plan(self._generate(prompt), question, MAX_SEARCHES)

    async def _search_one(self, query: str) -> list[dict]:
        try:
            return await asyncio.to_thread(web_search, query)
        except Exception as exc:
            return [{
                "title": f"Search error: {query}",
                "url": "",
                "snippet": str(exc),
                "source": "SerpApi",
            }]

    def _verify(self, sources, question: str) -> list[VerifiedClaim]:
        extraction_prompt = f"""Extract the most important factual claims needed to answer:
{question}

Use ONLY the supplied source snippets. Return ONLY JSON:
{{"claims":["claim 1","claim 2"]}}

SOURCES:
{compact_evidence(sources)}
"""
        data = self._json(self._generate(extraction_prompt))
        claims = [x for x in data.get("claims", []) if isinstance(x, str)][:20]
        if not claims:
            return []

        verified = self._json(self._generate(verification_prompt(claims, sources)))
        return [
            VerifiedClaim(
                claim=item.get("claim", ""),
                status=item.get("status", "unverified"),
                source_ids=item.get("source_ids", []),
                reasoning=item.get("reasoning", ""),
            )
            for item in verified.get("claims", [])
            if isinstance(item, dict) and item.get("claim")
        ]

    def _contradictions(self, sources) -> list[Contradiction]:
        data = self._json(self._generate(contradiction_prompt(sources)))
        return [
            Contradiction(
                topic=item.get("topic", ""),
                claim_a=item.get("claim_a", ""),
                claim_b=item.get("claim_b", ""),
                source_a=item.get("source_a", []),
                source_b=item.get("source_b", []),
                explanation=item.get("explanation", ""),
            )
            for item in data.get("contradictions", [])
            if isinstance(item, dict) and item.get("claim_a") and item.get("claim_b")
        ]

    def _followup_queries(self, question, verified, contradictions) -> list[str]:
        unresolved = [
            f"Claim: {v.claim}\nStatus: {v.status}\nReason: {v.reasoning}"
            for v in verified if v.status in {"mixed", "unsupported"}
        ]
        conflicts = [
            f"Topic: {c.topic}\nA: {c.claim_a}\nB: {c.claim_b}"
            for c in contradictions
        ]
        if not unresolved and not conflicts:
            return []

        prompt = (
            "You are ScoutAI's research verifier. Generate targeted web-search "
            "queries to resolve unresolved claims or contradictions.\n\n"
            f"USER QUESTION:\n{question}\n\n"
            f"UNRESOLVED CLAIMS:\n{chr(10).join(unresolved) or 'None'}\n\n"
            f"CONTRADICTIONS:\n{chr(10).join(conflicts) or 'None'}\n\n"
            f"Return ONLY JSON: {{\"queries\":[\"query 1\",\"query 2\"]}}. "
            f"Generate at most {MAX_FOLLOWUP_SEARCHES} targeted queries. "
            "Prefer primary, official, academic, or technical sources. "
            "Do not answer the claims; only create queries."
        )
        try:
            data = self._json(self._generate(prompt))
        except Exception:
            return []
        return [
            q.strip() for q in data.get("queries", [])
            if isinstance(q, str) and q.strip()
        ][:MAX_FOLLOWUP_SEARCHES]

    def _synthesize(self, question, plan, sources, verified, contradictions) -> str:
        verification_text = "\n".join(
            f"- {v.status.upper()}: {v.claim} [{', '.join(v.source_ids)}] — {v.reasoning}"
            for v in verified
        )
        conflict_text = "\n".join(
            f"- {c.topic}: {c.claim_a} ({', '.join(c.source_a)}) VS "
            f"{c.claim_b} ({', '.join(c.source_b)}). {c.explanation}"
            for c in contradictions
        ) or "No material contradictions detected."

        prompt = f"""You are ScoutAI's final research synthesizer.

QUESTION:
{question}

RESEARCH PLAN:
{plan.model_dump_json(indent=2)}

SOURCE EVIDENCE:
{compact_evidence(sources)}

VERIFIED CLAIMS:
{verification_text}

CONTRADICTIONS:
{conflict_text}

Write a rigorous report with:
# Executive Summary
# Research Objective
# Key Findings
# Evidence & Verification
# Conflicting Information / Uncertainty
# Limitations
# Sources

Rules:
- Use only supplied evidence.
- Never invent facts or citations.
- Cite sources as [S1], [S2], etc.
- Clearly distinguish supported, mixed, and unsupported claims.
- Explicitly preserve genuine source disagreements.
- If evidence is insufficient, say so.
"""
        return self._generate(prompt)

    def research(self, question: str, emit=None) -> str:
        plan = self._plan(question)
        if emit:
            asyncio.run(emit(ResearchEvent("planning_complete", "Research plan created", {"tasks": len(plan.tasks)}).as_dict()))
        queries = [task.question for task in plan.tasks][:MAX_SEARCHES]
        if not queries:
            raise RuntimeError("ScoutAI could not create a research plan.")

        if emit:
            asyncio.run(emit(ResearchEvent("searching", "Searching the web", {"queries": queries}).as_dict()))
        raw = asyncio.run(self._search_parallel(queries))
        sources = build_sources(raw)[:MAX_SOURCES]
        if emit:
            asyncio.run(emit(ResearchEvent("sources_found", "Sources collected", {"count": len(sources)}).as_dict()))
        if not sources:
            raise RuntimeError("ScoutAI found no web sources.")

        if emit:
            asyncio.run(emit(ResearchEvent("verifying", "Extracting and verifying claims").as_dict()))
        verified = self._verify(sources, question)
        contradictions = self._contradictions(sources)
        if emit:
            asyncio.run(emit(ResearchEvent("contradictions", "Contradiction analysis complete", {"count": len(contradictions)}).as_dict()))

        # Autonomous verification loop: unresolved claims/conflicts trigger
        # targeted searches, followed by another verification pass.
        for _ in range(MAX_VERIFICATION_ROUNDS):
            followups = self._followup_queries(question, verified, contradictions)
            if emit and followups:
                asyncio.run(emit(ResearchEvent("followup_search", "Running targeted follow-up searches", {"queries": followups}).as_dict()))
            if not followups:
                break
            extra_raw = asyncio.run(self._search_parallel(followups))
            existing = {s.url for s in sources if s.url}
            new_raw = [x for x in extra_raw if not x.get("url") or x.get("url") not in existing]
            if not new_raw:
                break
            sources = build_sources([
                {"title": s.title, "url": s.url, "snippet": s.snippet, "source": s.publisher}
                for s in sources
            ] + new_raw)[:MAX_SOURCES]
            verified = self._verify(sources, question)
            contradictions = self._contradictions(sources)

        if emit:
            asyncio.run(emit(ResearchEvent("synthesizing", "Writing evidence-based report").as_dict()))
        result = ResearchResult(
            question=question,
            plan=plan,
            sources=sources,
            verified_claims=verified,
            contradictions=contradictions,
            report=self._synthesize(question, plan, sources, verified, contradictions),
        )
        return result.report

    async def _search_parallel(self, queries: list[str]) -> list[dict]:
        batches = await asyncio.gather(*(self._search_one(q) for q in queries))
        output = []
        seen = set()
        for batch in batches:
            for item in batch:
                url = item.get("url", "")
                if url and url in seen:
                    continue
                if url:
                    seen.add(url)
                output.append(item)
        return output

    async def run(self, question: str, emit=None) -> str:
        if emit is None:
            return await asyncio.to_thread(self.research, question)
        async def wrapped():
            await emit(ResearchEvent("planning", "Planning research tasks").as_dict())
            return await asyncio.to_thread(self.research, question, emit)
        return await wrapped()


research_agent = ScoutAIResearchAgent()


async def run_research(question: str, emit=None) -> str:
    """Run a research mission, optionally streaming progress events."""
    return await research_agent.run(question, emit=emit)
