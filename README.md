# Pakistan Steel Cadet College (PSCC) — Weekly Teaching Plan & Timetable System

A modern, mobile-first, bilingual academic planning and scheduling web application for **Pakistan Steel Cadet College**.

The system links the college's 560 master timetable slots across 14 class-sections (Classes 8–12) to dynamic weekly teacher lesson submissions, administrative oversight dashboards, and publication-grade bilingual PDF reports (English, Urdu, and Sindhi).

---

## 🌟 Key Features

* **⚡ Ultra-Lightweight Frontend (React + Vite):**
  * Tiny bundle footprint (~71 KB gzipped) optimized for fast loading on 3G/4G mobile networks.
  * Mobile-first ergonomic layout with collapsible Day Accordions (Monday to Saturday) and auto-expansion for the current day.
  * Bottom Sticky Action Bar with live progress tracking and zero content occlusion.

* **🔤 True Bilingual Typography (Separate Urdu & Sindhi Engines):**
  * **Sindhi:** Authentic **MB Lateefi** Naskh typography (`public/fonts/MB-Lateefi-SKv2_0.ttf`) for proper native Sindhi rendering.
  * **Urdu:** **Jameel Noori Nastaleeq** (`public/fonts/Jameel_Noori_Nastaleeq_Regular.ttf`) for Nastaliq calligraphy.
  * Script-aware RTL textareas with PDF-safe character limit indicators and native localized placeholders.

* **📅 Master Timetable Browser:**
  * View schedules by **Class & Section** or by **Teacher**.
  * Strict chronological ordering (Monday → Saturday, Periods 1 → 7) with day grouping banners and "Today" highlighting.
  * Live client-side instant search across subjects, teachers, and days.

* **📝 Teacher Data Entry:**
  * Teachers enter weekly lesson plans against their own scheduled periods across all classes.
  * **Offline Draft Resilience:** Auto-saves uncommitted drafts to `localStorage` so inputs are never lost due to connection drops.
  * **"Copy Previous Week"** time-saving shortcut for recurring syllabi.
  * Automatic edit-lock after the week starts (Monday midnight).

* **📊 Admin Weekly Matrix:**
  * Real-time audit of submitted vs. missing period plans with single-click "Show missing periods only" filtering.

* **📄 Publication-Quality Bilingual PDF Generator:**
  * Powered by `fpdf2` and `uharfbuzz` for HarfBuzz vector text-shaping (proper Nastaliq and Sindhi letter joining).
  * In-app instant PDF preview modal before downloading.

---

## 🏗️ Architecture & Project Structure

```
Time_Table_Weekly_planner/
├── api/                         # Python Serverless Backend (FastAPI)
│   ├── config.py                # App configuration & font path resolvers
│   ├── index.py                 # FastAPI endpoints & PDF routes
│   ├── pdf_service.py           # Bilingual PDF generation & HarfBuzz shaping engine
│   ├── sheets_service.py        # Google Sheets client & TTL memory cache
│   └── fonts/                   # Serverless lambda font bundle
├── src/                         # Modern React SPA Frontend
│   ├── components/              # UI Components
│   │   ├── DataEntryView.jsx    # Teacher weekly entry view & accordions
│   │   ├── DayAccordion.jsx     # Collapsible day container
│   │   ├── Header.jsx           # College brand header
│   │   ├── PdfModal.jsx         # In-app PDF viewer modal
│   │   ├── PeriodInput.jsx      # Script-aware bilingual input
│   │   ├── StickyActionBar.jsx  # Floating progress & save bar
│   │   ├── TabNavigation.jsx    # Primary tab switcher
│   │   ├── TimetableView.jsx    # Master schedule table & search
│   │   ├── Toast.jsx            # Notification toast feedback
│   │   ├── WeekStepper.jsx      # Week picker & Monday stepper
│   │   └── WeeklyPlanAdminView.jsx # Admin matrix & missing tracker
│   ├── utils/
│   │   ├── dateHelpers.js       # Monday calculation & timezone helpers
│   │   └── scriptDetector.js    # Urdu/Sindhi/Latin character classifier
│   ├── App.jsx                  # Main application orchestrator
│   ├── index.css                # Semantic design tokens & typography
│   └── main.jsx                 # React DOM mount point
├── public/                      # Static assets served at root
│   ├── fonts/                   # Web fonts (MB-Lateefi & Jameel Noori)
│   └── pscc-logo.jpg            # College crest logo
├── fonts/                       # Master TrueType font files
├── docs/                        # Specifications & documentation
│   ├── DEPLOYMENT_GUIDE.md      # Vercel & local deployment guide
│   └── improvements_03_ui_ux_pro_max.md # Comprehensive UI/UX specification
├── .python-version              # Python 3.12 runtime pin for Vercel
├── dev_server.py                # Local development FastAPI runner
├── index.html                   # HTML5 template & font preloads
├── package.json                 # Frontend dependencies (React 18, Vite, Lucide)
├── requirements.txt             # Serverless Python dependencies
├── vercel.json                  # Vercel serverless routing configuration
└── vite.config.js               # Vite build configuration & API proxy
```

