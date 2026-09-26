"""Evidence extraction and source normalization."""

from app.agents.schemas import Evidence, SourceRecord


def build_sources(raw_sources: list[dict]) -> list[SourceRecord]:
    sources = []
    seen = set()
    for i, item in enumerate(raw_sources, 1):
        url = (item.get("url") or "").strip()
        if url and url in seen:
            continue
        if url:
            seen.add(url)
        sources.append(SourceRecord(
            source_id=f"S{i}",
            title=item.get("title", ""),
            url=url,
            snippet=item.get("snippet", ""),
            publisher=item.get("source", ""),
        ))
    return sources


def compact_evidence(sources: list[SourceRecord]) -> str:
    return "\n\n".join(
        f"[{s.source_id}] {s.title}\nURL: {s.url}\n"
        f"Publisher: {s.publisher}\nSnippet: {s.snippet}"
        for s in sources
    )


def extract_claim_lines(text: str) -> list[str]:
    claims = []
    for line in text.splitlines():
        cleaned = line.lstrip("-*• 0123456789.).").strip()
        if len(cleaned) >= 25 and cleaned not in claims:
            claims.append(cleaned)
    return claims
