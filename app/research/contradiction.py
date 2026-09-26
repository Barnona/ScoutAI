"""Contradiction detection prompt and data helpers."""

from app.agents.schemas import SourceRecord


def contradiction_prompt(sources: list[SourceRecord]) -> str:
    evidence = "\n\n".join(
        f"[{s.source_id}] {s.title}\n{s.snippet}\n{s.url}" for s in sources
    )
    return f"""Find material contradictions or incompatible factual claims in the sources.
Return ONLY JSON:
{{"contradictions":[{{"topic":"...","claim_a":"...","claim_b":"...",
"source_a":["S1"],"source_b":["S2"],"explanation":"..."}}]}}
Only report genuine disagreements. Different dates, models, definitions, or contexts
are not contradictions unless the sources actually conflict.

SOURCES:
{evidence}"""
