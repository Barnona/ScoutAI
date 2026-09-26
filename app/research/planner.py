"""Gemma-driven structured research planner."""

import json

from app.agents.schemas import ResearchPlan, ResearchTask


def parse_plan(text: str, question: str, max_tasks: int = 6) -> ResearchPlan:
    cleaned = text.strip()
    if cleaned.startswith("json"):
        cleaned = cleaned[4:].strip()
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("Planner did not return JSON.")
    data = json.loads(cleaned[start:end + 1])
    tasks = []
    for i, item in enumerate(data.get("tasks", [])[:max_tasks], 1):
        if isinstance(item, dict) and item.get("question"):
            tasks.append(ResearchTask(
                task_id=i,
                question=item["question"].strip(),
                reason=item.get("reason", ""),
            ))
    return ResearchPlan(objective=question, tasks=tasks)
