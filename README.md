# PSCC Weekly Teaching Plan

A Streamlit app for Pakistan Steel Cadet College (PSCC) that connects the class timetable
to a weekly teaching plan — teachers enter their plan directly against their own periods,
and admins can view any class/section's merged timetable + plan, filterable by week, and
download any view as a PDF.

## Features

- **Timetable View** — browse the master schedule by Class & Section, or by Teacher.
- **Data Entry** — a teacher selects their name and fills in that week's plan against their
  own periods only (across all classes/sections they teach). Supports planning ahead for
  next week. Locks to read-only once a week has started.
- **Weekly Plan View** — admin filters by date, class, and section to see the full week's
  timetable merged with submitted topics.
- **PDF export** on all three tabs, with the college name as a header.
- **Urdu / Sindhi support** — entries in either language are auto-detected and rendered in
  the correct Nastaliq font in the PDF.

## Project files

```
.
├── app.py              # the full app
├── requirements.txt    # Python dependencies
├── fonts/
│   ├── Jameel_Noori_Nastaleeq_Regular.ttf
│   └── MB-Lateefi-SKv2_0.ttf
├── README.md
└── PROJECT_SUMMARY.md  # how this project was designed, from scratch
```

## Google Sheets setup

Create **one** Google Sheets file with these 4 tabs:

**`Timetable`**
| RowID | Day | Period | Class | Section | Class_Section | Subject | Teacher |
|---|---|---|---|---|---|---|---|

**`Subjects`**
| Subject |
|---|

**`Teachers`**
| Teacher |
|---|

**`Teaching_Plan_Entries`** (starts empty — just add the header row)
| EntryID | TimetableRowID | WeekStartDate | Topic | SubmittedBy | LastUpdated |
|---|---|---|---|---|---|

Tab names and column headers must match **exactly** (case-sensitive) — the app looks them
up by name.

## One-time setup: Google service account

This app **writes** data (the Data Entry tab), so it needs more than read-only access.

1. Go to [console.cloud.google.com](https://console.cloud.google.com) → create/select a project.
2. **APIs & Services → Library** → enable **Google Sheets API** and **Google Drive API**.
3. **APIs & Services → Credentials → Create Credentials → Service Account**.
4. Open the service account → **Keys → Add Key → JSON** → download the file.
5. Open that JSON file and copy the `client_email` value.
6. Open your Google Sheet → **Share** → paste that email in → give it **Editor** access.

## Running locally

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

Create `.streamlit/secrets.toml` in the project folder with your service account details:

```toml
[gcp_service_account]
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "...@....iam.gserviceaccount.com"
client_id = "..."
token_uri = "https://oauth2.googleapis.com/token"
```

Fill in `SPREADSHEET_ID` near the top of `app.py` (the long ID in your sheet's URL, between
`/d/` and `/edit`), then run:

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`.

## Deploying to Streamlit Cloud

1. Push this folder to a GitHub repo — **excluding** `venv/` and `.streamlit/secrets.toml`
   (add both to a `.gitignore` file).
2. [share.streamlit.io](https://share.streamlit.io) → New app → point it at the repo.
3. In the app's **Settings → Secrets**, paste the same `[gcp_service_account]` block used
   locally.
4. Deploy.

## Known limitation

Nastaliq is a visually complex script, and rendering it correctly in a PDF library is a
known hard problem. This app uses fpdf2's built-in text-shaping engine (`uharfbuzz`) for
proper Urdu/Sindhi letter-joining — treat the first generated PDF as a test, and report
back if the shaping doesn't look right so it can be tuned further.
