"""
PSCC Weekly Teaching Plan App
------------------------------
Three tabs, one Google Sheets file behind them:

  TAB 1 - Timetable View     : browse the master schedule (by class+section, or by teacher)
  TAB 2 - Data Entry         : teachers write their week's plan directly against the timetable
  TAB 3 - Weekly Plan View   : admin filters by class+section (+week) to see timetable + topics

All three tabs can be downloaded as PDF. Urdu/Sindhi entries are auto-detected and
rendered in the correct Nastaliq font in the PDF.

------------------------------------------------------------------------------
ONE-TIME SETUP YOU NEED TO DO (this app WRITES data, so it needs more than the
read-only setup we used for the earlier dashboard):

1. Put all 4 sheets as TABS INSIDE ONE Google Sheets file (recommended, simpler
   than juggling multiple files): Timetable, Subjects, Teachers, Teaching_Plan_Entries.
   (Teaching_Plan_Entries can start empty -- just add the header row:
    EntryID | TimetableRowID | WeekStartDate | Topic | SubmittedBy | LastUpdated)

2. Create a Google Service Account (one-time, in Google Cloud Console):
   a. console.cloud.google.com -> create a project (or use an existing one)
   b. "APIs & Services" -> Library -> enable "Google Sheets API" and "Google Drive API"
   c. "APIs & Services" -> Credentials -> Create Credentials -> Service Account
   d. Open the service account -> Keys -> Add Key -> JSON -> download the file
   e. Open that JSON file -- it has a "client_email" field, something like
      xxxx@xxxx.iam.gserviceaccount.com
   f. Open your Google Sheet -> Share -> paste that email in -> give it "Editor" access

3. In Streamlit Cloud, go to your app's Settings -> Secrets, and paste the ENTIRE
   contents of that JSON file under a [gcp_service_account] section, e.g.:

   [gcp_service_account]
   type = "service_account"
   project_id = "..."
   private_key_id = "..."
   private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
   client_email = "...@....iam.gserviceaccount.com"
   client_id = "..."
   token_uri = "https://oauth2.googleapis.com/token"

4. Put the two font files (Jameel_Noori_Nastaleeq_Regular.ttf and the Sindhi font)
   in a "fonts/" folder next to this app.py, in your GitHub repo.

5. Fill in SPREADSHEET_ID below (the long ID in your sheet's URL, after /d/).
------------------------------------------------------------------------------
"""

import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
import re
import time
import gspread
from google.oauth2.service_account import Credentials
from fpdf import FPDF

# ============ 1. CONFIGURATION ============
SPREADSHEET_ID = "1x5wykhZlN2-pFqrreCFvQmDZikZkV8_1fr5igQ-6GCk"

WS_TIMETABLE = "Timetable"
WS_SUBJECTS = "Subjects"
WS_TEACHERS = "Teachers"
WS_ENTRIES = "Teaching_Plan_Entries"

DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
PERIODS_PER_DAY = {"Monday": 7, "Tuesday": 7, "Wednesday": 7, "Thursday": 7,
                    "Friday": 6, "Saturday": 6}

FONT_URDU = "fonts/Jameel_Noori_Nastaleeq_Regular.ttf"
FONT_SINDHI = "fonts/MB-Lateefi-SKv2_0.ttf"

# Characters that only appear in Sindhi, not standard Urdu -- used to tell the
# two apart automatically. Not 100% perfect (some fonts/typists vary), but
# good enough to pick the right font for the common case. (ڙڪڻڌڙ inserted
# because words like پڙهڻ/ايڪو/سنڌي are Sindhi but contain no letter from
# the original list, so they were being rendered with the Urdu font, which
# garbles them.)
SINDHI_ONLY_CHARS = set("ٻڀٺٽٿڃڄڇڏڊڍڦڱڳڙڪڻڌ")
ARABIC_SCRIPT_RANGE = re.compile(r"[\u0600-\u06FF]")


# ============ 2. GOOGLE SHEETS CONNECTION ============
@st.cache_resource
def get_client():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"],
    )
    return gspread.authorize(creds)


@st.cache_resource
def get_spreadsheet():
    return get_client().open_by_key(SPREADSHEET_ID)


