from pydantic import BaseModel


class Contradiction(BaseModel):
    claim_a: str
    claim_b: str
    source_a: str = ""
    source_b: str = ""
    explanation: str = ""


def detect_obvious_numeric_conflicts(claims: list[str]) -> list[tuple[str, str]]:
    """Placeholder for deterministic contradiction checks.

    Semantic contradiction detection belongs in the v0.2 verifier. Keeping
    this function small makes that upgrade easy without changing the API.
    """
    conflicts: list[tuple[str, str]] = []
    for i, a in enumerate(claims):
        for b in claims[i + 1 :]:
            if a.strip() and b.strip() and a.strip().lower() == b.strip().lower():
                continue
    return conflicts
