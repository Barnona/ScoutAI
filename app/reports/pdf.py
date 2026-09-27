"""PDF report generation for completed ScoutAI research missions."""

from io import BytesIO
from xml.sax.saxutils import escape
import re

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def _text(value) -> str:
    text = str(value or "")
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", " ", text)
    text = text.encode("latin-1", errors="replace").decode("latin-1")
    return escape(text)


def _bullet(text: str) -> Paragraph:
    return Paragraph(f"- {_text(text)}", _STYLES["body"])


def _page_number(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#66757d"))
    canvas.drawString(18 * mm, 12 * mm, "SCOUTAI // EVIDENCE BEFORE CONFIDENCE")
    canvas.drawRightString(192 * mm, 12 * mm, f"PAGE {doc.page}")
    canvas.restoreState()


_styles = getSampleStyleSheet()
_STYLES = {
    "title": ParagraphStyle(
        "ScoutTitle", parent=_styles["Title"], fontName="Helvetica-Bold",
        fontSize=24, leading=28, textColor=colors.HexColor("#172126"),
        spaceAfter=6,
    ),
    "subtitle": ParagraphStyle(
        "ScoutSubtitle", parent=_styles["Normal"], fontName="Helvetica",
        fontSize=9, leading=13, textColor=colors.HexColor("#60727a"),
        spaceAfter=16,
    ),
    "h1": ParagraphStyle(
        "ScoutH1", parent=_styles["Heading1"], fontName="Helvetica-Bold",
        fontSize=15, leading=19, textColor=colors.HexColor("#172126"),
        spaceBefore=13, spaceAfter=8,
    ),
    "h2": ParagraphStyle(
        "ScoutH2", parent=_styles["Heading2"], fontName="Helvetica-Bold",
        fontSize=11, leading=14, textColor=colors.HexColor("#008f7a"),
        spaceBefore=9, spaceAfter=5,
    ),
    "body": ParagraphStyle(
        "ScoutBody", parent=_styles["BodyText"], fontName="Helvetica",
        fontSize=9.5, leading=14, textColor=colors.HexColor("#33454d"),
        spaceAfter=7,
    ),
    "small": ParagraphStyle(
        "ScoutSmall", parent=_styles["BodyText"], fontName="Helvetica",
        fontSize=7.5, leading=10, textColor=colors.HexColor("#60727a"),
        spaceAfter=3,
    ),
    "claim": ParagraphStyle(
        "ScoutClaim", parent=_styles["BodyText"], fontName="Helvetica-Bold",
        fontSize=10, leading=14, textColor=colors.HexColor("#172126"),
        spaceAfter=5,
    ),
    "mono": ParagraphStyle(
        "ScoutMono", parent=_styles["BodyText"], fontName="Courier",
        fontSize=7.5, leading=10, textColor=colors.HexColor("#40545c"),
        wordWrap="CJK",
    ),
    "center": ParagraphStyle(
        "ScoutCenter", parent=_styles["BodyText"], fontName="Helvetica-Bold",
        fontSize=9, leading=12, alignment=TA_CENTER,
        textColor=colors.HexColor("#008f7a"),
    ),
}


def build_research_pdf(report: dict, depth: str = "standard") -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=17 * mm,
        bottomMargin=18 * mm,
        title="ScoutAI Research Report",
        author="ScoutAI",
    )

    question = report.get("question", "Research Mission")
    plan = report.get("plan") or {}
    sources = report.get("sources") or []
    verified = report.get("verified_claims") or []
    contradictions = report.get("contradictions") or []
    synthesis = report.get("synthesis") or {}
    findings = synthesis.get("key_findings") or []
    limitations = synthesis.get("limitations") or []
    overall_confidence = synthesis.get("overall_confidence", "low")

    story = [
        Paragraph("SCOUTAI", _STYLES["title"]),
        Paragraph("AUTONOMOUS RESEARCH & INTELLIGENCE AGENT", _STYLES["subtitle"]),
        Paragraph("INTELLIGENCE RESEARCH REPORT", _STYLES["h1"]),
        Paragraph(_text(question), _STYLES["claim"]),
    ]

    metadata = [
        ["RESEARCH DEPTH", str(depth).upper()],
        ["SOURCES ANALYSED", str(len(sources))],
        ["VERIFIED CLAIMS", str(len(verified))],
        ["CONTRADICTIONS", str(len(contradictions))],
        ["OVERALL CONFIDENCE", str(overall_confidence).upper()],
    ]
    table = Table(metadata, colWidths=[48 * mm, 42 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f3f7f8")),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#c8d5da")),
        ("INNERGRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#d7e1e4")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, -1), "Courier-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#60727a")),
        ("TEXTCOLOR", (1, 0), (1, -1), colors.HexColor("#008f7a")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story += [table, Spacer(1, 8)]

    story += [
        Paragraph("01 / EXECUTIVE SUMMARY", _STYLES["h1"]),
        Paragraph(_text(synthesis.get("executive_summary") or report.get("report") or "No summary available."), _STYLES["body"]),
        Paragraph("02 / RESEARCH PLAN", _STYLES["h1"]),
        Paragraph(_text(plan.get("objective", "Research objective not supplied.")), _STYLES["body"]),
    ]

    for task in plan.get("tasks", []):
        task_id = task.get("task_id", "")
        story.append(Paragraph(
            f"<b>Task {escape(str(task_id))}:</b> {_text(task.get('question'))}"
            f"<br/><font color='#60727a'>{_text(task.get('reason'))}</font>",
            _STYLES["body"],
        ))

    story.append(Paragraph("03 / KEY FINDINGS", _STYLES["h1"]))
    if findings:
        for i, finding in enumerate(findings, 1):
            status = str(finding.get("status", "unknown")).upper()
            confidence = str(finding.get("confidence", "low")).upper()
            sources_text = ", ".join(str(x) for x in finding.get("source_ids", [])) or "No source IDs"
            story.append(KeepTogether([
                Paragraph(f"{i}. {_text(finding.get('claim'))}", _STYLES["claim"]),
                Paragraph(
                    f"STATUS: {escape(status)} | CONFIDENCE: {escape(confidence)} | SOURCES: {escape(sources_text)}",
                    _STYLES["small"],
                ),
                Paragraph(_text(finding.get("reasoning", "")), _STYLES["body"]),
            ]))
    else:
        story.append(Paragraph("No structured key findings were generated.", _STYLES["body"]))

    story.append(Paragraph("04 / VERIFICATION RECORD", _STYLES["h1"]))
    if verified:
        for claim in verified:
            source_ids = ", ".join(str(x) for x in claim.get("source_ids", [])) or "None"
            story.append(KeepTogether([
                Paragraph(_text(claim.get("claim")), _STYLES["claim"]),
                Paragraph(
                    f"STATUS: {escape(str(claim.get('status', 'unverified')).upper())} | SOURCES: {escape(source_ids)}",
                    _STYLES["small"],
                ),
                Paragraph(_text(claim.get("reasoning", "")), _STYLES["body"]),
            ]))
    else:
        story.append(Paragraph("No separate verification records were returned.", _STYLES["body"]))

    story.append(PageBreak())
    story.append(Paragraph("05 / CONTRADICTION MATRIX", _STYLES["h1"]))
    if contradictions:
        for i, conflict in enumerate(contradictions, 1):
            a_sources = ", ".join(str(x) for x in conflict.get("source_a", [])) or "None"
            b_sources = ", ".join(str(x) for x in conflict.get("source_b", [])) or "None"
            conflict_table = Table([
                [Paragraph("<b>SOURCE POSITION A</b>", _STYLES["small"]),
                 Paragraph("<b>SOURCE POSITION B</b>", _STYLES["small"])],
                [Paragraph(_text(conflict.get("claim_a")), _STYLES["body"]),
                 Paragraph(_text(conflict.get("claim_b")), _STYLES["body"])],
                [Paragraph(_text(a_sources), _STYLES["small"]),
                 Paragraph(_text(b_sources), _STYLES["small"])],
            ], colWidths=[82 * mm, 82 * mm])
            conflict_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#fff4df")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#d8c7a6")),
                ("INNERGRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#e1d7c4")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]))
            story += [
                Paragraph(f"{i}. {_text(conflict.get('topic', 'Conflict'))}", _STYLES["h2"]),
                conflict_table,
                Paragraph(f"<b>Analysis:</b> {_text(conflict.get('explanation', ''))}", _STYLES["body"]),
            ]
    else:
        story.append(Paragraph("No material contradictions were detected.", _STYLES["body"]))

    story.append(Paragraph("06 / LIMITATIONS", _STYLES["h1"]))
    if limitations:
        for item in limitations:
            story.append(_bullet(item))
    else:
        story.append(Paragraph("No explicit limitations were supplied by the synthesis.", _STYLES["body"]))

    story.append(Paragraph("07 / EVIDENCE SOURCES", _STYLES["h1"]))
    for source in sources:
        source_id = source.get("source_id", "")
        title = source.get("title") or "Untitled source"
        publisher = source.get("publisher") or "Web source"
        score = source.get("quality_score", 0)
        tier = source.get("quality_tier", "unknown")
        url = source.get("url") or ""
        url_markup = (
            f'<link href="{escape(url)}" color="#008f7a">{_text(url)}</link>'
            if url else "URL unavailable"
        )
        story.append(KeepTogether([
            Paragraph(
                f"<b>{_text(source_id)} - {_text(title)}</b>",
                _STYLES["claim"],
            ),
            Paragraph(
                f"PUBLISHER: {_text(publisher)} | QUALITY: {escape(str(tier).upper())} | SCORE: {escape(str(score))}/100",
                _STYLES["small"],
            ),
            Paragraph(_text(source.get("snippet", "")), _STYLES["body"]),
            Paragraph(url_markup, _STYLES["mono"]),
            Spacer(1, 5),
        ]))

    story.append(Spacer(1, 10))
    story.append(Paragraph("ScoutAI: Plan -> Search -> Verify -> Challenge -> Synthesize", _STYLES["center"]))

    doc.build(story, onFirstPage=_page_number, onLaterPages=_page_number)
    return buffer.getvalue()