@st.cache_data(ttl=120)
def load_static_sheets():
    """Timetable/Subjects/Teachers rarely change within a session, so these
    are cached briefly to avoid hitting the Sheets API on every click."""
    sh = get_spreadsheet()
    timetable = pd.DataFrame(sh.worksheet(WS_TIMETABLE).get_all_records())
    subjects = pd.DataFrame(sh.worksheet(WS_SUBJECTS).get_all_records())
    teachers = pd.DataFrame(sh.worksheet(WS_TEACHERS).get_all_records())
    return timetable, subjects, teachers


def load_entries() -> pd.DataFrame:
    """Teaching_Plan_Entries changes constantly (every save), so this is
    NEVER cached -- always reads fresh."""
    sh = get_spreadsheet()
    ws = sh.worksheet(WS_ENTRIES)
    records = ws.get_all_records()
    if not records:
        return pd.DataFrame(columns=["EntryID", "TimetableRowID", "WeekStartDate",
                                      "Topic", "SubmittedBy", "LastUpdated"])
    df = pd.DataFrame(records)
    # Safety net: if the same EntryID ever ends up on more than one row
    # (e.g. a save submitted twice in a row on a slow connection before
    # the sheet had a chance to update), always keep the most recently
    # updated one -- this must match what upsert_entries() below treats
    # as canonical, or a save can look successful yet the box still
    # shows old/blank data the next time it's opened.
    if "LastUpdated" in df.columns and df["EntryID"].duplicated().any():
        df = df.sort_values("LastUpdated").drop_duplicates(subset="EntryID", keep="last")
    return df


def _call_with_retry(fn, *args, retries=3, **kwargs):
    """Retries a Google Sheets API call a few times with a short pause if
    it hits a rate-limit / transient error, instead of failing outright.
    This is the single biggest cause of "it looked saved but wasn't" --
    all teachers share one Google service account, so a busy moment
    (many teachers saving around the same time) can trip Google's
    per-minute write quota for a single request."""
    last_error = None
    for attempt in range(retries):
        try:
            return fn(*args, **kwargs)
        except gspread.exceptions.APIError as e:
            last_error = e
            time.sleep(2 * (attempt + 1))  # wait a bit longer each retry
    raise last_error


def upsert_entries(rows_to_save):
    """Writes a batch of entries: updates a row if its EntryID already
    exists, otherwise appends a new row.

    Returns a dict: {"saved": [...EntryIDs that saved successfully...],
                      "failed": [...EntryIDs that did not...]}
    so the caller can tell the teacher exactly what went through, instead
    of an all-or-nothing silent result. The update batch and the append
    batch are two separate API calls -- if one fails after the other
    already succeeded, this makes sure that partial success is still
    reported accurately rather than assumed to be a total failure."""
    sh = get_spreadsheet()
    ws = sh.worksheet(WS_ENTRIES)
    existing = _call_with_retry(ws.get_all_records)
    header = ws.row_values(1)
    id_to_rownum = {rec["EntryID"]: i + 2 for i, rec in enumerate(existing)}  # +2: header + 1-index

    updates, update_ids = [], []
    appends, append_ids = [], []
    for row in rows_to_save:
        if row["EntryID"] in id_to_rownum:
            rownum = id_to_rownum[row["EntryID"]]
            values = [row.get(col, "") for col in header]
            updates.append({"range": f"A{rownum}:{chr(64+len(header))}{rownum}", "values": [values]})
            update_ids.append(row["EntryID"])
        else:
            appends.append([row.get(col, "") for col in header])
            append_ids.append(row["EntryID"])

    saved, failed = [], []
    if updates:
        try:
            _call_with_retry(ws.batch_update, updates)
            saved += update_ids
        except gspread.exceptions.APIError:
            failed += update_ids
    if appends:
        try:
            _call_with_retry(ws.append_rows, appends)
            saved += append_ids
        except gspread.exceptions.APIError:
            failed += append_ids

    return {"saved": saved, "failed": failed}


# ============ 3. HELPERS ============
def monday_of(d: date) -> date:
    return d - timedelta(days=d.weekday())  # Monday = weekday 0


def prepare_timetable(timetable: pd.DataFrame) -> pd.DataFrame:
    tt = timetable.copy()
    tt["day_rank"] = tt["Day"].map(lambda d: DAY_ORDER.index(d))
    tt = tt.sort_values(["Class_Section", "day_rank", "Period"]).reset_index(drop=True)
    return tt


