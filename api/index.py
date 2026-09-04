import os
from typing import List, Optional
from datetime import datetime, date, timedelta
from fastapi import FastAPI, HTTPException, Response, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .sheets_service import (
    load_static_data,
    load_entries,
    upsert_entries
)
from .pdf_service import (
    make_pdf,
    make_class_timetable_pdf,
    make_teacher_timetable_pdf,
    make_weekly_grid_pdf
)

app = FastAPI(title="PSCC Weekly Teaching Plan API", version="2.0.0")

# Enable CORS for local Vite dev server and production frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PlanRow(BaseModel):
    EntryID: str
    TimetableRowID: str
    WeekStartDate: str
    Topic: str = ""
    SubmittedBy: str = ""
    LastUpdated: Optional[str] = None

class SavePlansRequest(BaseModel):
    rows: List[PlanRow]

@app.get("/api/health")
def health_check():
    return {"status": "ok", "app": "PSCC Weekly Teaching Plan API"}

@app.get("/api/timetable")
def get_timetable(refresh: bool = False):
    try:
        data = load_static_data(force_refresh=refresh)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/plans")
def get_plans(week_start: str = Query(..., description="ISO Monday date, e.g. 2026-08-10")):
    try:
        entries = load_entries()
        week_entries = [e for e in entries if str(e.get("WeekStartDate")) == week_start]
        return {
            "week_start": week_start,
            "entries": week_entries
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/plans")
def save_plans(payload: SavePlansRequest):
    try:
        if not payload.rows:
            return {"saved": [], "failed": [], "total": 0}
        
        rows_to_save = [row.model_dump() for row in payload.rows]
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        for r in rows_to_save:
            if not r.get("LastUpdated"):
                r["LastUpdated"] = now_str
                
        result = upsert_entries(rows_to_save)
        result["rows"] = rows_to_save
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/pdf/class-timetable")
def export_class_timetable_pdf(class_section: str = Query(...)):
    try:
        data = load_static_data()
        timetable = data.get("timetable", [])
        matched = [r for r in timetable if str(r.get("Class_Section")) == class_section]
        if not matched:
            raise HTTPException(status_code=404, detail="No periods found for class section")
        
        pdf_bytes = make_class_timetable_pdf(matched, class_section)
        filename = f"Timetable_Class_{class_section.replace(' ', '_')}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'inline; filename="{filename}"'}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/pdf/teacher-timetable")
def export_teacher_timetable_pdf(teacher: str = Query(...)):
    try:
        data = load_static_data()
        timetable = data.get("timetable", [])
        matched = [r for r in timetable if str(r.get("Teacher")) == teacher]
        if not matched:
            raise HTTPException(status_code=404, detail="No periods found for teacher")
        
        pdf_bytes = make_teacher_timetable_pdf(matched, teacher)
        filename = f"Timetable_Teacher_{teacher.replace(' ', '_')}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'inline; filename="{filename}"'}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/pdf/weekly-plan")
def export_weekly_plan_pdf(
    class_section: str = Query(...),
    week_start: str = Query(...)
):
    try:
        data = load_static_data()
        timetable = data.get("timetable", [])
        matched_slots = [r for r in timetable if str(r.get("Class_Section")) == class_section]
        if not matched_slots:
            raise HTTPException(status_code=404, detail="No slots found for class section")
        
        entries = load_entries()
        entries_map = {e.get("EntryID"): e.get("Topic", "") for e in entries if e.get("EntryID")}
        merged_rows = []
        for slot in matched_slots:
            entry_id = f"{slot['RowID']}_{week_start}"
            topic = entries_map.get(entry_id, "")
            merged_rows.append({
                "Day": slot.get("Day"),
                "Period": slot.get("Period"),
                "Subject": slot.get("Subject"),
                "Teacher": slot.get("Teacher"),
                "Topic": topic
            })
        
        try:
            w_start = date.fromisoformat(week_start)
            w_end = w_start + timedelta(days=5)
            w_start_str = w_start.strftime("%d %b %Y")
            w_end_str = w_end.strftime("%d %b %Y")
        except Exception:
            w_start_str = week_start
            w_end_str = ""
            
        pdf_bytes = make_weekly_grid_pdf(merged_rows, class_section, w_start_str, w_end_str)
        filename = f"Plan_Class_{class_section.replace(' ', '_')}_{week_start}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'inline; filename="{filename}"'}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/pdf/teacher-plan")
def export_teacher_plan_pdf(
    teacher: str = Query(...),
    week_start: str = Query(...)
):
    try:
        data = load_static_data()
        timetable = data.get("timetable", [])
        matched_slots = [r for r in timetable if str(r.get("Teacher")) == teacher]
        if not matched_slots:
            raise HTTPException(status_code=404, detail="No slots found for teacher")
        
        # Sort matched slots chronologically by DAY_ORDER and Period
        day_order_list = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        def sort_key(s):
            d = s.get("Day", "")
            d_idx = day_order_list.index(d) if d in day_order_list else 99
            try:
                p = int(s.get("Period", 0))
            except Exception:
                p = 0
            return (d_idx, p)
        
        matched_slots = sorted(matched_slots, key=sort_key)
        
        entries = load_entries()
        entries_map = {e.get("EntryID"): e.get("Topic", "") for e in entries if e.get("EntryID")}
        pdf_rows = []
        for slot in matched_slots:
            entry_id = f"{slot['RowID']}_{week_start}"
            topic = entries_map.get(entry_id, "")
            pdf_rows.append({
                "Day": slot.get("Day"),
                "Period": slot.get("Period"),
                "Class": slot.get("Class_Section"),
                "Subject": slot.get("Subject"),
                "Topic": topic
            })
        
        try:
            w_start = date.fromisoformat(week_start)
            w_start_str = w_start.strftime("%d %b %Y")
        except Exception:
            w_start_str = week_start
            
        pdf_bytes = make_pdf(
            pdf_rows,
            ["Day", "Period", "Class", "Subject", "Topic"],
            f"Weekly Plan - {teacher}",
            f"Week of {w_start_str}"
        )
        filename = f"Plan_{teacher.replace(' ', '_')}_{week_start}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'inline; filename="{filename}"'}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
