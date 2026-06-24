"""
Server-side PDF generation for ELD Daily Log Sheets.

Renders a multi-page PDF containing:
  1. Trip summary header page
  2. One daily log sheet page per day in the trip
  3. 70-hour / 8-day cycle recap page

Uses ReportLab's Platypus high-level framework for layout, with a custom
``Flowable`` for the 24-hour duty status grid.
"""

from datetime import datetime, timezone
from io import BytesIO
from typing import List

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Flowable,
    KeepTogether,
)
from reportlab.pdfgen import canvas as rl_canvas


# ---------------------------------------------------------------------------
# Styling constants — keep in sync with the frontend's "editorial brutalist"
# palette so the PDF visually matches the on-screen dashboard.
# ---------------------------------------------------------------------------
INK = colors.HexColor("#1A1A1A")
PAPER = colors.HexColor("#F4F1ED")
PARCHMENT = colors.HexColor("#F4F1ED")
SHADE = colors.HexColor("#E8E4DF")
ACCENT = colors.HexColor("#FF6B00")
GRID_FAINT = colors.HexColor("#1A1A1A")
MUTED = colors.HexColor("#1A1A1A")

PAGE_SIZE = landscape(LETTER)  # 11" x 8.5" = 792 x 612 points
MARGIN = 0.4 * inch

STATUS_LABELS = {
    "OFF": "OFF DUTY",
    "SB": "SLEEPER BERTH",
    "D": "DRIVING",
    "ON": "ON DUTY (ND)",
}


# ---------------------------------------------------------------------------
# Custom Flowable: 24-hour duty status grid
# ---------------------------------------------------------------------------
class EldGridFlowable(Flowable):
    """Vector-drawn 24-hour ELD grid mirroring the on-screen SVG."""

    def __init__(self, timeline: List[dict], totals: dict, width: float = 10.2 * inch, height: float = 2.0 * inch):
        super().__init__()
        self.timeline = timeline
        self.totals = totals
        self.width = width
        self.height = height

    def wrap(self, _avail_w, _avail_h):
        return self.width, self.height

    def draw(self):
        c = self.canv
        w, h = self.width, self.height

        left_pad = 1.25 * inch
        right_pad = 0.7 * inch
        top_pad = 0.30 * inch
        bottom_pad = 0.10 * inch
        grid_w = w - left_pad - right_pad
        grid_h = h - top_pad - bottom_pad
        row_h = grid_h / 4.0

        def x_of(hour: float) -> float:
            return left_pad + (hour / 24.0) * grid_w

        def y_of(status: str) -> float:
            offsets = {"OFF": 0.5, "SB": 1.5, "D": 2.5, "ON": 3.5}
            return h - top_pad - row_h * offsets[status]

        # ----- Hour axis (top) -----
        c.setFont("Helvetica-Bold", 7)
        c.setFillColor(INK)
        for i in range(25):
            hour = 0 if i == 24 else i
            # Skip the closing "M" label at position 24 — it would collide with the totals column
            if i == 24:
                # Still draw the rightmost grid border line at this x
                c.setStrokeColor(INK)
                c.setLineWidth(1.2)
                c.line(x_of(i), h - top_pad, x_of(i), bottom_pad)
                continue
            display = "M" if hour == 0 else ("N" if hour == 12 else str(hour))
            x = x_of(i)
            is_major = hour in (0, 12)
            c.setFont("Helvetica-Bold" if is_major else "Helvetica", 7)
            c.drawCentredString(x, h - top_pad + 6, display)

            # Vertical hour line (top of grid)
            c.setStrokeColor(INK)
            c.setLineWidth(0.9 if is_major else 0.4)
            c.setLineCap(1)
            c.line(x, h - top_pad, x, bottom_pad)

            # Quarter-hour ticks within the column
            for frac, dash in [(0.25, None), (0.50, [2, 2]), (0.75, None)]:
                qx = x_of(i + frac)
                c.setLineWidth(0.25)
                c.setStrokeColor(colors.Color(0.1, 0.1, 0.1, alpha=0.35))
                if dash:
                    c.setDash(*dash)
                else:
                    c.setDash()
                c.line(qx, h - top_pad, qx, bottom_pad + 4)
            c.setDash()

        # ----- Row dividers -----
        c.setStrokeColor(INK)
        c.setDash()
        # Heavy top border
        c.setLineWidth(1.2)
        c.line(left_pad, h - top_pad, w - right_pad, h - top_pad)
        # Heavy bottom border
        c.line(left_pad, bottom_pad, w - right_pad, bottom_pad)
        # Faint inner dividers
        c.setLineWidth(0.3)
        c.setStrokeColor(colors.Color(0.1, 0.1, 0.1, alpha=0.3))
        for r in (1, 2, 3):
            y = h - top_pad - row_h * r
            c.line(left_pad, y, w - right_pad, y)

        # ----- Row labels (left) -----
        c.setFillColor(INK)
        for status in ("OFF", "SB", "D", "ON"):
            y = y_of(status)
            c.setFont("Helvetica-Bold", 7)
            c.drawString(0.05 * inch, y - 2, STATUS_LABELS[status])

        # ----- Dynamic ELD duty line path -----
        c.setStrokeColor(INK)
        c.setLineWidth(2.6)
        c.setLineCap(1)
        sorted_blocks = sorted(self.timeline, key=lambda b: b["start_hour"])
        for idx, block in enumerate(sorted_blocks):
            x1 = x_of(block["start_hour"])
            x2 = x_of(block["end_hour"])
            y = y_of(block["status"])
            c.line(x1, y, x2, y)
            if idx + 1 < len(sorted_blocks):
                next_y = y_of(sorted_blocks[idx + 1]["status"])
                c.line(x2, y, x2, next_y)

        # ----- Totals column (right) -----
        c.setStrokeColor(INK)
        c.setLineWidth(1.2)
        c.line(w - right_pad, h - top_pad, w - right_pad, bottom_pad)
        c.setLineWidth(0.4)
        c.line(w - right_pad + 0.32 * inch, h - top_pad, w - right_pad + 0.32 * inch, bottom_pad)
        c.setFillColor(INK)
        c.setFont("Helvetica-Bold", 7)
        c.drawCentredString(w - right_pad + 0.16 * inch, h - top_pad + 6, "TOTAL")
        for status in ("OFF", "SB", "D", "ON"):
            y = y_of(status)
            c.setFont("Helvetica-Bold", 9)
            c.drawCentredString(w - right_pad + 0.16 * inch, y - 3, f"{self.totals[status]:.2f}")
        # 24h certification footer
        c.setFillColor(ACCENT)
        c.setFont("Helvetica-Bold", 7)
        c.drawCentredString(w - right_pad + 0.16 * inch, 0, "24.00 hr")


