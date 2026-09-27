from config.settings import get_research_profile
from app.research.evidence import build_sources


def test_research_profiles_scale_up():
    quick = get_research_profile("quick")
    standard = get_research_profile("standard")
    deep = get_research_profile("deep")
    investigative = get_research_profile("investigative")

    assert quick["searches"] < standard["searches"] < deep["searches"] < investigative["searches"]
    assert quick["sources"] < standard["sources"] < deep["sources"] < investigative["sources"]
    assert quick["rounds"] < standard["rounds"] < deep["rounds"] < investigative["rounds"]


def test_unknown_profile_falls_back_to_standard():
    assert get_research_profile("does-not-exist") == get_research_profile("standard")


def test_source_quality_metadata_is_present():
    sources = build_sources([
        {
            "title": "Official documentation",
            "url": "https://docs.example.com/guide",
            "snippet": "Primary technical documentation.",
            "source": "Example",
        }
    ])

    assert len(sources) == 1
    assert 0 <= sources[0].quality_score <= 100
    assert sources[0].quality_tier in {"high", "medium", "low"}
    assert sources[0].quality_reasons
