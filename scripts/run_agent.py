import asyncio

from app.agents.research_agent import run_research


async def main() -> None:
    question = input("\nWhat should ScoutAI research?\n> ").strip()
    if not question:
        raise SystemExit("Please provide a research question.")

    print("\nScoutAI is researching with Gemma + SerpApi...\n")

    try:
        report = await run_research(question)
    except Exception as exc:
        raise SystemExit(f"ScoutAI failed: {exc}") from exc

    print("\n" + "=" * 72)
    print("SCOUTAI REPORT")
    print("=" * 72)
    print(report)


if __name__ == "__main__":
    asyncio.run(main())