def detect_font_for(text: str, subject: str = "") -> str:
    """Returns 'sindhi', 'urdu', or 'latin' depending on the script used.

    `subject` is the row's Subject value when known ("Sindhi", "Urdu", ...).
    It acts as the strongest hint because a topic under the Sindhi subject
    can be made up entirely of letters that are also valid Urdu (e.g.
    "قومي ايڪو") -- letter-detection alone would misclassify it as Urdu and
    render it with the Urdu font, which garbles Sindhi words."""
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
    """Helvetica (the built-in font used for English text) only supports
    Latin-1 characters. Teachers typing from a phone keyboard can easily
    include an emoji, a "smart" curly quote, or another character outside
    that range -- which would otherwise crash PDF generation entirely.
    This swaps anything unsupported for a plain '?' instead of failing."""
    if not isinstance(text, str):
        return str(text)
    try:
        text.encode("latin-1")
        return text
    except UnicodeEncodeError:
        return text.encode("latin-1", errors="replace").decode("latin-1")


# ============ 4. PDF BUILDER (shared by all 3 tabs) ============
# Content-sized widths (mm) -- short columns stay narrow, Topic gets the rest.
# This is what removes the wasted white space you saw.
COLUMN_WIDTHS = {"Day": 24, "Period": 14, "Class": 16, "Class_Section": 20,
                  "Subject": 30, "Teacher": 24}
ROW_HEIGHT = 7
HEADER_HEIGHT = 8


