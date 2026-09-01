# PSCC Weekly Teaching Plan — Technical Analysis & Scaling Recommendations

**Author:** Antigravity AI  
**Date:** August 2, 2026  
**Target Application:** PSCC Weekly Teaching Plan (`app.py`)  
**Document Status:** Final Recommendations Report  

---

## 1. Executive Summary

The **PSCC Weekly Teaching Plan** application is a lightweight, purpose-built Streamlit app designed for Pakistan Steel Cadet College. It successfully bridges static timetable schedules with dynamic weekly lesson planning by allowing teachers to enter topic submissions and administrative staff to view and export merged schedules as bilingual PDFs (supporting English, Urdu, and Sindhi).

While the application solves an immediate operational problem effectively, the current implementation is a single-file prototype (`app.py`) built on top of Google Sheets. As user concurrency increases, historical data accumulates, or security demands tighten, the current setup will encounter critical bottlenecks in data integrity, API rate limits, user authorization, and layout formatting.

This document provides a thorough codebase analysis and presents an actionable, multi-phase roadmap to transform the application into a robust, scalable, secure, and maintainable academic management system without altering the core functionality.

---

## 2. Current Architecture & Codebase Overview

```
Time_Table_Weekly_planner/
├── app.py                  # Monolithic entrypoint (417 lines: config, DB, PDF, UI)
├── requirements.txt        # Dependencies: streamlit, pandas, fpdf2, gspread, google-auth, uharfbuzz
├── CLAUDE.md               # Claude guidelines & invariants
├── PROJECT_SUMMARY.md      # Design background & historical context
├── README.md               # Setup & deployment documentation
├── fonts/
│   ├── Jameel_Noori_Nastaleeq_Regular.ttf   # Urdu font (~10.7 MB)
│   └── MB-Lateefi-SKv2_0.ttf                # Sindhi font (~96 KB)
└── docs/                   # Documentation directory
```

### Core Strengths
1. **Clear Domain Modeling:** Long/tidy data schema using `RowID` (`Day-Period-Class-Section`) as a primary composite join key.
2. **Bilingual PDF Rendering Engine:** Automatic script detection (Latin vs. Urdu vs. Sindhi) with HarfBuzz/uharfbuzz text shaping for complex Nastaliq ligatures.
3. **Teacher-Centric Data Entry UI:** Filtering entries specifically by teacher reduces cognitive load compared to class-by-class grid entry.

---

## 3. Detailed Technical Analysis & Critical Vulnerabilities

### A. Monolithic Architecture & Code Maintainability
* **Single File Antipattern:** All business logic, UI declaration, database API integration, helpers, and PDF rendering are tightly coupled in `app.py`.
* **Zero Automated Test Coverage:** No unit or integration tests exist for date math (`monday_of`), language detection (`detect_font_for`), PDF formatting (`make_pdf`), or database upserts.
* **Hardcoded Magic Strings:** Worksheet tab names (`Timetable`, `Teaching_Plan_Entries`) and column header strings are hardcoded across multiple functions.

### B. Storage & Concurrency Limitations (Google Sheets as Backend)
* **API Rate Limits & Quotas:** Google Sheets API imposes a quota limit (60 requests/minute per user). Concurrent submissions by multiple teachers on peak submission days (e.g., Friday/Saturday) will trigger `HTTP 429 Too Many Requests` errors.
* **Race Conditions & Lost Updates:** `upsert_entries` reads all records into Python memory, maps row indices in-memory, and writes updates back. If two teachers submit plans concurrently, one teacher's submission can overwrite or corrupt row indices.
* **Uncached Data Fetching:** `load_entries()` reads the entire `Teaching_Plan_Entries` worksheet on **every single Streamlit rerun** without caching. As entries grow to thousands of rows over the academic year, app performance will degrade linearly ($O(N)$ network latency per user click).

