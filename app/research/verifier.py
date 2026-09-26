"""LLM-assisted claim verification with conservative statuses."""

from app.agents.schemas import SourceRecord


def verification_prompt(claims: list[str], sources: list[SourceRecord]) -> str:
    evidence = "\n\n".join(
        f"[{s.source_id}] {s.title}\n{s.snippet}\n{s.url}" for s in sources
    )
    return f"""Verify each candidate claim against ONLY the supplied sources.
Return ONLY JSON:
{{"claims":[{{"claim":"...","status":"supported|mixed|unsupported",
"source_ids":["S1"],"reasoning":"..."}}]}}
Do not infer missing facts. Use mixed when sources disagree or only partially support a claim.

CANDIDATE CLAIMS:
{claims}

SOURCES:
{evidence}"""


def normalize_claim(text: str) -> str:
    return " ".join(text.lower().split())
