from app.research.planner import starter_plan


def test_starter_plan():
    plan = starter_plan("What is edge AI?")
    assert plan.objective == "What is edge AI?"
    assert len(plan.tasks) == 1
