# PSCC Weekly Teaching Plan — Project Summary

A record of how this project was designed, from the original problem to the working app.

## 1. The original problem

PSCC needed a **Class Time Table** in a format a program could actually read — not the
usual notice-board grid — so it could later be used to auto-generate a **weekly teaching
plan** for every subject, class, and section.

School structure:
- Classes 8 to 12
- Classes 8–11: sections A, B, C
- Class 12: sections A, B
- Periods: **7 per day Monday–Thursday, 6 per day Friday–Saturday**

## 2. Designing the Timetable format

Instead of a grid (one tab per class, hard for code to read), we used a **tidy/long
format**: one row per period slot. Columns:

```
RowID | Day | Period | Class | Section | Class_Section | Subject | Teacher
```

`RowID` (e.g. `Monday-1-8-A`) uniquely identifies a slot and became the key used to link
other data to it later. Two supporting reference sheets — `Subjects` and `Teachers` — feed
dropdown validation so entries stay spelled consistently.

The user built this sheet themselves in Google Sheets using the native **Tables** feature,
generating all 560 rows across 14 class-sections.

## 3. First attempt: a Google Form for weekly plans

The initial plan was a Google Form where teachers submitted a week's plan as
`Period_01, Period_02...` columns (one form response per subject/class/section/week). This
required inferring which calendar slot each `Period_0N` referred to, by counting each
subject's occurrences in chronological order through the week.

## 4. Pivot: in-app data entry instead of a Form

This was replaced with a proper **3-tab Streamlit app**, because writing plans directly
against specific timetable slots (rather than a numbered sequence) removes the fragile
"which occurrence is this" guesswork entirely.

**Schema settled on (4 Google Sheets tabs):**
- `Timetable`, `Subjects`, `Teachers` — as above
- `Teaching_Plan_Entries` (new): `EntryID | TimetableRowID | WeekStartDate | Topic | SubmittedBy | LastUpdated`
  - `EntryID` = `TimetableRowID + "_" + WeekStartDate` — doubles as unique key and lookup key,
    making edits an upsert (update in place) rather than a duplicate row.
  - `WeekStartDate` = that week's Monday, calculated automatically from whatever date is picked.

**The 3 tabs:**
1. **Timetable View** — browse the master schedule, either by Class & Section or by Teacher.
2. **Data Entry** — a teacher picks a week (with "This week" / "Next week" shortcuts, since
   plans for the coming week are often submitted Friday/Saturday), then enters that week's
   plan against **their own periods only**, across all classes/sections they teach, shown in
   chronological order. This design replaced an earlier class/section-based layout, which
   was confusing and risked one teacher editing another's entry.
   - **Edit rule**: a submitted week can be edited only *before* that week starts (before its
     Monday); once the week has commenced, entries lock as read-only.
3. **Weekly Plan View** — admin filters by date + class + section to see the timetable merged
   with that week's submitted topics; flags periods with nothing submitted yet.

All 3 tabs can be downloaded as PDF.

## 5. Bilingual support

Some teachers submit plans in Urdu or Sindhi. The app auto-detects the script per entry
(Arabic-script Unicode range, with a specific character set to distinguish Sindhi from
Urdu) and renders it in the matching font in the PDF — Jameel Noori Nastaleeq for Urdu, a
separate uploaded font for Sindhi — using fpdf2's text-shaping engine for correct Nastaliq
letter-joining.

## 6. PDF layout refinements

- Column widths sized to content (Day/Period narrow, Topic wide) instead of split evenly.
- Long tables (e.g. a full week's ~40 rows) print as **two blocks side by side on one page**
  instead of overflowing onto a second page below.
- Header: "Pakistan Steel Cadet College" centered at the top, with the report title
  (e.g. "Weekly Plan - Class 8-A") centered beneath it.

## 7. Current status

Built and being tested locally (Windows, VS Code) before deployment to GitHub + Streamlit
Cloud. Requires a Google service account with Editor access to the spreadsheet, since Tab 2
writes data (unlike an earlier read-only version of this idea).
