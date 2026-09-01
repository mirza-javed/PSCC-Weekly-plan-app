import time
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from .config import (
    SPREADSHEET_ID,
    WS_TIMETABLE,
    WS_SUBJECTS,
    WS_TEACHERS,
    WS_ENTRIES,
    DAY_ORDER,
    get_service_account_credentials
)

_client = None
_spreadsheet = None
_static_cache = None
_static_cache_time = 0
CACHE_TTL = 120  # seconds

def get_client():
    global _client
    if _client is not None:
        return _client
    creds_info = get_service_account_credentials()
    if not creds_info:
        raise ValueError("Google Service Account credentials not found. Please configure GCP_SERVICE_ACCOUNT or .streamlit/secrets.toml")
    creds = Credentials.from_service_account_info(
        creds_info,
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
    )
    _client = gspread.authorize(creds)
    return _client

def get_spreadsheet():
    global _spreadsheet
    if _spreadsheet is not None:
        return _spreadsheet
    client = get_client()
    _spreadsheet = client.open_by_key(SPREADSHEET_ID)
    return _spreadsheet

def _call_with_retry(fn, *args, retries=3, **kwargs):
    last_error = None
    for attempt in range(retries):
        try:
            return fn(*args, **kwargs)
        except gspread.exceptions.APIError as e:
            last_error = e
            time.sleep(2 * (attempt + 1))
    raise last_error

def prepare_timetable(timetable_df: pd.DataFrame) -> pd.DataFrame:
    tt = timetable_df.copy()
    if "Day" in tt.columns:
        tt["day_rank"] = tt["Day"].map(lambda d: DAY_ORDER.index(d) if d in DAY_ORDER else 99)
        sort_cols = [c for c in ["Class_Section", "day_rank", "Period"] if c in tt.columns]
        if sort_cols:
            tt = tt.sort_values(sort_cols).reset_index(drop=True)
    return tt

def load_static_data(force_refresh=False):
    global _static_cache, _static_cache_time
    now = time.time()
    if not force_refresh and _static_cache and (now - _static_cache_time < CACHE_TTL):
        return _static_cache

    sh = get_spreadsheet()
    timetable_ws = sh.worksheet(WS_TIMETABLE)
    subjects_ws = sh.worksheet(WS_SUBJECTS)
    teachers_ws = sh.worksheet(WS_TEACHERS)

    timetable_raw = pd.DataFrame(timetable_ws.get_all_records())
    subjects_df = pd.DataFrame(subjects_ws.get_all_records())
    teachers_df = pd.DataFrame(teachers_ws.get_all_records())

    timetable = prepare_timetable(timetable_raw)

    _static_cache = {
        "timetable": timetable.to_dict("records"),
        "subjects": subjects_df["Subject"].dropna().tolist() if "Subject" in subjects_df.columns else [],
        "teachers": sorted(teachers_df["Teacher"].dropna().unique().tolist()) if "Teacher" in teachers_df.columns else [],
        "classes": sorted(timetable["Class"].dropna().unique().tolist()) if "Class" in timetable.columns else [],
        "class_sections": sorted(timetable["Class_Section"].dropna().unique().tolist()) if "Class_Section" in timetable.columns else []
    }
    _static_cache_time = now
    return _static_cache

def load_entries() -> pd.DataFrame:
    sh = get_spreadsheet()
    ws = sh.worksheet(WS_ENTRIES)
    records = _call_with_retry(ws.get_all_records)
    if not records:
        return pd.DataFrame(columns=["EntryID", "TimetableRowID", "WeekStartDate", "Topic", "SubmittedBy", "LastUpdated"])
    df = pd.DataFrame(records)
    if "LastUpdated" in df.columns and "EntryID" in df.columns and df["EntryID"].duplicated().any():
        df = df.sort_values("LastUpdated").drop_duplicates(subset="EntryID", keep="last")
    return df

def upsert_entries(rows_to_save):
    sh = get_spreadsheet()
    ws = sh.worksheet(WS_ENTRIES)
    existing = _call_with_retry(ws.get_all_records)
    header = ws.row_values(1)
    if not header:
        header = ["EntryID", "TimetableRowID", "WeekStartDate", "Topic", "SubmittedBy", "LastUpdated"]

    id_to_rownum = {rec["EntryID"]: i + 2 for i, rec in enumerate(existing)}

    updates, update_ids = [], []
    appends, append_ids = [], []
    for row in rows_to_save:
        entry_id = row.get("EntryID")
        if entry_id in id_to_rownum:
            rownum = id_to_rownum[entry_id]
            values = [str(row.get(col, "")) for col in header]
            updates.append({"range": f"A{rownum}:{chr(64+len(header))}{rownum}", "values": [values]})
            update_ids.append(entry_id)
        else:
            appends.append([str(row.get(col, "")) for col in header])
            append_ids.append(entry_id)

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

    return {"saved": saved, "failed": failed, "total": len(rows_to_save)}
