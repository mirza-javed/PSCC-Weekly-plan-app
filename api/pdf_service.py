import os
import re
from fpdf import FPDF
from .config import FONT_URDU, FONT_SINDHI, DAY_ORDER, PERIODS_PER_DAY

SINDHI_ONLY_CHARS = set("ٻڀٺٽٿڃڄڇڏڊڍڦڱڳڙڪڻڌ")
ARABIC_SCRIPT_RANGE = re.compile(r"[\u0600-\u06FF]")

COLUMN_WIDTHS = {
    "Day": 24,
    "Period": 14,
    "Class": 16,
    "Class_Section": 20,
    "Subject": 30,
    "Teacher": 24
}
ROW_HEIGHT = 7
HEADER_HEIGHT = 8

ONE_INCH = 25.4  # mm
TOP_MARGIN_075IN = 19.05  # mm

def detect_font_for(text: str, subject: str = "") -> str:
    if not isinstance(text, str) or not text.strip():
        return "latin"
    if any(ch in SINDHI_ONLY_CHARS for ch in text):
        return "sindhi"
    if not ARABIC_SCRIPT_RANGE.search(text):
        return "latin"
    subject = (subject or "").strip().lower()
    if subject == "sindhi":
        return "sindhi"
    if subject == "urdu":
        return "urdu"
    return "urdu"

def safe_latin(text: str) -> str:
    if not isinstance(text, str):
        return str(text)
    try:
        text.encode("latin-1")
        return text
    except UnicodeEncodeError:
        return text.encode("latin-1", errors="replace").decode("latin-1")

