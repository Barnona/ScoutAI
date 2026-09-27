from app.reports.pdf import build_research_pdf


def test_build_research_pdf():
    report = {
        "question": "Test research question",
        "plan": {
            "objective": "Test objective",
            "tasks": [{"task_id": 1, "question": "Test task", "reason": "Coverage"}],
        },
        "sources": [{
            "source_id": "S1",
            "title": "Test Source",
            "url": "https://example.com",
            "snippet": "Evidence snippet.",
            "publisher": "Example",
            "quality_score": 80,
            "quality_tier": "high",
        }],
        "verified_claims": [{
            "claim": "Test claim",
            "status": "supported",
            "source_ids": ["S1"],
            "reasoning": "Supported by the test source.",
        }],
        "contradictions": [],
        "synthesis": {
            "executive_summary": "Test summary.",
            "key_findings": [{
                "claim": "Test claim",
                "confidence": "high",
                "status": "supported",
                "source_ids": ["S1"],
                "reasoning": "Supported.",
            }],
            "limitations": ["Test limitation."],
            "overall_confidence": "high",
        },
    }

    pdf = build_research_pdf(report, "standard")
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 1000