# ---------------------------------------------------------------------------
# Page furniture: title bar, metadata strip, footer with sheet numbering
# ---------------------------------------------------------------------------
class EldDocTemplate(BaseDocTemplate):
    """Single-frame landscape doc with a header/footer drawn directly on the canvas."""

    def __init__(self, filename: str, total_sheets: int, **kwargs):
        super().__init__(filename, pagesize=PAGE_SIZE, **kwargs)
        self.total_sheets = total_sheets
        frame = Frame(
            MARGIN,
            MARGIN + 0.35 * inch,  # leave space for footer
            PAGE_SIZE[0] - 2 * MARGIN,
            PAGE_SIZE[1] - 2 * MARGIN - 0.35 * inch,  # leave space for header
            id="eld-frame",
            leftPadding=0,
            bottomPadding=0,
            rightPadding=0,
            topPadding=0,
        )
        self.addPageTemplates(PageTemplate(id="eld", frames=[frame]))

    def afterPage(self):
        c = self.canv
        w, h = PAGE_SIZE
        # Header bar
        c.setFillColor(INK)
        c.rect(0, h - 0.30 * inch, w, 0.30 * inch, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(MARGIN, h - 0.20 * inch, "ELD DAILY LOG BOOK")
        c.setFont("Helvetica", 8)
        c.drawRightString(w - MARGIN, h - 0.20 * inch, "FMCSA § 395 — Driver's Record of Duty Status")

        # Footer bar
        c.setFillColor(INK)
        c.rect(0, 0, w, 0.30 * inch, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 8)
        sheet_no = self.page
        c.drawString(
            MARGIN,
            0.10 * inch,
            f"Sheet {sheet_no} of {self.total_sheets}",
        )
        c.setFont("Helvetica", 8)
        c.drawCentredString(w / 2.0, 0.10 * inch, "Generated by E-DOT Dispatch Terminal")
        c.drawRightString(
            w - MARGIN,
            0.10 * inch,
            datetime.now(timezone.utc).strftime("Generated %Y-%m-%d %H:%M UTC"),
        )


# ---------------------------------------------------------------------------
# Page builders
# ---------------------------------------------------------------------------
def _build_styles():
    base = getSampleStyleSheet()
    title = ParagraphStyle(
        "TitleBig",
        parent=base["Title"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=INK,
        alignment=TA_LEFT,
        spaceAfter=4,
    )
    subtitle = ParagraphStyle(
        "Sub",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#1A1A1A"),
        spaceAfter=10,
    )
    section = ParagraphStyle(
        "Section",
        parent=base["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=13,
        textColor=INK,
        spaceBefore=4,
        spaceAfter=4,
    )
    body = ParagraphStyle(
        "Body",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=INK,
    )
    small = ParagraphStyle(
        "Small",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=10,
        textColor=INK,
    )
    header_white = ParagraphStyle(
        "HeaderWhite",
        parent=base["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.white,
    )
    return {
        "title": title,
        "subtitle": subtitle,
        "section": section,
        "body": body,
        "small": small,
        "header_white": header_white,
    }


def _summary_table(styles, summary: dict) -> Table:
    rows = [
        [Paragraph("<b>FROM</b>", styles["small"]), Paragraph(summary.get("from_label", "—"), styles["body"]),
         Paragraph("<b>TOTAL MILES</b>", styles["small"]), Paragraph(f"{int(summary.get('total_distance_miles', 0))} mi", styles["body"])],
        [Paragraph("<b>PICKUP</b>", styles["small"]), Paragraph(summary.get("pickup_label", "—"), styles["body"]),
         Paragraph("<b>TOTAL DURATION</b>", styles["small"]), Paragraph(f"{summary.get('total_duration_hours', 0):.2f} hrs", styles["body"])],
        [Paragraph("<b>DROPOFF</b>", styles["small"]), Paragraph(summary.get("dropoff_label", "—"), styles["body"]),
         Paragraph("<b>CYCLE HRS USED (ENTRY)</b>", styles["small"]), Paragraph(f"{summary.get('current_cycle_used_hrs', 0):.2f} hrs", styles["body"])],
        [Paragraph("<b>CARRIER</b>", styles["small"]), Paragraph(summary.get("carrier_name", "—"), styles["body"]),
         Paragraph("<b>TRIP DAYS</b>", styles["small"]), Paragraph(str(summary.get("trip_days", 1)), styles["body"])],
        [Paragraph("<b>TRACTOR #</b>", styles["small"]), Paragraph(summary.get("tractor_number", "—"), styles["body"]),
         Paragraph("<b>TRAILER #</b>", styles["small"]), Paragraph(summary.get("trailer_number", "—"), styles["body"])],
    ]
    t = Table(rows, colWidths=[1.3 * inch, 3.4 * inch, 1.7 * inch, 3.4 * inch])
    t.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1.0, INK),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.Color(0.1, 0.1, 0.1, alpha=0.3)),
        ("BACKGROUND", (0, 0), (0, -1), SHADE),
        ("BACKGROUND", (2, 0), (2, -1), SHADE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return t


def _metadata_strip(styles, log: dict) -> Table:
    rows = [[
        Paragraph(f"<b>DATE ON GRID</b><br/>{log.get('date_label', '—')}", styles["body"]),
        Paragraph(f"<b>CARRIER</b><br/>{log.get('carrier_name', '—')}", styles["body"]),
        Paragraph(f"<b>EQUIPMENT IDs</b><br/>TRAC: {log.get('tractor_number', '—')} &nbsp;/&nbsp; TRAIL: {log.get('trailer_number', '—')}", styles["body"]),
        Paragraph(f"<b>MILES DRIVEN TODAY</b><br/><font color='#FF6B00'><b>{log.get('total_miles_driven', 0)} mi</b></font>", styles["body"]),
    ]]
    t = Table(rows, colWidths=[2.4 * inch, 3.0 * inch, 3.0 * inch, 1.6 * inch])
    t.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1.0, INK),
        ("BACKGROUND", (0, 0), (-1, -1), SHADE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


def _remarks_table(styles, remarks: List[dict]) -> Table:
    header = [
        Paragraph("<b>TIME</b>", styles["header_white"]),
        Paragraph("<b>STATUS</b>", styles["header_white"]),
        Paragraph("<b>LOCATION</b>", styles["header_white"]),
        Paragraph("<b>REMARKS</b>", styles["header_white"]),
    ]
    body = [header]
    for r in remarks or []:
        body.append([
            Paragraph(r.get("time_label", "—"), styles["body"]),
            Paragraph(f"<b>{STATUS_LABELS.get(r.get('status', ''), r.get('status', ''))}</b>", styles["body"]),
            Paragraph(r.get("location", "—"), styles["body"]),
            Paragraph(f"<i>{r.get('remarks_text', '')}</i>", styles["body"]),
        ])
    if len(body) == 1:
        body.append([Paragraph("No status changes recorded.", styles["body"]), "", "", ""])

    t = Table(body, colWidths=[0.9 * inch, 1.6 * inch, 2.7 * inch, 4.6 * inch], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), INK),
        ("BOX", (0, 0), (-1, -1), 1.0, INK),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.Color(0.1, 0.1, 0.1, alpha=0.25)),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PARCHMENT]),
    ]))
    return t