def make_pdf(rows, columns, title, subtitle=""):
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.set_margins(10, 10, 10)
    pdf.add_page()
    if os.path.exists(FONT_URDU):
        pdf.add_font("Urdu", "", FONT_URDU)
    if os.path.exists(FONT_SINDHI):
        pdf.add_font("Sindhi", "", FONT_SINDHI)
    pdf.set_text_shaping(True)

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Pakistan Steel Cadet College", align="C", ln=True)
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 9, title, align="C", ln=True)
    if subtitle:
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 8, subtitle, ln=True)
    pdf.ln(2)
    top_y = pdf.get_y()

    page_width = 297 - 20
    gap = 8
    block_width = (page_width - gap) / 2

    fixed_cols = [c for c in columns if c != "Topic"]
    fixed_total = sum(COLUMN_WIDTHS.get(c, 22) for c in fixed_cols)

    usable_height = 210 - top_y - 15
    max_rows_per_block = max(1, int((usable_height - HEADER_HEIGHT) / ROW_HEIGHT))

    n = len(rows)
    if n <= max_rows_per_block:
        blocks = [(rows, 10, page_width)]
    else:
        half = -(-n // 2)
        blocks = [(rows[:half], 10, block_width),
                  (rows[half:], 10 + block_width + gap, block_width)]

    for block_rows, x0, width in blocks:
        topic_width = width - fixed_total if "Topic" in columns else 0
        col_widths = {c: COLUMN_WIDTHS.get(c, 22) for c in fixed_cols}
        if "Topic" in columns:
            col_widths["Topic"] = max(topic_width, 20)

        y = top_y
        pdf.set_xy(x0, y)
        pdf.set_font("Helvetica", "B", 9)
        for col in columns:
            pdf.cell(col_widths[col], HEADER_HEIGHT, col, border=1)
        pdf.ln(HEADER_HEIGHT)
        pdf.set_x(x0)

        for row in block_rows:
            subject = str(row.get("Subject", ""))
            for col in columns:
                w = col_widths[col]
                text = str(row.get(col, ""))
                script = detect_font_for(text, subject)
                if script == "urdu" and os.path.exists(FONT_URDU):
                    pdf.set_font("Urdu", "", 10)
                elif script == "sindhi" and os.path.exists(FONT_SINDHI):
                    pdf.set_font("Sindhi", "", 10)
                else:
                    pdf.set_font("Helvetica", "", 8)
                    text = safe_latin(text)
                max_chars = max(3, int(w / 1.7))
                pdf.cell(w, ROW_HEIGHT, text[:max_chars], border=1)
            pdf.ln(ROW_HEIGHT)
            pdf.set_x(x0)

    return bytes(pdf.output())

def _new_grid_page():
    pdf = FPDF(orientation="L", unit="mm", format="Legal")
    pdf.set_margins(ONE_INCH, TOP_MARGIN_075IN, ONE_INCH)
    pdf.add_page()
    if os.path.exists(FONT_URDU):
        pdf.add_font("Urdu", "", FONT_URDU)
    if os.path.exists(FONT_SINDHI):
        pdf.add_font("Sindhi", "", FONT_SINDHI)
    pdf.set_text_shaping(True)
    return pdf, pdf.w - 2 * ONE_INCH

def _render_day_period_grid(pdf, top_y, page_w, cell_lookup, urdu_font_size=9, sindhi_font_size=9):
    left = ONE_INCH
    day_col_w = 24
    period_col_w = (page_w - day_col_w) / 7
    header_h = 8
    row_h = 24

    pdf.set_xy(left, top_y)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(day_col_w, header_h, "Days", border=1, align="C")
    for p in range(1, 8):
        pdf.cell(period_col_w, header_h, f"Period_{p:02d}", border=1, align="C")
    pdf.ln(header_h)

    y = top_y + header_h
    for day in DAY_ORDER:
        pdf.set_xy(left, y)
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(day_col_w, row_h, day, border=1, align="C")

        n_periods = PERIODS_PER_DAY.get(day, 7)
        x = left + day_col_w
        for p in range(1, 8):
            pdf.rect(x, y, period_col_w, row_h)
            if p > n_periods:
                pdf.set_xy(x, y + row_h / 2 - 3)
                pdf.set_font("Helvetica", "", 9)
                pdf.cell(period_col_w, 6, "-----------", align="C")
            else:
                cell = cell_lookup(day, p) or {}
                line1 = str(cell.get("line1", ""))
                line2 = str(cell.get("line2", ""))
                subject = str(cell.get("subject", ""))

                pdf.set_xy(x + 1, y + 1)
                pdf.set_font("Helvetica", "B", 8)
                pdf.multi_cell(period_col_w - 2, 4, safe_latin(line1)[:40], align="C")

                script = detect_font_for(line2, subject)
                if script == "urdu" and os.path.exists(FONT_URDU):
                    pdf.set_font("Urdu", "", urdu_font_size)
                elif script == "sindhi" and os.path.exists(FONT_SINDHI):
                    pdf.set_font("Sindhi", "", sindhi_font_size)
                else:
                    pdf.set_font("Helvetica", "", 7)
                    line2 = safe_latin(line2)
                pdf.set_xy(x + 1, y + 6)
                pdf.multi_cell(period_col_w - 2, 3.5, line2[:150], align="C")
            x += period_col_w
        y += row_h

def make_weekly_grid_pdf(rows, class_section: str, week_start_str: str, week_end_str: str) -> bytes:
    lookup = {(r["Day"], r["Period"]): r for r in rows}
    pdf, page_w = _new_grid_page()

    pdf.set_font("Helvetica", "B", 15)
    pdf.cell(0, 9, "PAKISTAN STEEL CADET COLLEGE", align="C", ln=True)

    pdf.set_font("Helvetica", "B", 11)
    third = page_w / 3
    pdf.cell(third, 8, f"Class: {class_section}", align="L")
    pdf.cell(third, 8, "Weekly Study Plan", align="C")
    pdf.cell(third, 8, f"From: {week_start_str}   To: {week_end_str}", align="R", ln=True)
    pdf.ln(2)

    def cell_lookup(day, period):
        slot = lookup.get((day, period), {})
        return {
            "line1": slot.get("Subject", ""),
            "line2": slot.get("Topic", ""),
            "subject": slot.get("Subject", "")
        }

    _render_day_period_grid(pdf, pdf.get_y(), page_w, cell_lookup, urdu_font_size=12, sindhi_font_size=10)
    return bytes(pdf.output())

def make_class_timetable_pdf(rows, class_section: str) -> bytes:
    lookup = {(r["Day"], r["Period"]): r for r in rows}
    pdf, page_w = _new_grid_page()

    pdf.set_font("Helvetica", "B", 15)
    pdf.cell(0, 9, "PAKISTAN STEEL CADET COLLEGE", align="C", ln=True)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, f"Class Time Table: {class_section}", align="C", ln=True)
    pdf.ln(2)

    def cell_lookup(day, period):
        slot = lookup.get((day, period), {})
        return {
            "line1": slot.get("Subject", ""),
            "line2": slot.get("Teacher", ""),
            "subject": slot.get("Subject", "")
        }

    _render_day_period_grid(pdf, pdf.get_y(), page_w, cell_lookup)
    return bytes(pdf.output())

def make_teacher_timetable_pdf(rows, teacher_name: str) -> bytes:
    lookup = {(r["Day"], r["Period"]): r for r in rows}
    pdf, page_w = _new_grid_page()

    pdf.set_font("Helvetica", "B", 15)
    pdf.cell(0, 9, "PAKISTAN STEEL CADET COLLEGE", align="C", ln=True)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, f"Teacher's Time Table: {teacher_name}", align="C", ln=True)
    pdf.ln(2)

    def cell_lookup(day, period):
        slot = lookup.get((day, period), {})
        return {
            "line1": str(slot.get("Class", "")),
            "line2": str(slot.get("Section", ""))
        }

    _render_day_period_grid(pdf, pdf.get_y(), page_w, cell_lookup)
    return bytes(pdf.output())