---

## 📊 Google Sheets Data Model

The app connects to **one** Google Spreadsheet containing 4 tabs:

1. **`Timetable`** — Master schedule (560 rows):
   ```
   RowID | Day | Period | Class | Section | Class_Section | Subject | Teacher
   ```
2. **`Subjects`** — Reference list feeding subject validation:
   ```
   Subject
   ```
3. **`Teachers`** — Reference list feeding teacher validation:
   ```
   Teacher
   ```
4. **`Teaching_Plan_Entries`** — Stores submitted weekly plans:
   ```
   EntryID | TimetableRowID | WeekStartDate | Topic | SubmittedBy | LastUpdated
   ```

> [!IMPORTANT]
> `EntryID` follows the pattern `<TimetableRowID>_<WeekStartDate>` (e.g. `Monday-1-8-A_2026-08-10`), enabling efficient batch upserts.

---

## 💻 Local Development Setup

### Prerequisites
* **Python 3.10+** installed
* **Node.js 18+** installed

### Step 1: Install Dependencies
```powershell
# 1. Activate Python virtual environment and install backend packages
venv\Scripts\activate
pip install -r requirements.txt

# 2. Install frontend dependencies
npm install
```

### Step 2: Configure Credentials
Create `.streamlit/secrets.toml` with your Google Cloud Service Account JSON credentials:
```toml
[gcp_service_account]
type = "service_account"
project_id = "your-project-id"
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "your-service-account@project.iam.gserviceaccount.com"
client_id = "..."
token_uri = "https://oauth2.googleapis.com/token"
```

### Step 3: Run Development Servers
Open two terminal windows:

* **Terminal 1 (Backend API):**
  ```powershell
  venv\Scripts\activate
  python dev_server.py
  # API server runs on http://127.0.0.1:8000
  ```

* **Terminal 2 (Frontend SPA):**
  ```powershell
  npm run dev
  # React app opens on http://localhost:5173
  ```

---

## ☁️ Deploying to Vercel (100% Free)

This repository is configured for free All-in-One deployment on **Vercel** (React Frontend + Python Serverless API).

### 1. Push to GitHub
```powershell
git add .
git commit -m "Deploy PSCC Weekly Teaching Plan v2.0"
git push origin main
```

### 2. Import into Vercel
1. Log in to **[vercel.com](https://vercel.com)** with your GitHub account.
2. Click **"Add New..."** → **"Project"** and select your repository.
3. Build Settings will be detected automatically (`Vite` preset, output directory `dist`).

### 3. Add Environment Variables
Under **Environment Variables**, add:
* **`SPREADSHEET_ID`**: `1x5wykhZlN2-pFqrreCFvQmDZikZkV8_1fr5igQ-6GCk`
* **`GCP_SERVICE_ACCOUNT`**: Paste the full JSON content of your Google Service Account key.

### 4. Click Deploy
Vercel will build the frontend, package the `/api` serverless backend, and assign a free HTTPS URL (`*.vercel.app`).

---

## 📄 License & Attribution

Designed and developed for **Pakistan Steel Cadet College (PSCC)**.
Supported by **Antigravity AI**.