def make_pdf(rows, columns, title, subtitle=""):
    """rows: list of dicts with keys matching `columns`. Any cell whose
    text is Urdu/Sindhi is rendered in the matching Nastaliq font;
    everything else uses the normal Latin font.

    Layout: if all rows fit in one column-block on the page, prints as a
    single table. If not (e.g. a full week's 40 rows), splits the rows in
    half and prints the second half in a second block BESIDE the first
    one on the same page, instead of continuing onto a new page below."""
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.set_margins(10, 10, 10)
    pdf.add_page()
    pdf.add_font("Urdu", "", FONT_URDU)
    pdf.add_font("Sindhi", "", FONT_SINDHI)
    pdf.set_text_shaping(True)  # needed for correct Nastaliq letter-joining (needs uharfbuzz installed)

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Pakistan Steel Cadet College", align="C", ln=True)
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 9, title, align="C", ln=True)
    if subtitle:
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 8, subtitle, ln=True)
    pdf.ln(2)
    top_y = pdf.get_y()

    page_width = 297 - 20  # landscape A4 minus left+right margins
    gap = 8  # space between the two blocks, when there are two
    block_width = (page_width - gap) / 2

    fixed_cols = [c for c in columns if c != "Topic"]
    fixed_total = sum(COLUMN_WIDTHS.get(c, 22) for c in fixed_cols)

    usable_height = 210 - top_y - 15  # landscape page height (210mm) minus margins/footer room
    max_rows_per_block = max(1, int((usable_height - HEADER_HEIGHT) / ROW_HEIGHT))

    n = len(rows)
    if n <= max_rows_per_block:
        blocks = [(rows, 10, page_width)]
    else:
        half = -(-n // 2)  # ceil
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
                if script == "urdu":
                    pdf.set_font("Urdu", "", 10)
                elif script == "sindhi":
                    pdf.set_font("Sindhi", "", 10)
                else:
                    pdf.set_font("Helvetica", "", 8)
                    text = safe_latin(text)
                max_chars = max(3, int(w / 1.7))
                pdf.cell(w, ROW_HEIGHT, text[:max_chars], border=1)
            pdf.ln(ROW_HEIGHT)
            pdf.set_x(x0)

    return bytes(pdf.output())


ONE_INCH = 25.4  # mm
TOP_MARGIN_075IN = 19.05  # mm


def _new_grid_page():
    """Common page setup shared by all 3 grid-style PDFs: Legal, landscape,
    1-inch left/right margins, 0.75-inch top margin."""
    pdf = FPDF(orientation="L", unit="mm", format="Legal")
    pdf.set_margins(ONE_INCH, TOP_MARGIN_075IN, ONE_INCH)
    pdf.add_page()
    pdf.add_font("Urdu", "", FONT_URDU)
    pdf.add_font("Sindhi", "", FONT_SINDHI)
    pdf.set_text_shaping(True)
    return pdf, pdf.w - 2 * ONE_INCH  # pdf, usable page width


def _render_day_period_grid(pdf, top_y, page_w, cell_lookup, urdu_font_size=9, sindhi_font_size=9):
    """Draws the Days x Period_01..07 grid used by all 3 templates.
    cell_lookup(day, period) -> {"line1": ..., "line2": ...} or None for
    an empty slot. Periods beyond that day's actual count (Period_07 on
    Fri/Sat) are dashed-out automatically, matching the templates."""
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
                if script == "urdu":
                    pdf.set_font("Urdu", "", urdu_font_size)
                elif script == "sindhi":
                    pdf.set_font("Sindhi", "", sindhi_font_size)
                else:
                    pdf.set_font("Helvetica", "", 7)
                    line2 = safe_latin(line2)
                pdf.set_xy(x + 1, y + 6)
                pdf.multi_cell(period_col_w - 2, 3.5, line2[:150], align="C")
            x += period_col_w
        y += row_h


def make_weekly_grid_pdf(rows, class_section: str, week_start: date, week_end: date) -> bytes:
    """Weekly Study Plan template: Class (left) / "Weekly Study Plan"
    (center) / From-To dates (right) on one sub-heading line, then the
    Days x Period grid with Subject + Topic per cell."""
    lookup = {(r["Day"], r["Period"]): r for r in rows}
    pdf, page_w = _new_grid_page()

    pdf.set_font("Helvetica", "B", 15)
    pdf.cell(0, 9, "PAKISTAN STEEL CADET COLLEGE", align="C", ln=True)

    pdf.set_font("Helvetica", "B", 11)
    third = page_w / 3
    pdf.cell(third, 8, f"Class: {class_section}", align="L")
    pdf.cell(third, 8, "Weekly Study Plan", align="C")
    pdf.cell(third, 8, f"From: {week_start.strftime('%d %b %Y')}   To: {week_end.strftime('%d %b %Y')}",
              align="R", ln=True)
    pdf.ln(2)

    def cell_lookup(day, period):
        slot = lookup.get((day, period), {})
        return {"line1": slot.get("Subject", ""), "line2": slot.get("Topic", ""),
                "subject": slot.get("Subject", "")}

    _render_day_period_grid(pdf, pdf.get_y(), page_w, cell_lookup, urdu_font_size=12, sindhi_font_size=10)
    return bytes(pdf.output())


def make_class_timetable_pdf(rows, class_section: str) -> bytes:
    """Class Time Table template: each cell shows Subject + Teacher."""
    lookup = {(r["Day"], r["Period"]): r for r in rows}
    pdf, page_w = _new_grid_page()

    pdf.set_font("Helvetica", "B", 15)
    pdf.cell(0, 9, "PAKISTAN STEEL CADET COLLEGE", align="C", ln=True)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, f"Class Time Table: {class_section}", align="C", ln=True)
    pdf.ln(2)

    def cell_lookup(day, period):
        slot = lookup.get((day, period), {})
        return {"line1": slot.get("Subject", ""), "line2": slot.get("Teacher", ""),
                "subject": slot.get("Subject", "")}

    _render_day_period_grid(pdf, pdf.get_y(), page_w, cell_lookup)
    return bytes(pdf.output())


def make_teacher_timetable_pdf(rows, teacher_name: str) -> bytes:
    """Teacher's Time Table template: each cell shows Class + Section."""
    lookup = {(r["Day"], r["Period"]): r for r in rows}
    pdf, page_w = _new_grid_page()

    pdf.set_font("Helvetica", "B", 15)
    pdf.cell(0, 9, "PAKISTAN STEEL CADET COLLEGE", align="C", ln=True)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, f"Teacher's Time Table: {teacher_name}", align="C", ln=True)
    pdf.ln(2)

    def cell_lookup(day, period):
        slot = lookup.get((day, period), {})
        return {"line1": str(slot.get("Class", "")), "line2": str(slot.get("Section", ""))}

    _render_day_period_grid(pdf, pdf.get_y(), page_w, cell_lookup)
    return bytes(pdf.output())


# ============ 5. STREAMLIT APP ============
st.set_page_config(page_title="PSCC Weekly Teaching Plan", layout="wide")
st.title("PSCC Weekly Teaching Plan")

try:
    timetable_raw, subjects_df, teachers_df = load_static_sheets()
    timetable = prepare_timetable(timetable_raw)
