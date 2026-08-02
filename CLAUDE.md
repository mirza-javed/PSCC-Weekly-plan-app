# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Streamlit app "PSCC Weekly Teaching Plan": joins a class timetable to weekly teaching plans —
teachers enter plans per period, admins view any class/section's timetable + plan by week,
everything downloads as PDF. All logic lives in `app.py` (config → Sheets connection → helpers →
PDF builder → three tabs). No tests.

## Run it

```bash
venv\Scripts\activate        # Windows (venv already exists)
streamlit run app.py         # opens at http://localhost:8501
```

Needs `.streamlit/secrets.toml` (gitignored) with the service-account JSON under
`[gcp_service_account]` and `SPREADSHEET_ID` near the top of `app.py`; without credentials it errors at startup.

## Data model (Google Sheets backend)

One spreadsheet, 4 tabs looked up by exact (case-sensitive) name:
- **Timetable** — tidy/long, one row per period slot. `RowID` (e.g. `Monday-1-8-A`) is the unique
  slot key / join key everywhere.
- **Subjects** / **Teachers** — one-column reference lists feeding dropdowns.
- **Teaching_Plan_Entries** — `EntryID | TimetableRowID | WeekStartDate | Topic | SubmittedBy | LastUpdated`.
  `EntryID = <TimetableRowID>_<WeekStartDate>` (Monday's ISO date), so saving is an **upsert**:
  existing `EntryID` updates in place, else appends (`upsert_entries` batches to ~3 API calls).

Invariants: `WeekStartDate` is always that week's Monday (`monday_of()`); Data Entry locks
read-only once a week starts; Weekly Plan View is always read-only.

## Caching, connection, PDFs

`get_client()`/`get_spreadsheet()` are `@st.cache_resource`; static sheets `@st.cache_data(ttl=120)`;
`load_entries()` is **never cached** (changes every save). Auth uses Sheets + Drive scopes.
`make_pdf(rows, columns, title, subtitle)` builds every PDF. `detect_font_for()` picks Urdu /
Sindhi / Latin per cell; Urdu/Sindhi render in the matching Nastaliq font from `fonts/` (needs
`uharfbuzz` shaping). Widths come from `COLUMN_WIDTHS` (Topic gets the remainder); long tables
split into two side-by-side blocks on one landscape A4 page. Cells truncate at `int(width/1.7)`
chars — long topics get cut off.

## Gotchas

- Sheet tab/column names must match the `WS_*` constants exactly or lookups return empty frames.
- `SINDHI_ONLY_CHARS` detection is approximate by design — don't "fix" it unless a real mis-detection is reported.
- Streamlit widget keys are tab-prefixed (`t1_`, `t2_`, `t3_`) to avoid collisions.