def _recap_table(styles, daily_logs: List[dict], cycle_hours_used_entry: float) -> Table:
    header = [
        Paragraph("<b>DATE</b>", styles["header_white"]),
        Paragraph("<b>OFF</b>", styles["header_white"]),
        Paragraph("<b>SB</b>", styles["header_white"]),
        Paragraph("<b>DRIVING</b>", styles["header_white"]),
        Paragraph("<b>ON DUTY</b>", styles["header_white"]),
        Paragraph("<b>MILES</b>", styles["header_white"]),
        Paragraph("<b>CUM. CYCLE HRS</b>", styles["header_white"]),
    ]
    rows = [header]
    running = cycle_hours_used_entry
    cumulative_off = 0.0
    cumulative_sb = 0.0
    cumulative_d = 0.0
    cumulative_on = 0.0
    cumulative_miles = 0

    for log in daily_logs:
        t = log.get("totals", {})
        cumulative_off += t.get("OFF", 0)
        cumulative_sb += t.get("SB", 0)
        cumulative_d += t.get("D", 0)
        cumulative_on += t.get("ON", 0)
        cumulative_miles += int(log.get("total_miles_driven", 0))
        # Cycle used: ON + D, plus previous days' carry
        driving_today = t.get("D", 0) + t.get("ON", 0)
        running += driving_today

        rows.append([
            Paragraph(log.get("date_label", "—"), styles["body"]),
            Paragraph(f"{t.get('OFF', 0):.2f}", styles["body"]),
            Paragraph(f"{t.get('SB', 0):.2f}", styles["body"]),
            Paragraph(f"{t.get('D', 0):.2f}", styles["body"]),
            Paragraph(f"{t.get('ON', 0):.2f}", styles["body"]),
            Paragraph(str(int(log.get("total_miles_driven", 0))), styles["body"]),
            Paragraph(f"{running:.2f}", styles["body"]),
        ])

    # Totals row
    rows.append([
        Paragraph("<b>TOTAL</b>", styles["body"]),
        Paragraph(f"<b>{cumulative_off:.2f}</b>", styles["body"]),
        Paragraph(f"<b>{cumulative_sb:.2f}</b>", styles["body"]),
        Paragraph(f"<b>{cumulative_d:.2f}</b>", styles["body"]),
        Paragraph(f"<b>{cumulative_on:.2f}</b>", styles["body"]),
        Paragraph(f"<b>{cumulative_miles}</b>", styles["body"]),
        Paragraph(f"<b>{running:.2f}</b>", styles["body"]),
    ])

    t = Table(rows, colWidths=[2.5 * inch, 0.8 * inch, 0.8 * inch, 1.0 * inch, 1.0 * inch, 0.9 * inch, 1.4 * inch], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), INK),
        ("BACKGROUND", (0, -1), (-1, -1), SHADE),
        ("BOX", (0, 0), (-1, -1), 1.0, INK),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.Color(0.1, 0.1, 0.1, alpha=0.25)),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, PARCHMENT]),
    ]))
    return t


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def build_eld_pdf(payload: dict) -> bytes:
    """
    Build a multi-page PDF document for an ELD trip.

    ``payload`` is the JSON request body sent to the export endpoint. Expected keys:
        - summary: dict with from/pickup/dropoff labels, totals, carrier metadata
        - daily_logs: list of daily-log dicts in the same shape the
          ``/api/trips/generate/`` endpoint returns.

    Returns the rendered PDF as ``bytes``.
    """
    summary = payload.get("summary", {}) or {}
    daily_logs = payload.get("daily_logs", []) or []

    if not daily_logs:
        raise ValueError("No daily logs provided for PDF export.")

    styles = _build_styles()
    total_sheets = 1 + len(daily_logs) + 1  # summary + N days + recap

    buffer = BytesIO()
    doc = EldDocTemplate(buffer, total_sheets=total_sheets)
    story = []

    # ---------------------------------------------------------------------
    # Page 1: Trip Summary
    # ---------------------------------------------------------------------
    story.append(Paragraph("ELD Daily Log Book — Trip Summary", styles["title"]))
    story.append(Paragraph(
        "This document compiles every daily Record of Duty Status produced for the "
        "trip below, in compliance with 49 CFR Part 395.",
        styles["subtitle"],
    ))
    story.append(Paragraph("Trip Overview", styles["section"]))
    story.append(_summary_table(styles, summary))
    story.append(Spacer(1, 0.18 * inch))
    story.append(Paragraph(
        f"<b>Driver's Certification:</b> I certify that the entries on these daily log "
        f"sheets are true and correct, and that I have complied with the applicable "
        f"Hours of Service regulations for each day recorded.",
        styles["body"],
    ))
    story.append(PageBreak())

    # ---------------------------------------------------------------------
    # Pages 2..N+1: One daily log sheet per day
    # ---------------------------------------------------------------------
    for idx, log in enumerate(daily_logs):
        blocks = []
        blocks.append(Paragraph(f"Daily Log Sheet — {log.get('date_label', '')}", styles["title"]))
        blocks.append(_metadata_strip(styles, log))
        blocks.append(Spacer(1, 0.12 * inch))
        blocks.append(EldGridFlowable(
            timeline=log.get("timeline", []),
            totals=log.get("totals", {}),
            width=PAGE_SIZE[0] - 2 * MARGIN,
            height=2.2 * inch,
        ))
        blocks.append(Spacer(1, 0.15 * inch))
        blocks.append(Paragraph("Duty Status Remarks / Geographic Change Log", styles["section"]))
        blocks.append(_remarks_table(styles, log.get("remarks", [])))
        story.append(KeepTogether(blocks))
        if idx < len(daily_logs) - 1:
            story.append(PageBreak())

    story.append(PageBreak())

    # ---------------------------------------------------------------------
    # Final page: 70hr / 8-day cycle recap
    # ---------------------------------------------------------------------
    story.append(Paragraph("70-Hour / 8-Day Cycle Recap", styles["title"]))
    story.append(Paragraph(
        "Cumulative duty totals across all days of this trip. The 70-hour clock tracks "
        "Driving + On-Duty time over a rolling 8-day window.",
        styles["subtitle"],
    ))
    cycle_entry = float(summary.get("current_cycle_used_hrs", 0) or 0)
    story.append(Paragraph(
        f"<b>Cycle hours on file before trip start:</b> {cycle_entry:.2f} hrs",
        styles["body"],
    ))
    story.append(Spacer(1, 0.10 * inch))
    story.append(_recap_table(styles, daily_logs, cycle_entry))
    story.append(Spacer(1, 0.20 * inch))
    story.append(Paragraph(
        f"<i>Total trip driving time: {sum(log.get('totals', {}).get('D', 0) for log in daily_logs):.2f} hrs. "
        f"Total trip miles: {sum(int(log.get('total_miles_driven', 0)) for log in daily_logs)} mi.</i>",
        styles["body"],
    ))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