except Exception as e:
    st.error("Could not connect to Google Sheets. Check SPREADSHEET_ID and that "
              "the service account has Editor access to the sheet.")
    st.exception(e)
    st.stop()

tab1, tab2, tab3 = st.tabs(["Timetable View", "Data Entry", "Weekly Plan View"])

# ---------------- TAB 1: TIMETABLE VIEW ----------------
with tab1:
    view_mode = st.radio("View by", ["Class & Section", "Teacher"], horizontal=True)

    if view_mode == "Class & Section":
        c1, c2 = st.columns(2)
        with c1:
            class_no = st.selectbox("Class", sorted(timetable["Class"].unique()), key="t1_class")
        with c2:
            sections = sorted(timetable[timetable["Class"] == class_no]["Section"].unique())
            section = st.selectbox("Section", sections, key="t1_section")
        view_df = timetable[(timetable["Class"] == class_no) & (timetable["Section"] == section)]
        title = f"Timetable - Class {class_no}-{section}"
        pdf_bytes = make_class_timetable_pdf(view_df.to_dict("records"), f"{class_no}-{section}")
    else:
        teacher = st.selectbox("Teacher", sorted(timetable["Teacher"].dropna().unique()), key="t1_teacher")
        view_df = timetable[timetable["Teacher"] == teacher].sort_values(["day_rank", "Period"])
        title = f"Timetable - {teacher}"
        pdf_bytes = make_teacher_timetable_pdf(view_df.to_dict("records"), teacher)

    show_cols = ["Day", "Period", "Class_Section", "Subject", "Teacher"]
    st.dataframe(view_df[show_cols], use_container_width=True, hide_index=True)

    st.download_button("Download as PDF", data=pdf_bytes,
                        file_name=f"{title.replace(' ', '_')}.pdf", mime="application/pdf",
                        key="t1_pdf")

# ---------------- TAB 2: DATA ENTRY ----------------
with tab2:
    st.subheader("Week")
    today = date.today()
    # IMPORTANT: once a widget has a `key`, Streamlit reads its value from
    # that key on every rerun and ignores `value=` after the first render.
    # So the buttons below must write straight into "t2_date_input" itself
    # (the date_input's own key) -- not a separate tracking variable -- or
    # the widget will keep showing whatever it already had.
    if "t2_date_input" not in st.session_state:
        st.session_state["t2_date_input"] = today

    # Two buttons side by side (fine at half-width each, even on a phone),
    # then the date picker on its own full-width line below -- this stacks
    # naturally on a narrow screen instead of squeezing 3 items into one row.
    qc1, qc2 = st.columns(2)
    with qc1:
        if st.button("This week", use_container_width=True):
            st.session_state["t2_date_input"] = today
    with qc2:
        if st.button("Next week", use_container_width=True):
            st.session_state["t2_date_input"] = today + timedelta(days=7)
    pick_date = st.date_input("...or pick any date in the target week", key="t2_date_input")

    week_start = monday_of(pick_date)
    week_end = week_start + timedelta(days=5)  # Saturday
    st.info(f"Planning for: **{week_start.strftime('%a %d %b %Y')} - {week_end.strftime('%a %d %b %Y')}**")

    editable = week_start > today  # only future weeks can be edited, per your rule
    if not editable:
        st.warning("This week has already started (or is in the past) — entries are locked and shown read-only.")

    teacher_name = st.selectbox("Your name", sorted(teachers_df["Teacher"].dropna().unique()), key="t2_teacher")

    # Only this teacher's own periods -- across every class & section they teach --
    # in chronological order (Monday's periods first, then Tuesday's, etc.)
    slots = timetable[timetable["Teacher"] == teacher_name]
    entries_df = load_entries()
    week_str = week_start.isoformat()

    if slots.empty:
        st.warning("No periods found in the timetable for this teacher.")
    else:
        st.subheader(f"{teacher_name} — enter this week's plan")
        new_rows = []
        for _, slot in slots.iterrows():
            entry_id = f"{slot['RowID']}_{week_str}"
            existing = entries_df[entries_df["EntryID"] == entry_id] if not entries_df.empty else pd.DataFrame()
            existing_topic = existing.iloc[0]["Topic"] if not existing.empty else ""

            # Label shows Class-Section + Subject so a teacher with multiple
            # classes on the same day/period can still tell them apart.
            label = f"{slot['Day']} - Period {slot['Period']} - {slot['Class_Section']} - {slot['Subject']}"
            if editable:
                topic = st.text_area(label, value=existing_topic, key=f"topic_{entry_id}", height=68)
            else:
                st.markdown(f"**{label}**")
                st.text(existing_topic or "(nothing submitted)")
                topic = existing_topic

            new_rows.append({
                "EntryID": entry_id, "TimetableRowID": slot["RowID"], "WeekStartDate": week_str,
                "Topic": topic, "SubmittedBy": teacher_name,
                "LastUpdated": datetime.now().strftime("%Y-%m-%d %H:%M"),
            })

        if editable:
            if st.button("Save week's plan", type="primary", use_container_width=True):
                with st.spinner("Saving your plan — please wait, don't tap Save again..."):
                    result = upsert_entries(new_rows)
                if result["failed"]:
                    st.session_state["t2_save_result"] = (
                        f"Saved {len(result['saved'])} of {len(new_rows)} periods. "
                        f"{len(result['failed'])} didn't go through (likely a busy moment on the server) "
                        f"— please try Save again to submit just the rest."
                    )
                else:
                    st.session_state["t2_save_result"] = "success"
                st.rerun()

        pdf_rows = []
        for nr in new_rows:
            slot_row = slots[slots["RowID"] == nr["TimetableRowID"]].iloc[0]
            pdf_rows.append({"Day": slot_row["Day"], "Period": slot_row["Period"],
                              "Class": slot_row["Class_Section"], "Subject": slot_row["Subject"],
                              "Topic": nr["Topic"]})
        pdf_bytes2 = make_pdf(pdf_rows, ["Day", "Period", "Class", "Subject", "Topic"],
                                f"Weekly Plan - {teacher_name}",
                                f"Week of {week_start.strftime('%d %b %Y')}")
        st.download_button("Download as PDF", data=pdf_bytes2,
                            file_name=f"Plan_{teacher_name.replace(' ', '_')}_{week_str}.pdf",
                            mime="application/pdf", key="t2_pdf", use_container_width=True)

        # Shown here (below the buttons) rather than at the top of the entry
        # list, since that's what's actually in view after scrolling down to click Save.
        save_result = st.session_state.get("t2_save_result")
        if save_result == "success":
            st.success("Weekly plan saved successfully.")
        elif save_result:
            st.warning(save_result)
        st.session_state["t2_save_result"] = None

