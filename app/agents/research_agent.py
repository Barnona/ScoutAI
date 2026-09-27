"""ScoutAI multi-stage research agent powered by Gemma + SerpApi."""

import asyncio
import json
import time
from typing import Any

from google import genai

from config.settings import GEMINI_API_KEY, GEMMA_MODEL, GEMMA_FALLBACK_MODEL, get_research_profile
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
        last_error = None
        models = [self.model]
        if GEMMA_FALLBACK_MODEL and GEMMA_FALLBACK_MODEL != self.model:
            models.append(GEMMA_FALLBACK_MODEL)

        for model in models:
            for attempt in range(3):
                try:
                    response = self.client.models.generate_content(
                        model=model,
                        contents=prompt,
                    )
                    text = getattr(response, "text", None)
                    if not text:
                        raise RuntimeError("Gemma returned an empty response.")
                    return text.strip()
                except Exception as exc:
                    last_error = exc
                    if attempt < 2:
                        # 500s can be transient. Back off progressively rather
                        # than immediately issuing another request.
                        time.sleep(2 ** attempt * 2)

        raise RuntimeError(
            f"Gemma request failed for {', '.join(models)} after retries: {last_error}"
        ) from last_error

    @staticmethod
    def _json(text: str) -> dict[str, Any]:
        cleaned = text.strip()
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start < 0 or end <= start:
            raise ValueError("Gemma did not return a JSON object.")
        return json.loads(cleaned[start:end + 1])

    def _plan(self, question: str, max_searches: int) -> ResearchPlan:
        prompt = f"""You are ScoutAI's research planner.

Break the user's broad question into independent research tasks.
Return ONLY valid JSON:
{{"tasks":[{{"question":"...","reason":"..."}}]}}

Rules:
- Generate 2 to {max_searches} tasks.
- Each task must investigate a different aspect.
- Prefer primary, official, academic, technical, or high-quality reporting sources.
- Do not answer the question.

USER QUESTION:
{question}
"""
        return parse_plan(self._generate(prompt), question, max_searches)

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

    def _followup_queries(self, question, verified, contradictions, max_followups: int) -> list[str]:
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
            f"Generate at most {max_followups} targeted queries. "
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
        ][:max_followups]

    def _synthesize(self, question, plan, sources, verified, contradictions) -> dict[str, Any]:
        verification_text = "\n".join(
            f"- {v.status.upper()}: {v.claim} [{', '.join(v.source_ids)}] — {v.reasoning}"
            for v in verified
        )
        conflict_text = "\n".join(
            f"- {c.topic}: {c.claim_a} ({', '.join(c.source_a)}) VS "
            f"{c.claim_b} ({', '.join(c.source_b)}). {c.explanation}"
            for c in contradictions
        ) or "No material contradictions detected."

        prompt = f"""You are ScoutAI's final intelligence synthesizer.

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

Return ONLY valid JSON:
{{
  "executive_summary": "2-4 sentence evidence-based synthesis",
  "key_findings": [
    {{"claim":"...", "confidence":"high|medium|low", "status":"supported|mixed|unsupported", "source_ids":["S1"], "reasoning":"..."}}
  ],
  "limitations": ["..."],
  "overall_confidence": "high|medium|low"
}}

Rules:
- Use only supplied evidence.
- Never invent facts, sources, URLs, or citations.
- Keep source IDs exactly as supplied.
- Confidence means strength of available evidence, not certainty.
- Preserve genuine source disagreements.
- If evidence is insufficient, say so.
"""
        try:
            data = self._json(self._generate(prompt))
        except Exception:
            data = {
                "executive_summary": "Structured synthesis failed; inspect the verified claims and evidence below.",
                "key_findings": [],
                "limitations": ["The final structured synthesis could not be generated."],
                "overall_confidence": "low",
            }
        data.setdefault("executive_summary", "")
        data.setdefault("key_findings", [])
        data.setdefault("limitations", [])
        data.setdefault("overall_confidence", "low")
        return data

    def research(self, question: str, emit=None, depth: str = "standard") -> dict[str, Any]:
        profile = get_research_profile(depth)
        plan = self._plan(question, profile["searches"])
        if emit:
            emit(ResearchEvent("planning_complete", "Research plan created", {"tasks": len(plan.tasks)}).as_dict())
        queries = [task.question for task in plan.tasks][:profile["searches"]]
        if not queries:
            raise RuntimeError("ScoutAI could not create a research plan.")

        if emit:
            emit(ResearchEvent("searching", "Searching the web", {"queries": queries}).as_dict())
        raw = asyncio.run(self._search_parallel(queries))
        sources = build_sources(raw)[:profile["sources"]]
        if emit:
            emit(ResearchEvent("sources_found", "Sources collected", {"count": len(sources)}).as_dict())
        if not sources:
            raise RuntimeError("ScoutAI found no web sources.")

        if emit:
            emit(ResearchEvent("verifying", "Extracting and verifying claims").as_dict())
        verified = self._verify(sources, question)
        contradictions = self._contradictions(sources)
        if emit:
            emit(ResearchEvent("contradictions", "Contradiction analysis complete", {"count": len(contradictions)}).as_dict())

        # Autonomous verification loop: unresolved claims/conflicts trigger
        # targeted searches, followed by another verification pass.
        for round_no in range(profile["rounds"]):
            followups = self._followup_queries(question, verified, contradictions, profile["followups"])
            if emit:
                emit(ResearchEvent("verification_round", f"Verification round {round_no + 1}", {"round": round_no + 1, "gaps": len(followups)}).as_dict())
            if emit and followups:
                emit(ResearchEvent("followup_search", "Running targeted follow-up searches", {"queries": followups}).as_dict())
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
            ] + new_raw)[:profile["sources"]]
            verified = self._verify(sources, question)
            contradictions = self._contradictions(sources)

        if emit:
            emit(ResearchEvent("synthesizing", "Writing evidence-based report").as_dict())
        synthesis = self._synthesize(question, plan, sources, verified, contradictions)
        result = ResearchResult(
            question=question,
            plan=plan,
            sources=sources,
            verified_claims=verified,
            contradictions=contradictions,
            report=synthesis.get("executive_summary", ""),
        )
        return {**result.model_dump(), "synthesis": synthesis}

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

    async def run(self, question: str, emit=None, depth: str = "standard") -> dict[str, Any]:
        if emit:
            emit(ResearchEvent("planning", "Planning research tasks").as_dict())
        return await asyncio.to_thread(self.research, question, emit, depth)


research_agent = ScoutAIResearchAgent()


async def run_research(question: str, emit=None, depth: str = "standard") -> dict[str, Any]:
    """Run a research mission, optionally streaming progress events."""
    return await research_agent.run(question, emit=emit, depth=depth)