### C. Security & Access Control Vulnerabilities
* **No Authentication or Authorization:** The application lacks user login. Any user who accesses the Streamlit web URL can select any teacher's name from the dropdown and modify or overwrite their submitted lesson plans.
* **Lack of Audit Logging:** `LastUpdated` stores a simple timestamp, but there is no audit log or version history to track who changed a plan or restore prior topic entries.
* **Over-Privileged Service Account:** The service account has broad Editor access to the entire Google Sheet without field-level security.

### D. PDF Layout & Rendering Deficiencies
* **Cell Text Truncation vs. Multi-line Wrapping:** `pdf.cell(w, ROW_HEIGHT, text[:max_chars])` truncates text strictly at `int(w / 1.7)` characters. Detailed multi-sentence topics entered by teachers get abruptly cut off in the exported PDF report.
* **Memory & Performance Overhead:** The 10.7 MB Nastaleeq font is re-registered on every call to `make_pdf()`. High memory consumption and CPU usage occur when multiple users request PDF exports simultaneously.

### E. Business Logic & UX Edge Cases
* **Strict Lock Rule Bug:** `editable = week_start > today` locks data entry as soon as `today == week_start` (Monday). Teachers attempting to finalize or adjust plans on Monday morning are prematurely locked out.
* **Timezone Inconsistencies:** `date.today()` relies on the server host system time. On Streamlit Cloud (UTC), dates shift at midnight UTC, causing lock states to change unexpectedly for users in Pakistan Standard Time (PKT, UTC+5).

---

## 4. Actionable Recommendations & Scaling Roadmap

### Phase 1: Immediate Refactoring & Quality Improvements (Low Effort, High Value)

#### 1. Modularize Code Structure
Split `app.py` into dedicated modules:
* `config.py`: Application constants, column names, paths, feature flags.
* `services/db.py`: Google Sheets client initialization, caching, load/upsert functions.
* `services/pdf.py`: Font loading, text shaping, multi-cell rendering engine.
* `utils/text.py`: Language detection (`detect_font_for`), date utilities (`monday_of`).
* `views/`: Individual Streamlit UI tab views (`tab_timetable.py`, `tab_entry.py`, `tab_plan.py`).

#### 2. Fix PDF Text Truncation with Multi-Cell Wrapping
Replace fixed-height `pdf.cell()` with `pdf.multi_cell()` or calculated row heights so long topic descriptions wrap naturally across lines without text loss.

#### 3. Implement Intelligent Data Caching
Wrap `load_entries()` with `@st.cache_data(ttl=15)` or use Streamlit `st.session_state` to prevent unnecessary Google Sheets API requests on every UI click while keeping data sufficiently fresh.

#### 4. Timezone-Aware Lock Logic
Enforce explicit timezone handling (`Asia/Karachi`) using Python's `zoneinfo` module:
```python
from zoneinfo import ZoneInfo
from datetime import datetime

pkt_today = datetime.now(ZoneInfo("Asia/Karachi")).date()
# Allow editing up to Monday end-of-day or explicit cutoff
```

---

### Phase 2: Security, Authentication & Data Integrity (Medium Effort)

#### 1. Add User Authentication & Role-Based Access Control (RBAC)
* Integrate `streamlit-authenticator` or OAuth2 (Google Workspace Login).
* **Teachers:** Automatically filter Data Entry tab to the logged-in teacher's schedule only; restrict editing other teachers' plans.
* **Admins / Principals:** Access Weekly Plan View across all classes, section completion reports, and global PDF downloads.

#### 2. Introduce Transaction Safety & Optimistic Locking
Include a `Version` or `Hash` field in `Teaching_Plan_Entries` to verify row integrity before performing upserts, preventing overwrites from concurrent editing sessions.

#### 3. Automated Testing Suite
Add `pytest` test cases covering:
* `monday_of()` date calculations across month/year boundaries.
* `detect_font_for()` script classification for English, Urdu, and Sindhi text.
* Data frame merging logic between `Timetable` and `Teaching_Plan_Entries`.

---

### Phase 3: Enterprise Database & Architectural Scaling (High Impact)

