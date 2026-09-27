"""Evidence extraction, source normalization, and transparent source-quality metadata."""

from urllib.parse import urlparse

from app.agents.schemas import Evidence, SourceRecord

AUTHORITATIVE_DOMAINS = (
    ".gov", ".gov.in", ".edu", ".ac.uk", ".ac.in", ".org",
)
PRIMARY_HINTS = (
    "docs.", "documentation", "developer.", "developers.", "github.com",
    "arxiv.org", "doi.org", "ieee.org", "acm.org", "nature.com",
)


def _quality(url: str, publisher: str) -> tuple[int, str, list[str]]:
    host = (urlparse(url).hostname or "").lower()
    score = 55
    reasons = ["baseline web source"]

    if any(host.endswith(domain) for domain in AUTHORITATIVE_DOMAINS):
        score += 25
        reasons.append("authoritative institutional domain")
    if any(hint in host or hint in url.lower() for hint in PRIMARY_HINTS):
        score += 15
        reasons.append("primary/technical source signal")
    if publisher and publisher.lower() in {"reuters", "associated press", "ap news"}:
        score += 8
        reasons.append("established news publisher")
    if not url:
        score -= 25
        reasons.append("missing URL")

    score = max(0, min(100, score))
    tier = "high" if score >= 80 else "medium" if score >= 60 else "low"
    return score, tier, reasons


def build_sources(raw_sources: list[dict]) -> list[SourceRecord]:
    sources = []
    seen = set()
    for item in raw_sources:
        url = (item.get("url") or "").strip()
        if url and url in seen:
            continue
        if url:
            seen.add(url)

        publisher = item.get("source", "")
        score, tier, reasons = _quality(url, publisher)
        sources.append(SourceRecord(
            source_id=f"S{len(sources) + 1}",
            title=item.get("title", ""),
            url=url,
            snippet=item.get("snippet", ""),
            publisher=publisher,
            quality_score=score,
            quality_tier=tier,
            quality_reasons=reasons,
        ))
    return sources


def compact_evidence(sources: list[SourceRecord]) -> str:
    return "\n\n".join(
        f"[{s.source_id}] {s.title}\nURL: {s.url}\n"
        f"Publisher: {s.publisher}\nQuality: {s.quality_score}/100 ({s.quality_tier})\n"
        f"Snippet: {s.snippet}"
        for s in sources
    )


def extract_claim_lines(text: str) -> list[str]:
    claims = []
    for line in text.splitlines():
        cleaned = line.lstrip("-*• 0123456789.).").strip()
        if len(cleaned) >= 25 and cleaned not in claims:
            claims.append(cleaned)
    return claims
