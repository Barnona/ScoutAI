"""Evidence verification helpers.

The first release keeps verification inside the agent instructions. This
module provides a clean seam for deterministic checks and a dedicated
verification agent in the next iteration.
"""


def normalize_claim(text: str) -> str:
    return " ".join(text.lower().split())