# ---------------- TAB 3: WEEKLY PLAN VIEW (admin) ----------------
with tab3:
    c1, c2, c3 = st.columns(3)
    with c1:
        view_date = st.date_input("Any date in the week", value=date.today(), key="t3_date")
    with c2:
        class_no3 = st.selectbox("Class", sorted(timetable["Class"].unique()), key="t3_class")
    with c3:
        sections3 = sorted(timetable[timetable["Class"] == class_no3]["Section"].unique())
        section3 = st.selectbox("Section", sections3, key="t3_section")

    week_start3 = monday_of(view_date)
    week_end3 = week_start3 + timedelta(days=5)  # Saturday
    slots3 = timetable[(timetable["Class"] == class_no3) & (timetable["Section"] == section3)]
    entries_df3 = load_entries()
    week_str3 = week_start3.isoformat()

    merged_rows = []
    for _, slot in slots3.iterrows():
        entry_id = f"{slot['RowID']}_{week_str3}"
        match = entries_df3[entries_df3["EntryID"] == entry_id] if not entries_df3.empty else pd.DataFrame()
        topic = match.iloc[0]["Topic"] if not match.empty else ""
        merged_rows.append({"Day": slot["Day"], "Period": slot["Period"], "Subject": slot["Subject"],
                             "Teacher": slot["Teacher"], "Topic": topic})

    merged_df = pd.DataFrame(merged_rows)
    st.dataframe(merged_df, use_container_width=True, hide_index=True)
    missing3 = (merged_df["Topic"] == "").sum()
    if missing3:
        st.info(f"{missing3} period(s) have no submitted plan for this week.")

    title3 = f"Weekly Plan - Class {class_no3}-{section3}"
    pdf_bytes3 = make_weekly_grid_pdf(merged_rows, f"{class_no3}-{section3}", week_start3, week_end3)
    st.download_button("Download as PDF", data=pdf_bytes3,
                        file_name=f"{title3.replace(' ', '_')}_{week_str3}.pdf", mime="application/pdf",
                        key="t3_pdf")