```
+-----------------------------------------------------------------------+
|                            USER INTERFACE                             |
|        Streamlit App (Admins)    /    Web & Mobile Client (Teachers)   |
+-----------------------------------+-----------------------------------+
                                    |
                                    v
+-----------------------------------------------------------------------+
|                         APPLICATION API LAYER                         |
|                         FastAPI / Python Backend                      |
+-----------------------------------+-----------------------------------+
                                    |
                                    v
+-----------------------------------------------------------------------+
|                           DATABASE STORAGE                            |
|             PostgreSQL / SQLite (SQLAlchemy ORM + Indexing)           |
+-----------------------------------+-----------------------------------+
```

#### 1. Migrate Storage from Google Sheets to PostgreSQL / SQLite
* **Schema Design:**
  * `teachers`: `id`, `name`, `email`, `role`
  * `classes`: `id`, `class_name`, `section`
  * `timetable_slots`: `id`, `day`, `period`, `class_id`, `subject_id`, `teacher_id`
  * `teaching_plans`: `id`, `slot_id`, `week_start_date`, `topic`, `submitted_by`, `updated_at` (Indexed on `(slot_id, week_start_date)`)
* **Benefits:** Sub-millisecond query latency, zero rate-limit errors, full ACID transactional safety, unlimited concurrent users.
* **Export Option:** Retain an automated background task to sync data to Google Sheets or Excel for stakeholders who prefer spreadsheet formats.

#### 2. Advanced Analytics & Administrative Features
* **Submission Progress Dashboard:** Real-time completion rates (% of periods planned per class/subject/teacher).
* **Automated Reminders:** Automated email/WhatsApp notifications sent to teachers with pending plans on Friday afternoon.
* **Curriculum Tracking:** Historical coverage analytics comparing planned topics against term syllabi.

---

## 5. Recommended Refactored Repository Structure

```
Time_Table_Weekly_planner/
├── app.py                          # Streamlit application launcher
├── requirements.txt                # Dependencies
├── pytest.ini                      # Test configuration
├── config.py                       # Global settings & constants
├── src/
│   ├── __init__.py
│   ├── database/
│   │   ├── __init__.py
│   │   ├── connection.py           # Sheets / DB client handling
│   │   └── repository.py           # Data access & upsert operations
│   ├── pdf/
│   │   ├── __init__.py
│   │   └── generator.py            # PDF building & text shaping engine
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── dates.py                # Monday calculation & timezone helpers
│   │   └── text.py                 # Language & font detection logic
│   └── views/
│       ├── __init__.py
│       ├── timetable_view.py       # Tab 1 UI
│       ├── data_entry_view.py      # Tab 2 UI
│       └── weekly_plan_view.py     # Tab 3 UI
├── tests/
│   ├── test_dates.py
│   ├── test_text.py
│   └── test_repository.py
├── fonts/
│   ├── Jameel_Noori_Nastaleeq_Regular.ttf
│   └── MB-Lateefi-SKv2_0.ttf
└── docs/
    ├── PROJECT_SUMMARY.md
    └── improvements_recommended_by_antigravity.md
```

---

## 6. Implementation Summary Matrix

| Recommendation | Priority | Complexity | Main Benefit |
| :--- | :--- | :--- | :--- |
| **Code Base Modularization** | High | Low | Code maintainability, developer productivity |
| **PDF Multi-line Text Wrapping** | High | Low | Prevents topic text truncation in exported reports |
| **Timezone & Date Lock Fix** | High | Low | Prevents early lockout of teachers on Monday morning |
| **Short-term Data Caching** | High | Medium | Eliminates Google Sheets API quota limits |
| **User Authentication (RBAC)** | Critical | Medium | Prevents unauthorized plan edits and data tampering |
| **Automated Testing Suite** | Medium | Medium | Ensures stability and prevents regression bugs |
| **Migrate to PostgreSQL / SQLite** | High (Long-term)| High | Enterprise scalability, concurrency, sub-ms speed |

---

*Report compiled by Antigravity AI for Pakistan Steel Cadet College (PSCC) Weekly Teaching Plan project.*
