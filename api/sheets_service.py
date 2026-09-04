import time
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

def prepare_timetable(records: list) -> list:
    def sort_key(r):
        cs = str(r.get("Class_Section", ""))
        day = str(r.get("Day", ""))
        day_rank = DAY_ORDER.index(day) if day in DAY_ORDER else 99
        try:
            p = int(r.get("Period", 0))
        except Exception:
            p = 0
        return (cs, day_rank, p)
    return sorted(records, key=sort_key)

def load_static_data(force_refresh=False):
    global _static_cache, _static_cache_time
    now = time.time()
    if not force_refresh and _static_cache and (now - _static_cache_time < CACHE_TTL):
        return _static_cache

    sh = get_spreadsheet()
    timetable_ws = sh.worksheet(WS_TIMETABLE)
    subjects_ws = sh.worksheet(WS_SUBJECTS)
    teachers_ws = sh.worksheet(WS_TEACHERS)

    timetable_raw = _call_with_retry(timetable_ws.get_all_records)
    subjects_raw = _call_with_retry(subjects_ws.get_all_records)
    teachers_raw = _call_with_retry(teachers_ws.get_all_records)

    timetable = prepare_timetable(timetable_raw)

    subjects = sorted(list(set(str(r.get("Subject")).strip() for r in subjects_raw if r.get("Subject"))))
    teachers = sorted(list(set(str(r.get("Teacher")).strip() for r in teachers_raw if r.get("Teacher"))))

    classes_set = set()
    for r in timetable:
        c = r.get("Class")
        if c is not None and str(c).strip():
            classes_set.add(c)
    classes = sorted(list(classes_set), key=lambda x: str(x))

    cs_set = set()
    for r in timetable:
        cs = r.get("Class_Section")
        if cs is not None and str(cs).strip():
            cs_set.add(str(cs).strip())
    class_sections = sorted(list(cs_set))

    _static_cache = {
        "timetable": timetable,
        "subjects": subjects,
        "teachers": teachers,
        "classes": classes,
        "class_sections": class_sections
    }
    _static_cache_time = now
    return _static_cache

def load_entries() -> list:
    sh = get_spreadsheet()
    ws = sh.worksheet(WS_ENTRIES)
    records = _call_with_retry(ws.get_all_records)
    if not records:
        return []

    # Deduplicate by EntryID keeping the latest LastUpdated entry
    entries_map = {}
    for r in records:
        eid = r.get("EntryID")
        if eid:
            if eid not in entries_map or str(r.get("LastUpdated", "")) >= str(entries_map[eid].get("LastUpdated", "")):
                entries_map[eid] = r
    return list(entries_map.values())

HEADER = ["EntryID", "TimetableRowID", "WeekStartDate", "Topic", "SubmittedBy", "LastUpdated"]

def upsert_entries(rows_to_save):
    sh = get_spreadsheet()
    ws = sh.worksheet(WS_ENTRIES)
    
    # Fast single-column read to map EntryID -> sheet row number (index + 1)
    entry_ids_col = _call_with_retry(ws.col_values, 1)
    
    id_to_rownum = {}
    for i, eid in enumerate(entry_ids_col):
        if i > 0 and eid:
            id_to_rownum[str(eid).strip()] = i + 1

    updates, update_ids = [], []
    appends, append_ids = [], []
    
    for row in rows_to_save:
        entry_id = str(row.get("EntryID", "")).strip()
        if not entry_id:
            continue
        
        topic = str(row.get("Topic", "")).strip()

        if entry_id in id_to_rownum:
            rownum = id_to_rownum[entry_id]
            values = [str(row.get(col, "")) for col in HEADER]
            updates.append({"range": f"A{rownum}:F{rownum}", "values": [values]})
            update_ids.append(entry_id)
        else:
            # Only append new entries if they have an actual topic
            if topic:
                appends.append([str(row.get(col, "")) for col in HEADER])
                append_ids.append(entry_id)

    saved, failed = [], []
    if updates:
        try:
            _call_with_retry(ws.batch_update, updates)
            saved += update_ids
        except Exception as e:
            print(f"Error updating entries: {e}")
            failed += update_ids
            
    if appends:
        try:
            _call_with_retry(ws.append_rows, appends)
            saved += append_ids
        except Exception as e:
            print(f"Error appending entries: {e}")
            failed += append_ids

    return {"saved": saved, "failed": failed, "total": len(rows_to_save)}
