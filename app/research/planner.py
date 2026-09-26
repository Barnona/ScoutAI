"""Planning scaffolding for the explicit multi-step research pipeline.

The v0.1 agent can plan implicitly through its tool loop. This module is
ready for the v0.2 structured planner that will emit ResearchPlan objects.
"""

from app.agents.schemas import ResearchPlan, ResearchTask


def starter_plan(question: str) -> ResearchPlan:
    return ResearchPlan(
        objective=question,
        tasks=[
            ResearchTask(
                task_id=1,
                question=question,
                reason="Initial research task for the MVP.",
            )
        ],
    )
